import threading
import time
import serial
import os
import database

class SerialMonitor(threading.Thread):
    def __init__(self, port="COM3", baudrate=9600):
        super().__init__()
        # Use SERIAL_PORT from environment if available, otherwise fallback to COM3
        self.port = os.environ.get("SERIAL_PORT", port)
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

    def run(self):
        print(f"[SerialMonitor] Iniciando monitoramento serial na porta {self.port}...")
        while self.running:
            if not self.connected:
                try:
                    self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
                    self.connected = True
                    print(f"[SerialMonitor] Conectado com sucesso à porta {self.port}.")
                except Exception as e:
                    print(f"[SerialMonitor] Não foi possível abrir a porta {self.port} ({e}). Tentando novamente em 5 segundos...")
                    self.connected = False
                    time.sleep(5)
                    continue
            
            try:
                # Ler linha da porta serial
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"[SerialMonitor] Recebido: '{line}'")
                        self.process_line(line)
            except Exception as e:
                print(f"[SerialMonitor] Conexão serial perdida ou erro na leitura: {e}")
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
            self.connected = False
            self.ser = None

    def stop(self):
        self.running = False
        self.close_serial()

    def write_char(self, char):
        """Método thread-safe para enviar um caractere via serial."""
        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(char.encode('utf-8'))
                    print(f"[SerialMonitor] Resposta serial enviada: '{char}'")
                    return True
                except Exception as e:
                    print(f"[SerialMonitor] Falha ao escrever na serial: {e}")
            return False

    def process_line(self, line):
        # Ignora mensagens de inicialização do Arduino
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
            # Salva o aluno ativo e atualiza o timestamp
            self.active_student_id = rfid_id
            self.active_student_time = time.time()
            print(f"[SerialMonitor] Aluno Ativo: '{aluno['nome']}' ({rfid_id}). Válido por 30s.")
            self.write_char('V')
        else:
            # Aluno inexistente
            self.active_student_id = None
            self.active_student_time = 0.0
            print(f"[SerialMonitor] Aluno com RFID '{rfid_id}' não localizado no banco.")
            self.write_char('R')

    def handle_livro(self, rfid_id):
        print(f"[SerialMonitor] Processando Livro com RFID: '{rfid_id}'")
        livro = database.get_livro(rfid_id)
        
        if not livro:
            print(f"[SerialMonitor] Livro com RFID '{rfid_id}' não cadastrado.")
            self.write_char('R')
            return

        # Verifica se há aluno ativo na sessão dentro do limite de 30 segundos
        now = time.time()
        if not self.active_student_id or (now - self.active_student_time) > 30:
            print("[SerialMonitor] Erro: Nenhum aluno ativo na sessão ou sessão expirou (> 30s).")
            self.active_student_id = None
            self.active_student_time = 0.0
            self.write_char('R')
            return

        # O aluno ativo é válido
        aluno_id = self.active_student_id
        aluno = database.get_aluno(aluno_id)
        aluno_nome = aluno['nome'] if aluno else "Desconhecido"
        
        book_status = livro['status']
        print(f"[SerialMonitor] Livro '{livro['titulo']}' com status '{book_status}'. Aluno Ativo: '{aluno_nome}'")

        if book_status == 'disponivel':
            # Realiza empréstimo
            try:
                database.create_loan(aluno_id, rfid_id)
                print(f"[SerialMonitor] EMPRÉSTIMO realizado com sucesso. Livro: '{livro['titulo']}' para Aluno: '{aluno_nome}'")
                self.write_char('V')
            except Exception as e:
                print(f"[SerialMonitor] Erro ao realizar empréstimo: {e}")
                self.write_char('R')
                
        elif book_status in ('emprestado', 'atrasado'):
            # Realiza devolução
            # Verifica o empréstimo ativo para este livro
            loan = database.get_active_loan_for_book(rfid_id)
            if loan:
                # Só pode devolver se o aluno ativo for quem pegou emprestado
                if loan['aluno_id'] == aluno_id:
                    try:
                        database.return_loan(loan['id'], rfid_id)
                        print(f"[SerialMonitor] DEVOLUÇÃO realizada com sucesso. Livro: '{livro['titulo']}' devolvido por: '{aluno_nome}'")
                        self.write_char('V')
                    except Exception as e:
                        print(f"[SerialMonitor] Erro ao realizar devolução: {e}")
                        self.write_char('R')
                else:
                    # Livro emprestado para outro aluno
                    borrower = database.get_aluno(loan['aluno_id'])
                    borrower_nome = borrower['nome'] if borrower else "Desconhecido"
                    print(f"[SerialMonitor] Erro: Livro '{livro['titulo']}' já está emprestado para outro aluno ('{borrower_nome}').")
                    self.write_char('R')
            else:
                # Caso o livro esteja marcado como emprestado/atrasado mas sem registro ativo (consistência do banco)
                try:
                    # Reset status de qualquer forma para 'disponivel'
                    database.return_loan(-1, rfid_id)
                    print(f"[SerialMonitor] Livro '{livro['titulo']}' estava '{book_status}' mas sem registro ativo. Resetado para disponível.")
                    self.write_char('V')
                except Exception as e:
                    print(f"[SerialMonitor] Erro ao limpar estado: {e}")
                    self.write_char('R')
