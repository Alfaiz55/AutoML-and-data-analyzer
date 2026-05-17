import sqlite3
from datetime import datetime

DB_NAME = "automl.db"

# =========================
# CREATE TABLE
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_name TEXT,
            problem_type TEXT,
            best_model TEXT,
            score REAL,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# SAVE RESULT
# =========================
def save_result(dataset_name, result):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO history (dataset_name, problem_type, best_model, score, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        dataset_name,
        result["problem_type"],
        result["best_model"],
        result["score"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


# =========================
# GET HISTORY
# =========================
def get_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT dataset_name, problem_type, best_model, score, timestamp
        FROM history
        ORDER BY id DESC
    """)

    data = c.fetchall()

    conn.close()
    return data
