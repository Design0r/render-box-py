from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

import render_box.shared.commands as commands
import render_box.shared.task as task
import render_box.shared.worker as worker
from render_box.server.sql import SQLoader

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
    sql = SQLoader()
    query = sql.load("select_next_task")

    if not query:
        return

    with DBConnection() as conn:
        cursor = conn.execute(query)
        conn.commit()
        result = cursor.fetchone()
        if not result:
            return

    id, prio, data, state, time = result
    return task.SerializedTask(
        id=id,
        priority=prio,
        state=state,
        timestamp=time,
        command=commands.SerializedCommand(json.loads(data)),
    )


def update_task(task: task.Task) -> None:
    sql = SQLoader()
    query = sql.load("update_task")

    if not query:
        return

    with DBConnection() as conn:
        conn.execute(
            query,
            (
                task.priority,
                json.dumps(task.command.serialize()),
                task.state,
                task.timestamp,
                str(task.id),
            ),
        )
        conn.commit()


def update_worker(worker: worker.WorkerMetadata) -> None:
    sql = SQLoader()
    query = sql.load("update_worker")

    if not query:
        return

    with DBConnection() as conn:
        conn.execute(
            query,
            (
                worker.name,
                worker.state,
                worker.timestamp,
                worker.task_id,
                worker.id,
            ),
        )
        conn.commit()


def insert_worker(worker: worker.WorkerMetadata) -> None:
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


def select_all_worker() -> list[worker.WorkerMetadata]:
    worker_list: list[worker.WorkerMetadata] = []
    with DBConnection() as conn:
        cursor = conn.execute("SELECT * FROM workers;")
        for id, name, _, time, state, task_id in cursor.fetchall():
            w = worker.WorkerMetadata(
                id,
                name=name,
                state=state,
                timestamp=time,
                task_id=task_id,
            )
            worker_list.append(w)

    return worker_list


def init_db():
    path = DB_PATH
    if path.exists():
        print("DB already exists.")
        return

    path.parent.mkdir(exist_ok=True)
    sql = SQLoader()
    query = sql.load("create_tables")

    if not query:
        return

    with DBConnection() as conn:
        conn.execute(query)
        conn.commit()

        print(f"Created DB {path.stem}")
