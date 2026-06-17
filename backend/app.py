import os
import time
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

import database
from serial_monitor import SerialMonitor

# Carregar variáveis de ambiente do arquivo .env se existir
load_dotenv()

app = Flask(__name__)
# Habilitar CORS para facilitar a comunicação com o front-end
CORS(app)

# Objeto global para monitorar a serial
serial_monitor = None

def check_overdue_loans_daemon(monitor_instance):
    """Rotina em segundo plano que verifica empréstimos em atraso a cada 2 segundos."""
    print("[OverdueDaemon] Daemon de verificação de atrasos iniciado.")
    while True:
        try:
            # Busca empréstimos ativos há mais de 15 segundos
            overdue_loans = database.get_overdue_loans(15)
            if overdue_loans:
                for loan in overdue_loans:
                    database.mark_loan_overdue(loan['id'], loan['livro_id'])
                    print(f"[OverdueDaemon] Empréstimo {loan['id']} do livro {loan['livro_id']} marcado como ATRASADO (> 15 segundos).")
                    
                    # Se o monitor serial estiver conectado, envia 'R' para o Arduino
                    if monitor_instance and monitor_instance.connected:
                        monitor_instance.write_char('R')
        except Exception as e:
            print(f"[OverdueDaemon] Erro ao processar empréstimos atrasados: {e}")
        
        time.sleep(2)

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        data = database.get_dashboard_data()
        # Injetar o status da conexão serial se ela estiver ativa
        data["serial_connected"] = serial_monitor.connected if serial_monitor is not None else False
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/avaliar', methods=['POST'])
def add_review():
    try:
        data = request.get_json() or {}
        livro_id = data.get('livro_id')
        nota = data.get('nota')
        comentario = data.get('comentario', '')
        
        if not livro_id:
            return jsonify({"error": "O campo 'livro_id' é obrigatório."}), 400
        
        if nota is None:
            return jsonify({"error": "O campo 'nota' é obrigatório."}), 400
            
        try:
            nota_int = int(nota)
            if nota_int < 1 or nota_int > 5:
                raise ValueError()
        except ValueError:
            return jsonify({"error": "A nota deve ser um número inteiro entre 1 e 5."}), 400
            
        database.add_review(livro_id, nota_int, comentario)
        return jsonify({"success": True, "message": "Avaliação salva com sucesso!"}), 201
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_db():
    try:
        database.reset_db_with_fake_data()
        return jsonify({"success": True, "message": "Banco de dados reinicializado e carregado com dados fictícios."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/check_delay', methods=['POST'])
def trigger_delay_check():
    """Rota para disparar manualmente a verificação de atraso de 15 segundos."""
    try:
        overdue_loans = database.get_overdue_loans(15)
        count = len(overdue_loans)
        for loan in overdue_loans:
            database.mark_loan_overdue(loan['id'], loan['livro_id'])
            if serial_monitor and serial_monitor.connected:
                serial_monitor.write_char('R')
        return jsonify({"success": True, "overdue_count": count, "message": f"{count} empréstimo(s) marcados como atrasado."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Inicialização do banco e das threads de segundo plano
database.init_db()

# Garante que as threads só iniciem no processo principal do Flask,
# evitando que rodem duas vezes quando o debug/reloader está ativo.
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    # Cria e inicia a thread do Monitor Serial
    serial_port = os.environ.get("SERIAL_PORT", "COM3")
    serial_monitor = SerialMonitor(port=serial_port, baudrate=9600)
    serial_monitor.start()
    
    # Cria e inicia a thread Daemon para verificação de atrasos de empréstimos
    overdue_thread = threading.Thread(target=check_overdue_loans_daemon, args=(serial_monitor,), daemon=True)
    overdue_thread.start()

if __name__ == '__main__':
    # Porta padrão do Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
