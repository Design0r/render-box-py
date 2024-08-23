from __future__ import annotations

import json
import time
from collections.abc import Iterable
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from render_box.server import db
from render_box.shared.commands import CommandManager

from .serialize import Command, Serializable, SerializedTask
from .worker import WorkerMetadata


class TaskState(StrEnum):
    Waiting = "waiting"
    Progress = "progress"
    Completed = "completed"


class Task(Serializable["Task", SerializedTask]):
    def __init__(
        self,
        id: UUID,
        priority: int,
        command: Command,
        state: TaskState = TaskState.Waiting,
        timestamp: Optional[float] = None,
    ) -> None:
        self.id = id
        self.priority = priority
        self.command = command
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
    def deserialize(cls, data: SerializedTask) -> Optional[Task]:
        command_type = CommandManager.get_command(data["command"]["name"])

        if not command_type:
            return

        command = command_type.deserialize(data["command"])
        if not command:
            return

        return Task(
            id=UUID(data["id"]),
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
    worker: dict[str, WorkerMetadata] = {}

    def __init__(self, task: Optional[Task | Iterable[Task]] = None) -> None:
        if task:
            self.add_task(task)

        self.worker = {worker.name: worker for worker in self.get_all_worker()}

    def add_task(self, task: Task | Iterable[Task]) -> None:
        if isinstance(task, Task):
            db.insert_task(task)
            return

        for t in task:
            db.insert_task(t)

    def pop_task(self) -> Optional[Task]:
        task = db.select_next_task()
        if task:
            return Task.deserialize(task)

        return

    @classmethod
    def create_task(cls, command: Command, priority: int = 50) -> Task:
        return Task(uuid4(), priority, command)

    def register_worker(self, worker: WorkerMetadata) -> None:
        self.worker[worker.name] = worker
        db.insert_worker(worker)

    def get_all_tasks(self) -> list[SerializedTask]:
        return db.select_all_tasks()

    def get_all_worker(self) -> list[WorkerMetadata]:
        return db.select_all_worker()

    def update_task(self, task: Task) -> None:
        db.update_task(task)

    def update_worker(self, worker: WorkerMetadata) -> None:
        db.update_worker(worker)
