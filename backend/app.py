import os
import threading
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

import database
from serial_monitor import SerialMonitor

load_dotenv()

app = Flask(__name__)
CORS(app)

serial_monitor = None
LOAN_TIMEOUT_SECONDS = int(os.environ.get("LOAN_TIMEOUT_SECONDS", "15"))
DEFAULT_SERIAL_PORT = os.environ.get("SERIAL_PORT", "MOCK")


def build_dashboard_payload():
    data = database.get_dashboard_data(LOAN_TIMEOUT_SECONDS)
    data["serial_connected"] = serial_monitor.connected if serial_monitor is not None else False
    data["serial_port"] = serial_monitor.port if serial_monitor is not None else None
    data["serial_mode"] = "mock" if serial_monitor and serial_monitor.mock_mode else "hardware"
    data["mock_enabled"] = bool(serial_monitor and serial_monitor.mock_mode)
    data["loan_timeout_seconds"] = LOAN_TIMEOUT_SECONDS
    data["active_student"] = (
        serial_monitor.get_active_student_summary() if serial_monitor is not None else None
    )
    return data


def check_overdue_loans_daemon(monitor_instance):
    print("[OverdueDaemon] Daemon de verificacao de atrasos iniciado.")
    while True:
        try:
            overdue_loans = database.get_overdue_loans(LOAN_TIMEOUT_SECONDS)
            if overdue_loans:
                for loan in overdue_loans:
                    database.mark_loan_overdue(loan["id"], loan["livro_id"])
                    database.log_event(
                        event_type="loan_overdue",
                        status="warning",
                        source="backend",
                        aluno_id=loan["aluno_id"],
                        livro_id=loan["livro_id"],
                        message=(
                            f"Emprestimo {loan['id']} do livro {loan['livro_id']} "
                            f"marcado como atrasado apos {LOAN_TIMEOUT_SECONDS}s."
                        ),
                    )
                    print(
                        f"[OverdueDaemon] Emprestimo {loan['id']} do livro {loan['livro_id']} "
                        f"marcado como ATRASADO (>{LOAN_TIMEOUT_SECONDS}s)."
                    )

                    if monitor_instance and monitor_instance.connected:
                        monitor_instance.write_char("R")
        except Exception as exc:
            database.log_event(
                event_type="daemon_error",
                status="error",
                source="backend",
                message=f"Erro no daemon de atrasos: {exc}",
            )
            print(f"[OverdueDaemon] Erro ao processar emprestimos atrasados: {exc}")

        time.sleep(2)


@app.route("/", methods=["GET"])
def root():
    return jsonify(
        {
            "name": "Library Manager Backend",
            "status": "ok",
            "serial_connected": serial_monitor.connected if serial_monitor is not None else False,
            "serial_port": serial_monitor.port if serial_monitor is not None else None,
            "serial_mode": "mock" if serial_monitor and serial_monitor.mock_mode else "hardware",
            "available_routes": [
                "/api/dashboard",
                "/api/acervo",
                "/api/eventos",
                "/api/avaliar",
                "/api/reset",
                "/api/check_delay",
                "/api/mock/scan",
            ],
        }
    ), 200


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    try:
        return jsonify(build_dashboard_payload()), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/acervo", methods=["GET"])
def get_collection():
    try:
        payload = build_dashboard_payload()
        return jsonify(
            {
                "counts": payload["counts"],
                "acervo": payload["acervo"],
                "atrasos": payload["atrasos"],
            }
        ), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/eventos", methods=["GET"])
