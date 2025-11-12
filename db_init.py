"""
Create a local SQLite DB at backend/tasks.db and seed with 3 tasks.
Run: python backend/db_init.py
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'backend', 'tasks.db')

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL;")
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0
    );
    """
)

# Clear existing for a fresh seed (dev convenience)
cur.execute("DELETE FROM tasks;")

seed = [
    ("Learn Flask", 0),
    ("Build a mini project", 0),
    ("Deploy to Vercel", 1),
]
cur.executemany("INSERT INTO tasks (title, done) VALUES (?, ?);", seed)

conn.commit()
conn.close()

print(f"SQLite DB created at {DB_PATH} with 3 tasks.")
