import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")

DEFAULT_ALUNOS = [
    ("43 E1 5C FE", "Bernardo Heckler", "20260001"),
    ("83 6C C1 02", "Gabriel Rico", "20260002"),
    ("33 14 11 FF", "Bento Martins", "20260003"),
]

DEFAULT_LIVROS = [
    ("63 6F 2C FE", "Introducao a Bancos de Dados", "C. J. Date", "disponivel"),
    ("43 82 51 FE", "Docker Pratico", "Jeferson Fernando", "disponivel"),
    ("73 BD BF 02", "Flask Web Development", "Miguel Grinberg", "disponivel"),
    ("63 34 63 FB", "Arquitetura Limpa", "Robert C. Martin", "disponivel"),
]


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alunos (
            id_rfid TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            matricula TEXT NOT NULL UNIQUE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS livros (
            id_rfid TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('disponivel', 'emprestado', 'atrasado')) DEFAULT 'disponivel'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id TEXT NOT NULL,
            livro_id TEXT NOT NULL,
            data_emprestimo TEXT NOT NULL,
            data_devolucao TEXT,
            status TEXT NOT NULL CHECK(status IN ('ativo', 'finalizado', 'atrasado')) DEFAULT 'ativo',
            FOREIGN KEY (aluno_id) REFERENCES alunos(id_rfid),
            FOREIGN KEY (livro_id) REFERENCES livros(id_rfid)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            livro_id TEXT NOT NULL,
            nota INTEGER NOT NULL CHECK(nota >= 1 AND nota <= 5),
            comentario TEXT,
            FOREIGN KEY (livro_id) REFERENCES livros(id_rfid)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            status TEXT NOT NULL,
            source TEXT NOT NULL,
            rfid_id TEXT,
            aluno_id TEXT,
            livro_id TEXT,
            message TEXT NOT NULL,
            metadata_json TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def _seed_default_data(cursor):
    cursor.executemany(
        "INSERT INTO alunos (id_rfid, nome, matricula) VALUES (?, ?, ?)",
        DEFAULT_ALUNOS,
    )
    cursor.executemany(
        "INSERT INTO livros (id_rfid, titulo, autor, status) VALUES (?, ?, ?, ?)",
        DEFAULT_LIVROS,
    )


def ensure_seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    alunos_count = cursor.execute("SELECT COUNT(*) FROM alunos").fetchone()[0]
    livros_count = cursor.execute("SELECT COUNT(*) FROM livros").fetchone()[0]

    if alunos_count == 0:
        cursor.executemany(
            "INSERT INTO alunos (id_rfid, nome, matricula) VALUES (?, ?, ?)",
            DEFAULT_ALUNOS,
        )

    if livros_count == 0:
        cursor.executemany(
            "INSERT INTO livros (id_rfid, titulo, autor, status) VALUES (?, ?, ?, ?)",
            DEFAULT_LIVROS,
        )

    conn.commit()
    conn.close()


def reset_db_with_fake_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS eventos")
    cursor.execute("DROP TABLE IF EXISTS avaliacoes")
    cursor.execute("DROP TABLE IF EXISTS emprestimos")
    cursor.execute("DROP TABLE IF EXISTS livros")
    cursor.execute("DROP TABLE IF EXISTS alunos")
    conn.commit()
    conn.close()

    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()
    _seed_default_data(cursor)
    conn.commit()
    conn.close()

    log_event(
        event_type="system",
        status="success",
        source="backend",
        message="Banco reinicializado com os dados padrao de demonstracao.",
    )


def log_event(event_type, status, source, message, rfid_id=None, aluno_id=None, livro_id=None, metadata=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO eventos (
            created_at, event_type, status, source, rfid_id, aluno_id, livro_id, message, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now_str(),
            event_type,
            status,
            source,
            rfid_id,
            aluno_id,
            livro_id,
            message,
            json.dumps(metadata, ensure_ascii=True) if metadata is not None else None,
        ),
    )
    conn.commit()
    conn.close()


def get_recent_events(limit=15):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            e.id,
            e.created_at,
            e.event_type,
            e.status,
            e.source,
            e.rfid_id,
            e.aluno_id,
            e.livro_id,
            e.message,
            e.metadata_json,
            a.nome AS aluno_nome,
            l.titulo AS livro_titulo
        FROM eventos e
        LEFT JOIN alunos a ON e.aluno_id = a.id_rfid
        LEFT JOIN livros l ON e.livro_id = l.id_rfid
        ORDER BY e.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    events = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item["metadata_json"]) if item["metadata_json"] else None
        item.pop("metadata_json", None)
        events.append(item)
    return events