def get_events():
    try:
        return jsonify({"eventos": database.get_recent_events(25)}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/avaliar", methods=["POST"])
def add_review():
    try:
        data = request.get_json() or {}
        livro_id = data.get("livro_id")
        nota = data.get("nota")
        comentario = data.get("comentario", "")

        if not livro_id:
            return jsonify({"error": "O campo 'livro_id' e obrigatorio."}), 400

        if nota is None:
            return jsonify({"error": "O campo 'nota' e obrigatorio."}), 400

        try:
            nota_int = int(nota)
            if nota_int < 1 or nota_int > 5:
                raise ValueError()
        except ValueError:
            return jsonify({"error": "A nota deve ser um numero inteiro entre 1 e 5."}), 400

        aluno_id = serial_monitor.active_student_id if serial_monitor is not None else None

        database.add_review(livro_id, nota_int, comentario, aluno_id=aluno_id)
        database.log_event(
            event_type="review_created",
            status="success",
            source="dashboard",
            aluno_id=aluno_id,
            livro_id=livro_id,
            message=f"Avaliacao registrada para o livro {livro_id}.",
            metadata={"nota": nota_int},
        )
        return jsonify({"success": True, "message": "Avaliacao salva com sucesso."}), 201

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/avaliacoes/<int:review_id>", methods=["PATCH"])
def update_review(review_id):
    try:
        data = request.get_json() or {}
        nota = data.get("nota")
        comentario = data.get("comentario", "")
        aluno_id = serial_monitor.active_student_id if serial_monitor is not None else None

        if nota is None:
            return jsonify({"error": "O campo 'nota' e obrigatorio."}), 400

        try:
            nota_int = int(nota)
            if nota_int < 1 or nota_int > 5:
                raise ValueError()
        except ValueError:
            return jsonify({"error": "A nota deve ser um numero inteiro entre 1 e 5."}), 400

        database.update_review(review_id, nota_int, comentario, aluno_id)
        database.log_event(
            event_type="review_updated",
            status="success",
            source="dashboard",
            aluno_id=aluno_id,
            message=f"Avaliacao {review_id} atualizada.",
            metadata={"nota": nota_int},
        )
        return jsonify({"success": True, "message": "Avaliacao atualizada com sucesso."}), 200

    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_db():
    try:
        database.reset_db_with_fake_data()
        if serial_monitor is not None:
            serial_monitor.active_student_id = None
            serial_monitor.active_student_time = 0.0
        return jsonify({"success": True, "message": "Banco reinicializado com dados padrao."}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/check_delay", methods=["POST"])
def trigger_delay_check():
    try:
        overdue_loans = database.get_overdue_loans(LOAN_TIMEOUT_SECONDS)
        count = len(overdue_loans)
        for loan in overdue_loans:
            database.mark_loan_overdue(loan["id"], loan["livro_id"])
            database.log_event(
                event_type="loan_overdue",
                status="warning",
                source="dashboard",
                aluno_id=loan["aluno_id"],
                livro_id=loan["livro_id"],
                message=f"Emprestimo do livro {loan['livro_id']} marcado manualmente como atrasado.",
            )
            if serial_monitor and serial_monitor.connected:
                serial_monitor.write_char("R")
        return jsonify(
            {
                "success": True,
                "overdue_count": count,
                "message": f"{count} emprestimo(s) marcados como atrasado.",
            }
        ), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/mock/scan", methods=["POST"])
def mock_scan():
    if not serial_monitor or not serial_monitor.mock_mode:
        return jsonify({"error": "O modo mock nao esta habilitado."}), 400

    try:
        data = request.get_json() or {}
        type_prefix = (data.get("type") or "RFID").strip().upper()
        rfid_id = (data.get("rfid_id") or "").strip().upper()

        if not rfid_id:
            return jsonify({"error": "O campo 'rfid_id' e obrigatorio."}), 400

        result = serial_monitor.simulate_scan(type_prefix, rfid_id)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


database.init_db()
database.ensure_seed_data()

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    serial_monitor = SerialMonitor(port=DEFAULT_SERIAL_PORT, baudrate=9600)
    serial_monitor.start()

    overdue_thread = threading.Thread(
        target=check_overdue_loans_daemon,
        args=(serial_monitor,),
        daemon=True,
    )
    overdue_thread.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
