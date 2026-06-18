import os
import threading
import time

import serial
from serial.tools import list_ports

import database


class SerialMonitor(threading.Thread):
    def __init__(self, port=None, baudrate=9600):
        super().__init__()
        configured_port = os.environ.get("SERIAL_PORT")
        self.port = configured_port or port or self.detect_serial_port()
        self.baudrate = baudrate
        self.daemon = True
        self.running = True
        self.ser = None
        self.lock = threading.Lock()

        # Active student memory
        self.active_student_id = None
        self.active_student_time = 0.0

        # Connection status
        self.connected = False

    def detect_serial_port(self):
        candidates = []

        for port_info in list_ports.comports():
            device = (port_info.device or "").strip()
            description = (port_info.description or "").lower()

            if any(token in device for token in ("/dev/ttyACM", "/dev/ttyUSB", "COM")):
                candidates.append(device)
                continue

            if any(token in description for token in ("arduino", "usb serial", "ch340", "cp210", "ttyacm", "ttyusb")):
                candidates.append(device)

        return candidates[0] if candidates else None

    def run(self):
        print(f"[SerialMonitor] Iniciando monitoramento serial na porta {self.port or 'NENHUMA'}...")
        while self.running:
            if not self.connected:
                if not self.port:
                    self.port = self.detect_serial_port()
                    if not self.port:
                        print("[SerialMonitor] Nenhuma porta serial detectada. Defina SERIAL_PORT no .env ou conecte o Arduino. Nova tentativa em 5 segundos...")
                        time.sleep(5)
                        continue

                try:
                    self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
                    self.connected = True
                    print(f"[SerialMonitor] Conectado com sucesso na porta {self.port}.")
                except Exception as e:
                    print(f"[SerialMonitor] Nao foi possivel abrir a porta {self.port} ({e}). Tentando novamente em 5 segundos...")
                    self.connected = False
                    self.port = self.detect_serial_port()
                    time.sleep(5)
                    continue

            try:
                # Ler linha da porta serial
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        print(f"[SerialMonitor] Recebido: '{line}'")
                        self.process_line(line)
            except Exception as e:
                print(f"[SerialMonitor] Conexao serial perdida ou erro na leitura: {e}")
                self.close_serial()
                self.port = self.detect_serial_port()
                time.sleep(2)

            time.sleep(0.1)

    def close_serial(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.connected = False
            self.ser = None

    def stop(self):
        self.running = False
        self.close_serial()

    def write_char(self, char):
        """Metodo thread-safe para enviar um caractere via serial."""
        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(char.encode("utf-8"))
                    print(f"[SerialMonitor] Resposta serial enviada: '{char}'")
                    return True
                except Exception as e:
                    print(f"[SerialMonitor] Falha ao escrever na serial: {e}")
            return False

    def process_line(self, line):
        # Ignora mensagens de inicializacao do Arduino
        if "---" in line or "Aproxime" in line or "Status:" in line or "UID" in line:
            return

        if ":" not in line:
            return

        parts = line.split(":", 1)
        type_prefix = parts[0].strip().upper()
        rfid_id = parts[1].strip().upper()

        if type_prefix == "ALUNO":
            self.handle_aluno(rfid_id)
        elif type_prefix == "LIVRO":
            self.handle_livro(rfid_id)

    def handle_aluno(self, rfid_id):
        print(f"[SerialMonitor] Processando Aluno com RFID: '{rfid_id}'")
        aluno = database.get_aluno(rfid_id)

        if aluno:
            self.active_student_id = rfid_id
            self.active_student_time = time.time()
            print(f"[SerialMonitor] Aluno ativo: '{aluno['nome']}' ({rfid_id}). Valido por 30s.")
            self.write_char("V")
        else:
            self.active_student_id = None
            self.active_student_time = 0.0
            print(f"[SerialMonitor] Aluno com RFID '{rfid_id}' nao localizado no banco.")
            self.write_char("R")

    def handle_livro(self, rfid_id):
        print(f"[SerialMonitor] Processando Livro com RFID: '{rfid_id}'")
        livro = database.get_livro(rfid_id)

        if not livro:
            print(f"[SerialMonitor] Livro com RFID '{rfid_id}' nao cadastrado.")
            self.write_char("R")
            return

        now = time.time()
        if not self.active_student_id or (now - self.active_student_time) > 30:
            print("[SerialMonitor] Erro: nenhum aluno ativo na sessao ou a sessao expirou (> 30s).")
            self.active_student_id = None
            self.active_student_time = 0.0
            self.write_char("R")
            return

        aluno_id = self.active_student_id
        aluno = database.get_aluno(aluno_id)
        aluno_nome = aluno["nome"] if aluno else "Desconhecido"

        book_status = livro["status"]
        print(f"[SerialMonitor] Livro '{livro['titulo']}' com status '{book_status}'. Aluno ativo: '{aluno_nome}'")

        if book_status == "disponivel":
            try:
                database.create_loan(aluno_id, rfid_id)
                print(f"[SerialMonitor] Emprestimo realizado com sucesso. Livro: '{livro['titulo']}' para aluno: '{aluno_nome}'")
                self.write_char("V")
            except Exception as e:
                print(f"[SerialMonitor] Erro ao realizar emprestimo: {e}")
                self.write_char("R")

        elif book_status in ("emprestado", "atrasado"):
            loan = database.get_active_loan_for_book(rfid_id)
            if loan:
                if loan["aluno_id"] == aluno_id:
                    try:
                        database.return_loan(loan["id"], rfid_id)
                        print(f"[SerialMonitor] Devolucao realizada com sucesso. Livro: '{livro['titulo']}' devolvido por: '{aluno_nome}'")
                        self.write_char("V")
                    except Exception as e:
                        print(f"[SerialMonitor] Erro ao realizar devolucao: {e}")
                        self.write_char("R")
                else:
                    borrower = database.get_aluno(loan["aluno_id"])
                    borrower_nome = borrower["nome"] if borrower else "Desconhecido"
                    print(f"[SerialMonitor] Erro: livro '{livro['titulo']}' ja esta emprestado para outro aluno ('{borrower_nome}').")
                    self.write_char("R")
            else:
                try:
                    database.return_loan(-1, rfid_id)
                    print(f"[SerialMonitor] Livro '{livro['titulo']}' estava '{book_status}' sem registro ativo. Resetado para disponivel.")
                    self.write_char("V")
                except Exception as e:
                    print(f"[SerialMonitor] Erro ao limpar estado: {e}")
                    self.write_char("R")
