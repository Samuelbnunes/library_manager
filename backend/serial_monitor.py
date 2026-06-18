import os
import threading
import time

import database
import serial


class SerialMonitor(threading.Thread):
    def __init__(self, port="MOCK", baudrate=9600):
        super().__init__()
        self.port = os.environ.get("SERIAL_PORT", port)
        self.baudrate = baudrate
        self.daemon = True
        self.running = True
        self.ser = None
        self.lock = threading.Lock()

        self.active_student_id = None
        self.active_student_time = 0.0
        self.active_student_window_seconds = int(
            os.environ.get("ACTIVE_STUDENT_WINDOW_SECONDS", "30")
        )

        self.connected = False
        self.mock_mode = self.port.strip().upper() == "MOCK"
        self.last_response = None

    def run(self):
        if self.mock_mode:
            self.connected = True
            print("[SerialMonitor] Rodando em modo MOCK. Nenhuma porta serial sera aberta.")
            while self.running:
                time.sleep(0.2)
            return

        print(f"[SerialMonitor] Iniciando monitoramento serial na porta {self.port}...")
        while self.running:
            if not self.connected:
                try:
                    self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
                    self.connected = True
                    print(f"[SerialMonitor] Conectado com sucesso a porta {self.port}.")
                except Exception as exc:
                    print(
                        f"[SerialMonitor] Nao foi possivel abrir a porta {self.port} ({exc}). "
                        "Tentando novamente em 5 segundos..."
                    )
                    self.connected = False
                    time.sleep(5)
                    continue

            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        print(f"[SerialMonitor] Recebido: '{line}'")
                        self.process_line(line)
            except Exception as exc:
                print(f"[SerialMonitor] Conexao serial perdida ou erro na leitura: {exc}")
                self.close_serial()
                time.sleep(2)

            time.sleep(0.1)

    def close_serial(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.connected = False if not self.mock_mode else True
            self.ser = None

    def stop(self):
        self.running = False
        self.close_serial()

    def write_char(self, char):
        self.last_response = char

        if self.mock_mode:
            print(f"[SerialMonitor][MOCK] Resposta simulada enviada: '{char}'")
            return True

        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(char.encode("utf-8"))
                    print(f"[SerialMonitor] Resposta serial enviada: '{char}'")
                    return True
                except Exception as exc:
                    print(f"[SerialMonitor] Falha ao escrever na serial: {exc}")
            return False

    def process_line(self, line):
        if "---" in line or "Aproxime" in line or "Status:" in line or "UID" in line:
            return {"ignored": True}

        if ":" not in line:
            return {"ignored": True}

        type_prefix, rfid_id = line.split(":", 1)
        type_prefix = type_prefix.strip().upper()
        rfid_id = rfid_id.strip().upper()

        if type_prefix == "ALUNO":
            return self.handle_aluno(rfid_id)
        if type_prefix == "LIVRO":
            return self.handle_livro(rfid_id)
        return {"success": False, "response": "R", "message": "Tipo RFID invalido."}

    def simulate_scan(self, type_prefix, rfid_id):
        simulated_line = f"{type_prefix.strip().upper()}:{rfid_id.strip().upper()}"
        print(f"[SerialMonitor][MOCK] Simulando leitura: {simulated_line}")
        return self.process_line(simulated_line)

    def handle_aluno(self, rfid_id):
        print(f"[SerialMonitor] Processando Aluno com RFID: '{rfid_id}'")
        aluno = database.get_aluno(rfid_id)

        if aluno:
            self.active_student_id = rfid_id
            self.active_student_time = time.time()
            self.write_char("V")
            return {
                "success": True,
                "response": "V",
                "type": "ALUNO",
                "rfid_id": rfid_id,
                "message": f"Aluno {aluno['nome']} ativado por {self.active_student_window_seconds}s.",
                "entity": {"nome": aluno["nome"], "matricula": aluno["matricula"]},
            }

        self.active_student_id = None
        self.active_student_time = 0.0
        self.write_char("R")
        return {
            "success": False,
            "response": "R",
            "type": "ALUNO",
            "rfid_id": rfid_id,
            "message": f"Aluno com RFID {rfid_id} nao localizado no banco.",
        }

    def handle_livro(self, rfid_id):
        print(f"[SerialMonitor] Processando Livro com RFID: '{rfid_id}'")
        livro = database.get_livro(rfid_id)

        if not livro:
            self.write_char("R")
            return {
                "success": False,
                "response": "R",
                "type": "LIVRO",
                "rfid_id": rfid_id,
                "message": f"Livro com RFID {rfid_id} nao cadastrado.",
            }

        now = time.time()
        if not self.active_student_id or (now - self.active_student_time) > self.active_student_window_seconds:
            self.active_student_id = None
            self.active_student_time = 0.0
            self.write_char("R")
            return {
                "success": False,
                "response": "R",
                "type": "LIVRO",
                "rfid_id": rfid_id,
                "message": "Nenhum aluno ativo na sessao ou a sessao expirou.",
            }

        aluno_id = self.active_student_id
        aluno = database.get_aluno(aluno_id)
        aluno_nome = aluno["nome"] if aluno else "Desconhecido"
        book_status = livro["status"]

        if book_status == "disponivel":
            try:
                database.create_loan(aluno_id, rfid_id)
                self.write_char("V")
                return {
                    "success": True,
                    "response": "V",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": f"Emprestimo realizado: {aluno_nome} -> {livro['titulo']}.",
                }
            except Exception as exc:
                self.write_char("R")
                return {
                    "success": False,
                    "response": "R",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": f"Erro ao realizar emprestimo: {exc}",
                }

        if book_status in ("emprestado", "atrasado"):
            loan = database.get_active_loan_for_book(rfid_id)
            if loan:
                if loan["aluno_id"] == aluno_id:
                    try:
                        database.return_loan(loan["id"], rfid_id)
                        self.write_char("V")
                        return {
                            "success": True,
                            "response": "V",
                            "type": "LIVRO",
                            "rfid_id": rfid_id,
                            "message": f"Devolucao realizada: {aluno_nome} devolveu {livro['titulo']}.",
                        }
                    except Exception as exc:
                        self.write_char("R")
                        return {
                            "success": False,
                            "response": "R",
                            "type": "LIVRO",
                            "rfid_id": rfid_id,
                            "message": f"Erro ao realizar devolucao: {exc}",
                        }

                borrower = database.get_aluno(loan["aluno_id"])
                borrower_nome = borrower["nome"] if borrower else "Desconhecido"
                self.write_char("R")
                return {
                    "success": False,
                    "response": "R",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": (
                        f"Livro {livro['titulo']} ja esta emprestado para outro aluno "
                        f"({borrower_nome})."
                    ),
                }

            try:
                database.return_loan(-1, rfid_id)
                self.write_char("V")
                return {
                    "success": True,
                    "response": "V",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": (
                        f"Livro {livro['titulo']} estava marcado como {book_status} sem emprestimo "
                        "ativo e foi resetado para disponivel."
                    ),
                }
            except Exception as exc:
                self.write_char("R")
                return {
                    "success": False,
                    "response": "R",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": f"Erro ao limpar estado do livro: {exc}",
                }

        self.write_char("R")
        return {
            "success": False,
            "response": "R",
            "type": "LIVRO",
            "rfid_id": rfid_id,
            "message": f"Status do livro {livro['titulo']} nao suportado: {book_status}.",
        }