def get_aluno(id_rfid):
    conn = get_db_connection()
    aluno = conn.execute("SELECT * FROM alunos WHERE id_rfid = ?", (id_rfid,)).fetchone()
    conn.close()
    return aluno


def get_livro(id_rfid):
    conn = get_db_connection()
    livro = conn.execute("SELECT * FROM livros WHERE id_rfid = ?", (id_rfid,)).fetchone()
    conn.close()
    return livro


def classify_rfid(rfid_id):
    aluno = get_aluno(rfid_id)
    if aluno:
        return "ALUNO", aluno

    livro = get_livro(rfid_id)
    if livro:
        return "LIVRO", livro

    return "DESCONHECIDO", None


def get_active_loan_for_book(livro_id):
    conn = get_db_connection()
    loan = conn.execute(
        "SELECT * FROM emprestimos WHERE livro_id = ? AND status IN ('ativo', 'atrasado') ORDER BY id DESC LIMIT 1",
        (livro_id,),
    ).fetchone()
    conn.close()
    return loan


def create_loan(aluno_id, livro_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO emprestimos (aluno_id, livro_id, data_emprestimo, status) VALUES (?, ?, ?, 'ativo')",
        (aluno_id, livro_id, now_str()),
    )
    cursor.execute(
        "UPDATE livros SET status = 'emprestado' WHERE id_rfid = ?",
        (livro_id,),
    )
    conn.commit()
    conn.close()


def return_loan(loan_id, book_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE emprestimos SET status = 'finalizado', data_devolucao = ? WHERE id = ?",
        (now_str(), loan_id),
    )
    cursor.execute(
        "UPDATE livros SET status = 'disponivel' WHERE id_rfid = ?",
        (book_id,),
    )
    conn.commit()
    conn.close()


def get_overdue_loans(seconds_limit):
    conn = get_db_connection()
    loans = conn.execute("SELECT * FROM emprestimos WHERE status = 'ativo'").fetchall()
    conn.close()

    overdue = []
    now = datetime.now()
    for loan in loans:
        data_emp = datetime.strptime(loan["data_emprestimo"], "%Y-%m-%d %H:%M:%S")
        diff_seconds = (now - data_emp).total_seconds()
        if diff_seconds > seconds_limit:
            overdue.append(dict(loan))
    return overdue


