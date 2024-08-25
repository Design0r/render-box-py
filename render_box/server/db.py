from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

import render_box.shared.commands as commands
import render_box.shared.job as job
import render_box.shared.task as task
import render_box.shared.worker as worker
from render_box.server.sql import SQLoader
from render_box.shared.serialize import SerializedJob

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


def insert_job(job: job.Job) -> None:
    with DBConnection() as conn:
        conn.execute(
            "INSERT INTO jobs(id, priority, name ,state, timestamp) VALUES (?, ?, ?, ?, ?);",
            (
                str(job.id),
                job.priority,
                job.name,
                job.state,
                job.timestamp,
            ),
        )
        conn.commit()


def insert_task(task: task.Task) -> None:
    with DBConnection() as conn:
        conn.execute(
            "INSERT INTO tasks(id,job_id, priority, state, timestamp, data) VALUES (?, ?, ?, ?, ?, ?);",
            (
                str(task.id),
                str(task.job_id),
                task.priority,
                task.state,
                task.timestamp,
                json.dumps(task.command.serialize()),
            ),
        )
        conn.commit()


def cleanup_completed_jobs(task_id: str) -> None:
    sql = SQLoader()
    query = sql.load("get_remaining_tasks_from_job")

    if not query:
        return

    with DBConnection() as conn:
        cursor = conn.execute(query, (task_id,))
        conn.commit()
        (result,) = cursor.fetchone()
        if result == 0:
            query = sql.load("complete_job")
            if not query:
                return
            conn.execute(query, (task_id,))
            conn.commit()


def select_job(task_id: str) -> Optional[SerializedJob]:
    sql = SQLoader()
    query = sql.load("select_job")

    if not query:
        return

    with DBConnection() as conn:
        cursor = conn.execute(
            query,
            (task_id,),
        )
        conn.commit()
        result = cursor.fetchone()
        if not result:
            return

    id, name, prio, time, state = result
    return SerializedJob(
        id=id,
        name=name,
        priority=prio,
        state=state,
        timestamp=time,
        tasks=[],
    )


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

    id, job_id, prio, data, state, time = result
    return task.SerializedTask(
        id=id,
        job_id=job_id,
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


def update_worker(worker: worker.Worker) -> None:
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


def update_job(job: job.Job) -> None:
    sql = SQLoader()
    query = sql.load("update_job")

    if not query:
        return

    with DBConnection() as conn:
        conn.execute(
            query,
            (
                job.priority,
                job.name,
                job.state,
                job.timestamp,
                str(job.id),
            ),
        )
        conn.commit()


def insert_worker(worker: worker.Worker) -> None:
    with DBConnection() as conn:
        conn.execute(
            "INSERT INTO workers(name, state, timestamp, task_id) VALUES (?, ?, ?, ?);",
            (worker.name, worker.state, worker.timestamp, worker.task_id),
        )
        conn.commit()


def select_all_tasks(job_id: str) -> list[task.SerializedTask]:
    tasks: list[task.SerializedTask] = []
    with DBConnection() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE job_id = ?", (job_id,))
        for row in cursor.fetchall():
            id, job_id, prio, data, state, time = row
            t = task.SerializedTask(
                id=id,
                job_id=job_id,
                priority=prio,
                state=state,
                timestamp=time,
                command=commands.SerializedCommand(json.loads(data)),
            )
            tasks.append(t)

    return tasks


def select_all_jobs() -> list[SerializedJob]:
    jobs: list[SerializedJob] = []
    with DBConnection() as conn:
        cursor = conn.execute("SELECT * FROM jobs;")
        for row in cursor.fetchall():
            id, name, prio, time, state = row
            t = SerializedJob(
                id=id,
                name=name,
                priority=prio,
                state=state,
                timestamp=time,
                tasks=[],
            )
            jobs.append(t)

    return jobs


def select_all_worker() -> list[worker.Worker]:
    worker_list: list[worker.Worker] = []
    with DBConnection() as conn:
        cursor = conn.execute("SELECT * FROM workers;")
        for id, name, _, time, state, task_id in cursor.fetchall():
            w = worker.Worker(
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
        conn.executescript(query)
        conn.commit()

        print(f"Created DB {path.stem}")
