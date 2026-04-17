import sqlite3
from config import DATABASE_PATH


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            started_at DATETIME,
            completed_at DATETIME,
            result TEXT,
            error TEXT
        );

        CREATE TABLE IF NOT EXISTS task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT DEFAULT 'info',
            message TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );
    """)
    conn.commit()
    conn.close()


def get_tasks(status=None):
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, created_at ASC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_task(task_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_task(title, description, priority=1):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO tasks (title, description, priority) VALUES (?, ?, ?)",
        (title, description, priority)
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


def update_task_status(task_id, status):
    conn = get_conn()
    if status == 'running':
        conn.execute(
            "UPDATE tasks SET status = ?, started_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, task_id)
        )
    else:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()


def complete_task(task_id, result):
    conn = get_conn()
    conn.execute(
        "UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP, result = ? WHERE id = ?",
        (result, task_id)
    )
    conn.commit()
    conn.close()


def fail_task(task_id, error):
    conn = get_conn()
    conn.execute(
        "UPDATE tasks SET status = 'failed', completed_at = CURRENT_TIMESTAMP, error = ? WHERE id = ?",
        (error, task_id)
    )
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_conn()
    conn.execute("DELETE FROM task_logs WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def add_log(task_id, level, message):
    conn = get_conn()
    conn.execute(
        "INSERT INTO task_logs (task_id, level, message) VALUES (?, ?, ?)",
        (task_id, level, message)
    )
    conn.commit()
    conn.close()


def get_logs(task_id, since_id=0):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM task_logs WHERE task_id = ? AND id > ? ORDER BY id ASC",
        (task_id, since_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
