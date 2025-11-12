"""
Tiny DB helper that auto-detects backend:
1) Postgres when DATABASE_URL is present
2) SQLite file backend/tasks.db if it exists
3) In-memory dict (fallback, good for serverless demo without DB)

Provides functions:
- get_all_tasks()
- get_task(id)
- create_task(title)
- update_task(id, title=None, done=None)
- delete_task(id)

Each returns simple Python dicts like {"id": 1, "title": "...", "done": True} or None when missing.
"""
import os
import sqlite3
from typing import Any, Dict, List, Optional

# Optional: Postgres, only imported if DATABASE_URL provided
PG_AVAILABLE = False
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
try:
    if DATABASE_URL:
        import psycopg2
        PG_AVAILABLE = True
except Exception:
    PG_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'backend', 'tasks.db')

FORCE_BACKEND = os.getenv("FORCE_BACKEND", "").lower()  # 'memory' | 'sqlite' | 'postgres'


class BackendBase:
    def get_all_tasks(self) -> List[Dict[str, Any]]: ...
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]: ...
    def create_task(self, title: str) -> Dict[str, Any]: ...
    def update_task(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[Dict[str, Any]]: ...
    def delete_task(self, task_id: int) -> bool: ...


class MemoryBackend(BackendBase):
    def __init__(self) -> None:
        self._data: Dict[int, Dict[str, Any]] = {}
        self._next_id = 1

    def _to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return [self._to_dict(v) for v in sorted(self._data.values(), key=lambda r: r["id"])]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        row = self._data.get(task_id)
        return self._to_dict(row) if row else None

    def create_task(self, title: str) -> Dict[str, Any]:
        task = {"id": self._next_id, "title": title, "done": False}
        self._data[self._next_id] = task
        self._next_id += 1
        return self._to_dict(task)

    def update_task(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[Dict[str, Any]]:
        row = self._data.get(task_id)
        if not row:
            return None
        if title is not None:
            row["title"] = title
        if done is not None:
            row["done"] = bool(done)
        return self._to_dict(row)

    def delete_task(self, task_id: int) -> bool:
        return self._data.pop(task_id, None) is not None


class SQLiteBackend(BackendBase):
    def __init__(self, path: str) -> None:
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        self.conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, title, done FROM tasks ORDER BY id ASC;")
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, title, done FROM tasks WHERE id = ?;", (task_id,))
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def create_task(self, title: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO tasks (title, done) VALUES (?, 0);", (title,))
        self.conn.commit()
        new_id = cur.lastrowid
        return self.get_task(new_id)  # type: ignore

    def update_task(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[Dict[str, Any]]:
        if title is None and done is None:
            return self.get_task(task_id)
        sets = []
        params: List[Any] = []
        if title is not None:
            sets.append("title = ?")
            params.append(title)
        if done is not None:
            sets.append("done = ?")
            params.append(1 if done else 0)
        params.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?;"
        cur = self.conn.cursor()
        cur.execute(sql, tuple(params))
        self.conn.commit()
        return self.get_task(task_id)

    def delete_task(self, task_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
        self.conn.commit()
        return cur.rowcount > 0


class PostgresBackend(BackendBase):
    def __init__(self, url: str) -> None:
        import psycopg2  # type: ignore
        self.conn = psycopg2.connect(url)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            );
            """
        )
        self.conn.commit()

    def _row_to_dict(self, row: tuple) -> Dict[str, Any]:
        return {"id": row[0], "title": row[1], "done": bool(row[2])}

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, title, done FROM tasks ORDER BY id ASC;")
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def create_task(self, title: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id, title, done;", (title,))
        row = cur.fetchone()
        self.conn.commit()
        return self._row_to_dict(row)  # type: ignore

    def update_task(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[Dict[str, Any]]:
        if title is None and done is None:
            return self.get_task(task_id)
        sets = []
        params: List[Any] = []
        if title is not None:
            sets.append("title = %s")
            params.append(title)
        if done is not None:
            sets.append("done = %s")
            params.append(bool(done))
        params.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(sets)} WHERE id = %s RETURNING id, title, done;"
        cur = self.conn.cursor()
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        self.conn.commit()
        return self._row_to_dict(row) if row else None

    def delete_task(self, task_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
        deleted = cur.rowcount > 0
        self.conn.commit()
        return deleted


# Select backend in priority order
_backend: BackendBase
if FORCE_BACKEND == 'memory':
    _backend = MemoryBackend()
elif FORCE_BACKEND == 'sqlite':
    _backend = SQLiteBackend(SQLITE_PATH)
elif FORCE_BACKEND == 'postgres' and DATABASE_URL and PG_AVAILABLE:
    _backend = PostgresBackend(DATABASE_URL)
else:
    if DATABASE_URL and PG_AVAILABLE:
        _backend = PostgresBackend(DATABASE_URL)
    elif os.path.exists(SQLITE_PATH):
        _backend = SQLiteBackend(SQLITE_PATH)
    else:
        _backend = MemoryBackend()


def get_all_tasks():
    return _backend.get_all_tasks()


def get_task(task_id: int):
    return _backend.get_task(task_id)


def create_task(title: str):
    return _backend.create_task(title)


def update_task(task_id: int, title: Optional[str] = None, done: Optional[bool] = None):
    return _backend.update_task(task_id, title, done)


def delete_task(task_id: int):
    return _backend.delete_task(task_id)
