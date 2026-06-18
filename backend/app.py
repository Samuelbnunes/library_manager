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


def check_overdue_loans_daemon(monitor_instance):
    """Rotina em segundo plano que verifica emprestimos em atraso a cada 2 segundos."""
    print("[OverdueDaemon] Daemon de verificacao de atrasos iniciado.")
    while True:
        try:
            overdue_loans = database.get_overdue_loans(15)
            if overdue_loans:
                for loan in overdue_loans:
                    database.mark_loan_overdue(loan["id"], loan["livro_id"])
                    print(f"[OverdueDaemon] Emprestimo {loan['id']} do livro {loan['livro_id']} marcado como ATRASADO (> 15 segundos).")

                    if monitor_instance and monitor_instance.connected:
                        monitor_instance.write_char("R")
        except Exception as e:
            print(f"[OverdueDaemon] Erro ao processar emprestimos atrasados: {e}")

        time.sleep(2)


@app.route("/", methods=["GET"])
def root():
    return jsonify(
        {
            "name": "Library Manager Backend",
            "status": "ok",
            "serial_connected": serial_monitor.connected if serial_monitor is not None else False,
            "available_routes": [
                "/api/dashboard",
                "/api/avaliar",
                "/api/reset",
                "/api/check_delay",
            ],
        }
    ), 200


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    try:
        data = database.get_dashboard_data()
        data["serial_connected"] = serial_monitor.connected if serial_monitor is not None else False
        data["serial_port"] = serial_monitor.port if serial_monitor is not None else None
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

        database.add_review(livro_id, nota_int, comentario)
        return jsonify({"success": True, "message": "Avaliacao salva com sucesso."}), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_db():
    try:
        database.reset_db_with_fake_data()
        return jsonify({"success": True, "message": "Banco de dados reinicializado e carregado com dados ficticios."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/check_delay", methods=["POST"])
def trigger_delay_check():
    """Rota para disparar manualmente a verificacao de atraso de 15 segundos."""
    try:
        overdue_loans = database.get_overdue_loans(15)
        count = len(overdue_loans)
        for loan in overdue_loans:
            database.mark_loan_overdue(loan["id"], loan["livro_id"])
            if serial_monitor and serial_monitor.connected:
                serial_monitor.write_char("R")
        return jsonify({"success": True, "overdue_count": count, "message": f"{count} emprestimo(s) marcados como atrasado."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


database.init_db()

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    serial_port = os.environ.get("SERIAL_PORT") or None
    serial_monitor = SerialMonitor(port=serial_port, baudrate=9600)
    serial_monitor.start()

    overdue_thread = threading.Thread(target=check_overdue_loans_daemon, args=(serial_monitor,), daemon=True)
    overdue_thread.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