def mark_loan_overdue(loan_id, book_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE emprestimos SET status = 'atrasado' WHERE id = ?", (loan_id,))
    cursor.execute("UPDATE livros SET status = 'atrasado' WHERE id_rfid = ?", (book_id,))
    conn.commit()
    conn.close()


def add_review(livro_id, nota, comentario):
    conn = get_db_connection()
    cursor = conn.cursor()
    livro = cursor.execute("SELECT 1 FROM livros WHERE id_rfid = ?", (livro_id,)).fetchone()
    if not livro:
        conn.close()
        raise ValueError("Livro nao cadastrado.")

    cursor.execute(
        "INSERT INTO avaliacoes (livro_id, nota, comentario) VALUES (?, ?, ?)",
        (livro_id, int(nota), comentario),
    )
    conn.commit()
    conn.close()


def get_mock_catalog():
    conn = get_db_connection()
    alunos = conn.execute(
        "SELECT id_rfid, nome, matricula FROM alunos ORDER BY nome ASC"
    ).fetchall()
    livros = conn.execute(
        """
        SELECT
            l.id_rfid,
            l.titulo,
            l.autor,
            l.status,
            COALESCE(a.nome, '') AS aluno_atual
        FROM livros l
        LEFT JOIN emprestimos e
            ON e.livro_id = l.id_rfid
            AND e.status IN ('ativo', 'atrasado')
        LEFT JOIN alunos a ON e.aluno_id = a.id_rfid
        ORDER BY l.titulo ASC
        """
    ).fetchall()
    conn.close()

    return {
        "alunos": [dict(row) for row in alunos],
        "livros": [dict(row) for row in livros],
    }


def get_collection_overview():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            l.id_rfid,
            l.titulo,
            l.autor,
            l.status,
            COALESCE(a.nome, NULL) AS aluno_nome,
            COALESCE(e.data_emprestimo, NULL) AS data_emprestimo,
            COALESCE(e.status, NULL) AS emprestimo_status
        FROM livros l
        LEFT JOIN emprestimos e
            ON e.livro_id = l.id_rfid
            AND e.status IN ('ativo', 'atrasado')
        LEFT JOIN alunos a ON e.aluno_id = a.id_rfid
        ORDER BY
            CASE l.status
                WHEN 'atrasado' THEN 0
                WHEN 'emprestado' THEN 1
                ELSE 2
            END,
            l.titulo ASC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_overdue_details(seconds_limit):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            e.id,
            e.aluno_id,
            e.livro_id,
            e.data_emprestimo,
            a.nome AS aluno_nome,
            a.matricula AS aluno_matricula,
            l.titulo AS livro_titulo,
            l.autor AS livro_autor
        FROM emprestimos e
        JOIN alunos a ON e.aluno_id = a.id_rfid
        JOIN livros l ON e.livro_id = l.id_rfid
        WHERE e.status = 'atrasado'
        ORDER BY e.id DESC
        """
    ).fetchall()
    conn.close()

    details = []
    now = datetime.now()
    for row in rows:
        item = dict(row)
        data_emp = datetime.strptime(item["data_emprestimo"], "%Y-%m-%d %H:%M:%S")
        item["seconds_overdue"] = max(int((now - data_emp).total_seconds()) - seconds_limit, 0)
        details.append(item)
    return details


def get_dashboard_data(seconds_limit):
    conn = get_db_connection()

    counts = conn.execute(
        """
        SELECT
            SUM(CASE WHEN status = 'disponivel' THEN 1 ELSE 0 END) as disponiveis,
            SUM(CASE WHEN status = 'emprestado' THEN 1 ELSE 0 END) as emprestados,
            SUM(CASE WHEN status = 'atrasado' THEN 1 ELSE 0 END) as atrasados,
            COUNT(*) as total
        FROM livros
        """
    ).fetchone()

    counts_dict = {
        "disponiveis": counts["disponiveis"] or 0,
        "emprestados": counts["emprestados"] or 0,
        "atrasados": counts["atrasados"] or 0,
        "total": counts["total"] or 0,
    }

    recent_loans = conn.execute(
        """
        SELECT
            e.id,
            e.livro_id,
            e.data_emprestimo,
            e.data_devolucao,
            e.status,
            a.nome as aluno_nome,
            a.matricula as aluno_matricula,
            l.titulo as livro_titulo,
            l.autor as livro_autor
        FROM emprestimos e
        JOIN alunos a ON e.aluno_id = a.id_rfid
        JOIN livros l ON e.livro_id = l.id_rfid
        ORDER BY e.id DESC
        LIMIT 10
        """
    ).fetchall()
    recent_loans_list = [dict(row) for row in recent_loans]

    recent_reviews = conn.execute(
        """
        SELECT
            av.id,
            av.nota,
            av.comentario,
            l.titulo as livro_titulo,
            l.autor as livro_autor
        FROM avaliacoes av
        JOIN livros l ON av.livro_id = l.id_rfid
        ORDER BY av.id DESC
        LIMIT 10
        """
    ).fetchall()
    recent_reviews_list = [dict(row) for row in recent_reviews]

    top_borrowed = conn.execute(
        """
        SELECT
            l.id_rfid,
            l.titulo,
            l.autor,
            l.status,
            COUNT(e.id) as emprestimos_count
        FROM livros l
        LEFT JOIN emprestimos e ON l.id_rfid = e.livro_id
        GROUP BY l.id_rfid
        ORDER BY emprestimos_count DESC, l.titulo ASC
        """
    ).fetchall()
    top_borrowed_list = [dict(row) for row in top_borrowed]

    top_rated = conn.execute(
        """
        SELECT
            l.id_rfid,
            l.titulo,
            l.autor,
            AVG(av.nota) as nota_media,
            COUNT(av.id) as avaliacoes_count
        FROM livros l
        JOIN avaliacoes av ON l.id_rfid = av.livro_id
        GROUP BY l.id_rfid
        ORDER BY nota_media DESC, avaliacoes_count DESC
        """
    ).fetchall()
    top_rated_list = [dict(row) for row in top_rated]

    conn.close()

    return {
        "counts": counts_dict,
        "historico_recente": recent_loans_list,
        "avaliacoes": recent_reviews_list,
        "ranking_emprestimos": top_borrowed_list,
        "ranking_avaliacoes": top_rated_list,
        "mock_data": get_mock_catalog(),
        "acervo": get_collection_overview(),
        "atrasos": get_overdue_details(seconds_limit),
        "eventos": get_recent_events(),
    }
