import os
import threading
import time

import database
import serial
from serial.tools import list_ports


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
        self.pending_serial_line = None
        self.active_student_window_seconds = int(
            os.environ.get("ACTIVE_STUDENT_WINDOW_SECONDS", "60")
        )

        self.connected = False
        self.mock_mode = self.port.strip().upper() == "MOCK"
        self.last_response = None

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
        if self.mock_mode:
            self.connected = True
            print("[SerialMonitor] Rodando em modo MOCK. Nenhuma porta serial sera aberta.")
            database.log_event(
                event_type="serial_connection",
                status="success",
                source="mock",
                message="Modo MOCK ativado para simulacao local.",
            )
            while self.running:
                time.sleep(0.2)
            return

        print(f"[SerialMonitor] Iniciando monitoramento serial na porta {self.port}...")
        while self.running:
            if not self.connected:
                if not self.port:
                    self.port = self.detect_serial_port()
                    if not self.port:
                        print(
                            "[SerialMonitor] Nenhuma porta serial detectada. "
                            "Defina SERIAL_PORT no .env ou conecte o Arduino. Nova tentativa em 5 segundos..."
                        )
                        time.sleep(5)
                        continue

                try:
                    self.ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
                    self.connected = True
                    database.log_event(
                        event_type="serial_connection",
                        status="success",
                        source="arduino",
                        message=f"Conexao serial estabelecida na porta {self.port}.",
                    )
                    print(f"[SerialMonitor] Conectado com sucesso a porta {self.port}.")
                except Exception as exc:
                    database.log_event(
                        event_type="serial_connection",
                        status="error",
                        source="arduino",
                        message=f"Falha ao abrir a porta {self.port}: {exc}",
                    )
                    print(
                        f"[SerialMonitor] Nao foi possivel abrir a porta {self.port} ({exc}). "
                        "Tentando novamente em 5 segundos..."
                    )
                    self.connected = False
                    self.port = self.detect_serial_port()
                    time.sleep(5)
                    continue

            try:
                if self.ser.in_waiting > 0:
                    raw_line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    line = self.normalize_serial_line(raw_line)
                    if line:
                        print(f"[SerialMonitor] Recebido: '{line}'")
                        self.process_line(line, source="arduino")
            except Exception as exc:
                print(f"[SerialMonitor] Conexao serial perdida ou erro na leitura: {exc}")
                database.log_event(
                    event_type="serial_connection",
                    status="error",
                    source="arduino",
                    message=f"Conexao serial perdida: {exc}",
                )
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
            self.connected = False if not self.mock_mode else True
            self.ser = None

    def stop(self):
        self.running = False
        self.close_serial()

    def normalize_serial_line(self, line):
        if not line:
            return None

        if self.pending_serial_line:
            line = f"{self.pending_serial_line} {line}".strip()
            self.pending_serial_line = None

        if self.is_incomplete_rfid_line(line):
            self.pending_serial_line = line
            print(f"[SerialMonitor] Linha RFID incompleta recebida, aguardando complemento: '{line}'")
            return None

        if self.is_orphan_rfid_fragment(line):
            print(f"[SerialMonitor] Fragmento RFID incompleto ignorado: '{line}'")
            return None

        return line

    def is_incomplete_rfid_line(self, line):
        if ":" not in line:
            return False

        type_prefix, rfid_id = line.split(":", 1)
        if type_prefix.strip().upper() not in {"ALUNO", "LIVRO", "RFID", "TAG", "CARD"}:
            return False

        return 0 < len(rfid_id.strip().split()) < 4

    def is_orphan_rfid_fragment(self, line):
        if ":" in line:
            return False

        tokens = line.strip().split()
        if not tokens or len(tokens) >= 4:
            return False

        return all(
            1 <= len(token) <= 2
            and all(char in "0123456789ABCDEFabcdef" for char in token)
            for token in tokens
        )

    def get_active_student_summary(self):
        if not self.active_student_id:
            return None

        aluno = database.get_aluno(self.active_student_id)
        if not aluno:
            return None

        elapsed = max(time.time() - self.active_student_time, 0)
        remaining = max(int(self.active_student_window_seconds - elapsed), 0)
        is_valid = remaining > 0

        if not is_valid:
            self.active_student_id = None
            self.active_student_time = 0.0
            return None

        return {
            "id_rfid": self.active_student_id,
            "nome": aluno["nome"],
            "matricula": aluno["matricula"],
            "remaining_seconds": remaining,
            "window_seconds": self.active_student_window_seconds,
        }

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

    def classify_input(self, type_prefix, rfid_id):
        detected_type, entity = database.classify_rfid(rfid_id)

        if detected_type == "DESCONHECIDO":
            return "DESCONHECIDO", None, "RFID nao localizado em alunos nem livros."

        if type_prefix in {"", "TAG", "RFID", "CARD"}:
            return detected_type, entity, f"RFID identificado automaticamente como {detected_type}."

        if type_prefix != detected_type:
            return detected_type, entity, (
                f"Prefixo recebido ({type_prefix}) nao bateu com o cadastro. "
                f"O back-end tratou como {detected_type}."
            )

        return detected_type, entity, None

    def process_line(self, line, source="arduino"):
        if "---" in line or "Aproxime" in line or "Status:" in line or "UID" in line:
            return {"ignored": True}

        if ":" in line:
            type_prefix, rfid_id = line.split(":", 1)
            type_prefix = type_prefix.strip().upper()
            rfid_id = rfid_id.strip().upper()
        else:
            type_prefix = "RFID"
            rfid_id = line.strip().upper()

        final_type, entity, note = self.classify_input(type_prefix, rfid_id)

        if final_type == "DESCONHECIDO":
            self.write_char("R")
            database.log_event(
                event_type="rfid_scan",
                status="error",
                source=source,
                rfid_id=rfid_id,
                message=f"RFID {rfid_id} nao encontrado no cadastro.",
                metadata={"raw_prefix": type_prefix},
            )
            return {
                "success": False,
                "response": "R",
                "type": "DESCONHECIDO",
                "rfid_id": rfid_id,
                "message": f"RFID {rfid_id} nao encontrado no cadastro.",
            }

        if note:
            database.log_event(
                event_type="rfid_classification",
                status="info",
                source=source,
                rfid_id=rfid_id,
                aluno_id=rfid_id if final_type == "ALUNO" else None,
                livro_id=rfid_id if final_type == "LIVRO" else None,
                message=note,
                metadata={"raw_prefix": type_prefix, "resolved_type": final_type},
            )

        if final_type == "ALUNO":
            return self.handle_aluno(rfid_id, source=source)
        return self.handle_livro(rfid_id, source=source)

    def simulate_scan(self, type_prefix, rfid_id):
        simulated_line = f"{type_prefix.strip().upper()}:{rfid_id.strip().upper()}"
        print(f"[SerialMonitor][MOCK] Simulando leitura: {simulated_line}")
        return self.process_line(simulated_line, source="mock")

    def handle_aluno(self, rfid_id, source):
        aluno = database.get_aluno(rfid_id)

        if aluno:
            self.active_student_id = rfid_id
            self.active_student_time = time.time()
            self.write_char("V")
            message = (
                f"Aluno {aluno['nome']} identificado com sucesso. "
                f"Sessao ativa por {self.active_student_window_seconds}s."
            )
            database.log_event(
                event_type="student_identified",
                status="success",
                source=source,
                rfid_id=rfid_id,
                aluno_id=rfid_id,
                message=message,
            )
            return {
                "success": True,
                "response": "V",
                "type": "ALUNO",
                "rfid_id": rfid_id,
                "message": message,
                "entity": {"nome": aluno["nome"], "matricula": aluno["matricula"]},
            }

        self.active_student_id = None
        self.active_student_time = 0.0
        self.write_char("R")
        message = f"Aluno com RFID {rfid_id} nao localizado no banco."
        database.log_event(
            event_type="student_identified",
            status="error",
            source=source,
            rfid_id=rfid_id,
            message=message,
        )
        return {
            "success": False,
            "response": "R",
            "type": "ALUNO",
            "rfid_id": rfid_id,
            "message": message,
        }

    def handle_livro(self, rfid_id, source):
        livro = database.get_livro(rfid_id)

        if not livro:
            self.write_char("R")
            message = f"Livro com RFID {rfid_id} nao cadastrado."
            database.log_event(
                event_type="book_scan",
                status="error",
                source=source,
                rfid_id=rfid_id,
                message=message,
            )
            return {
                "success": False,
                "response": "R",
                "type": "LIVRO",
                "rfid_id": rfid_id,
                "message": message,
            }

        active_student = self.get_active_student_summary()
        if not active_student:
            self.write_char("R")
            message = "Nenhum aluno ativo na sessao. Identifique um aluno antes de ler o livro."
            database.log_event(
                event_type="book_scan",
                status="error",
                source=source,
                rfid_id=rfid_id,
                livro_id=rfid_id,
                message=message,
            )
            return {
                "success": False,
                "response": "R",
                "type": "LIVRO",
                "rfid_id": rfid_id,
                "message": message,
            }

        aluno_id = active_student["id_rfid"]
        aluno_nome = active_student["nome"]
        book_status = livro["status"]

        if book_status == "disponivel":
            try:
                database.create_loan(aluno_id, rfid_id)
                self.write_char("V")
                message = f"Emprestimo realizado: {aluno_nome} retirou {livro['titulo']}."
                database.log_event(
                    event_type="loan_created",
                    status="success",
                    source=source,
                    rfid_id=rfid_id,
                    aluno_id=aluno_id,
                    livro_id=rfid_id,
                    message=message,
                )
                return {
                    "success": True,
                    "response": "V",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": message,
                }
            except Exception as exc:
                self.write_char("R")
                message = f"Erro ao realizar emprestimo: {exc}"
                database.log_event(
                    event_type="loan_created",
                    status="error",
                    source=source,
                    rfid_id=rfid_id,
                    aluno_id=aluno_id,
                    livro_id=rfid_id,
                    message=message,
                )
                return {
                    "success": False,
                    "response": "R",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": message,
                }

        if book_status in ("emprestado", "atrasado"):
            loan = database.get_active_loan_for_book(rfid_id)
            if loan:
                if loan["aluno_id"] == aluno_id:
                    try:
                        database.return_loan(loan["id"], rfid_id)
                        self.write_char("V")
                        message = f"Devolucao realizada: {aluno_nome} devolveu {livro['titulo']}."
                        database.log_event(
                            event_type="loan_returned",
                            status="success",
                            source=source,
                            rfid_id=rfid_id,
                            aluno_id=aluno_id,
                            livro_id=rfid_id,
                            message=message,
                        )
                        return {
                            "success": True,
                            "response": "V",
                            "type": "LIVRO",
                            "rfid_id": rfid_id,
                            "message": message,
                        }
                    except Exception as exc:
                        self.write_char("R")
                        message = f"Erro ao realizar devolucao: {exc}"
                        database.log_event(
                            event_type="loan_returned",
                            status="error",
                            source=source,
                            rfid_id=rfid_id,
                            aluno_id=aluno_id,
                            livro_id=rfid_id,
                            message=message,
                        )
                        return {
                            "success": False,
                            "response": "R",
                            "type": "LIVRO",
                            "rfid_id": rfid_id,
                            "message": message,
                        }

                borrower = database.get_aluno(loan["aluno_id"])
                borrower_nome = borrower["nome"] if borrower else "Desconhecido"
                self.write_char("R")
                message = (
                    f"Operacao negada: {livro['titulo']} esta vinculado a outro aluno "
                    f"({borrower_nome})."
                )
                database.log_event(
                    event_type="book_scan",
                    status="error",
                    source=source,
                    rfid_id=rfid_id,
                    aluno_id=aluno_id,
                    livro_id=rfid_id,
                    message=message,
                )
                return {
                    "success": False,
                    "response": "R",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": message,
                }

            try:
                database.return_loan(-1, rfid_id)
                self.write_char("V")
                message = (
                    f"Estado ajustado: {livro['titulo']} estava marcado como {book_status} "
                    "sem emprestimo ativo e voltou para disponivel."
                )
                database.log_event(
                    event_type="book_state_repaired",
                    status="success",
                    source=source,
                    rfid_id=rfid_id,
                    aluno_id=aluno_id,
                    livro_id=rfid_id,
                    message=message,
                )
                return {
                    "success": True,
                    "response": "V",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": message,
                }
            except Exception as exc:
                self.write_char("R")
                message = f"Erro ao limpar estado do livro: {exc}"
                database.log_event(
                    event_type="book_state_repaired",
                    status="error",
                    source=source,
                    rfid_id=rfid_id,
                    aluno_id=aluno_id,
                    livro_id=rfid_id,
                    message=message,
                )
                return {
                    "success": False,
                    "response": "R",
                    "type": "LIVRO",
                    "rfid_id": rfid_id,
                    "message": message,
                }

        self.write_char("R")
        message = f"Status do livro {livro['titulo']} nao suportado: {book_status}."
        database.log_event(
            event_type="book_scan",
            status="error",
            source=source,
            rfid_id=rfid_id,
            aluno_id=aluno_id,
            livro_id=rfid_id,
            message=message,
        )
        return {
            "success": False,
            "response": "R",
            "type": "LIVRO",
            "rfid_id": rfid_id,
            "message": message,
        }
