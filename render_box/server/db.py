from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

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
        conn.execute(
            "INSERT INTO tasks(id, priority, state, timestamp, data) VALUES (?, ?, ?,?, ?);",
            (
                str(task.id),
                task.priority,
                task.state,
                task.timestamp,
                json.dumps(task.command.serialize()),
            ),
        )
        conn.commit()


def select_next_task() -> Optional[task.SerializedTask]:
    with DBConnection() as conn:
        cursor = conn.execute("""
WITH selected_task AS (
                SELECT id, priority, data, state, timestamp
                FROM tasks
                WHERE priority = (
                    SELECT MAX(priority)
                    FROM tasks
                    WHERE state = 'waiting'
                )
                AND state = 'waiting'
                ORDER BY timestamp ASC
                LIMIT 1
            )
            UPDATE tasks
            SET state = 'progress'
            WHERE id = (SELECT id FROM selected_task)
            RETURNING id, priority, data, 'progress', timestamp;            



        """)
        conn.commit()
        result = cursor.fetchone()
        if not result:
            return None

        id, prio, data, state, time = result

    t = task.SerializedTask(
        id=id,
        priority=prio,
        state=state,
        timestamp=time,
        command=commands.SerializedCommand(json.loads(data)),
    )

    return t


def update_task(task: task.Task) -> None:
    with DBConnection() as conn:
        conn.execute(
            """
 UPDATE tasks
    SET 
        priority = ?,
        data = ?,
        state = ?,
        timestamp = ?
    WHERE 
        id = ?;
""",
            (
                task.priority,
                json.dumps(task.command.serialize()),
                task.state,
                task.timestamp,
                str(task.id),
            ),
        )
        conn.commit()


def update_worker(worker: task.WorkerMetadata) -> None:
    with DBConnection() as conn:
        conn.execute(
            """
 UPDATE workers
    SET 
        name = ?,
        state = ?,
        timestamp = ?,
        task_id = ?
    WHERE 
        id = ?;
""",
            (
                worker.name,
                worker.state,
                worker.timestamp,
                worker.task_id,
                worker.id,
            ),
        )
        conn.commit()


def insert_worker(worker: task.WorkerMetadata) -> None:
    with DBConnection() as conn:
        conn.execute(
            "INSERT INTO workers(name, state, timestamp, task_id) VALUES (?, ?, ?, ?);",
            (worker.name, worker.state, worker.timestamp, worker.task_id),
        )
        conn.commit()


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
                    state=state,
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
        cursor = conn.execute("SELECT * FROM workers;")
        for id, name, _, time, state, task_id in cursor.fetchall():
            w = task.WorkerMetadata(
                id,
                name=name,
                state=state,
                timestamp=time,
                task_id=task_id,
            )
            worker.append(w)

    return worker


def init_db():
    path = DB_PATH
    if path.exists():
        print("DB already exists.")
        return

    path.parent.mkdir(exist_ok=True)

    with DBConnection() as conn:
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
