import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")

DEFAULT_ALUNOS = [
    ("43 E1 5C FE", "Ana Silva", "20260001"),
    ("83 6C C1 02", "Bruno Santos", "20260002"),
    ("33 14 11 FF", "Carlos Oliveira", "20260003"),
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
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO emprestimos (aluno_id, livro_id, data_emprestimo, status) VALUES (?, ?, ?, 'ativo')",
        (aluno_id, livro_id, now_str),
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
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "UPDATE emprestimos SET status = 'finalizado', data_devolucao = ? WHERE id = ?",
        (now_str, loan_id),
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
        "SELECT id_rfid, titulo, autor, status FROM livros ORDER BY titulo ASC"
    ).fetchall()
    conn.close()

    return {
        "alunos": [dict(row) for row in alunos],
        "livros": [dict(row) for row in livros],
    }


def get_dashboard_data():
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
        ORDER BY emprestimos_count DESC
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
    }
