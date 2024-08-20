from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import UUID

import render_box.shared.commands as commands
import render_box.shared.task as task

DB_PATH = Path(__file__).parent / "render_box.db"


class DBConnection:
    def __init__(self) -> None:
        self.connection = self._create_connection()

    def __enter__(self) -> sqlite3.Connection:
        return self.connection

    def __exit__(self, type, value, traceback) -> None:
        self._close_connection(self.connection)

    @staticmethod
    def _create_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)

        conn.executescript("""
            PRAGMA synchronous = NORMAL;
            PRAGMA journal_mode = WAL;
            PRAGMA temp_store = MEMORY;
            PRAGMA cache_size = 10000;
        """)

        return conn

    @staticmethod
    def _close_connection(conn: sqlite3.Connection) -> None:
        conn.execute("PRAGMA optimize;")
        conn.close()


def insert_task(task: task.Task) -> None:
    with DBConnection() as conn:
        try:
            conn.execute(
                "INSERT INTO tasks(id, priority, timestamp, data) VALUES (?, ?, ?, ?);",
                (
                    str(task.id),
                    task.priority,
                    task.timestamp,
                    json.dumps(task.command.serialize()),
                ),
            )
            conn.commit()
        except Exception as e:
            print(e)


def insert_worker(worker: task.WorkerMetadata) -> None:
    with DBConnection() as conn:
        try:
            conn.execute(
                f"INSERT INTO workers{worker.fields()} VALUES (?, ?,?, ?);",
                (worker.name, worker.state, worker.timestamp, worker.task_id),
            )
            conn.commit()
        except Exception as e:
            print(e)


def select_all_tasks() -> list[task.SerializedTask]:
    tasks: list[task.SerializedTask] = []
    with DBConnection() as conn:
        try:
            cursor = conn.execute("SELECT * FROM tasks;")
            for row in cursor.fetchall():
                id, prio, data, state, time = row
                t = task.SerializedTask(
                    id=id,
                    priority=prio,
                    timestamp=time,
                    command=commands.SerializedCommand(json.loads(data)),
                )
                tasks.append(t)

        except Exception as e:
            print(e)

    return tasks


def select_all_worker() -> list[task.WorkerMetadata]:
    worker: list[task.WorkerMetadata] = []
    with DBConnection() as conn:
        try:
            cursor = conn.execute("SELECT * FROM workers;")
            for _, name, _, time, state, task_id in cursor.fetchall():
                w = task.WorkerMetadata(
                    name=name,
                    state=state,
                    timestamp=time,
                    task_id=UUID(task_id) if task_id else None,
                )
                worker.append(w)

        except Exception as e:
            print(e)

    return worker


# def delete(table: Tables, data: DBSchema) -> None:
#     with DBConnection() as conn:
#         try:
#             conn.execute(f"DELETE FROM {table.name} WHERE NAME = '{data.name}';")
#             conn.commit()
#         except Exception as e:
#             print(e)


def init_db():
    path = DB_PATH
    if path.exists():
        print("DB already exists.")
        return

    path.parent.mkdir(exist_ok=True)

    with DBConnection() as conn:
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS tasks
                (id VARCHAR(50) PRIMARY KEY,
                priority INTEGER NOT NULL,
                data TEXT,
                state VARCHAR(10),
                timestamp REAL NOT NULL);
                """
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS workers
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                state VARCHAR(10),
                task_id INTEGER,
                FOREIGN KEY(task_id) REFERENCES tasks(id));
                """
            )
            conn.commit()

            print(f"Created DB {path.stem}")
        except Exception as e:
            print(e)
