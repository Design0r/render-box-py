from __future__ import annotations

import json
import time
from collections.abc import Iterable
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

import render_box.shared.job as job
from render_box.server import db
from render_box.shared.commands import CommandManager

from .serialize import (
    Command,
    Serializable,
    SerializedJob,
    SerializedTask,
    SerializedWorker,
)
from .worker import Worker


class TaskState(StrEnum):
    Waiting = "waiting"
    Progress = "progress"
    Completed = "completed"


class Task(Serializable["Task", SerializedTask]):
    def __init__(
        self,
        command: Command,
        id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
        priority: Optional[int] = None,
        state: TaskState = TaskState.Waiting,
        timestamp: Optional[float] = None,
    ) -> None:
        self.command = command
        self.id = id or uuid4()
        self.job_id = job_id
        self.priority = priority or 50
        self.state = state
        self.timestamp = timestamp or time.time()

    def run(self) -> None:
        self.command.run()

    def serialize(self) -> SerializedTask:
        task: SerializedTask = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Command):
                v = v.serialize()
            elif isinstance(v, UUID):
                v = str(v)
            task[k] = v

        return task

    @classmethod
    def deserialize(cls, data: Optional[SerializedTask]) -> Optional[Task]:
        if not data:
            return

        command_type = CommandManager.get_command(data["command"]["name"])

        if not command_type:
            return

        command = command_type.deserialize(data["command"])
        if not command:
            return

        return Task(
            id=UUID(data["id"]),
            job_id=UUID(data["job_id"]),
            priority=data["priority"],
            command=command,
            state=TaskState(data["state"]),
            timestamp=data["timestamp"],
        )

    @classmethod
    def from_json(cls, data: bytes) -> Optional[Task]:
        return cls.deserialize(json.loads(data.decode("utf-8")))

    def as_json(self) -> bytes:
        return json.dumps(self.serialize()).encode("utf-8")


class TaskManager:
    worker: dict[str, Worker] = {}

    def __init__(self, task: Optional[Task | Iterable[Task]] = None) -> None:
        if task:
            self.add_task(task)

        self.worker = {worker.name: worker for worker in self.get_all_worker()}

    def add_job(self, job: job.Job) -> None:
        db.insert_job(job)

        for task in job.tasks:
            db.insert_task(task)

    def add_task(self, task: Task | Iterable[Task]) -> None:
        if isinstance(task, Task):
            db.insert_task(task)
            return

        for t in task:
            db.insert_task(t)

    def pop_task(self) -> Optional[tuple[Task, job.Job]]:
        ser_task = db.select_next_task()
        if not ser_task:
            return
        ser_job = db.select_job(ser_task["id"])
        if not ser_job:
            return

        task, j = Task.deserialize(ser_task), job.Job.deserialize(ser_job)
        if not task or not j:
            return

        return (task, j)

    def register_worker(self, worker: Worker) -> None:
        self.worker[worker.name] = worker
        db.insert_worker(worker)

    def get_all_tasks(self, job_id: str) -> list[SerializedTask]:
        return db.select_all_tasks(job_id)

    def get_all_jobs(self) -> list[SerializedJob]:
        return db.select_all_jobs()

    def get_all_worker(self) -> list[Worker]:
        return db.select_all_worker()

    def get_all_worker_dict(self) -> list[SerializedWorker]:
        return [w.serialize() for w in db.select_all_worker()]

    def update_task(self, task: Task) -> None:
        db.update_task(task)

    def update_worker(self, worker: Worker) -> None:
        db.update_worker(worker)

    def update_job(self, job: job.Job) -> None:
        db.update_job(job)

    def cleanup_jobs(self, task: Task) -> None:
        db.cleanup_completed_jobs(str(task.id))
