from __future__ import annotations

import json
import time
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, NamedTuple, Optional, TypedDict
from uuid import UUID, uuid4

from render_box.server import db

from ..shared.commands import Command, SerializedCommand


class SerializedTask(TypedDict):
    id: str
    priority: int
    state: str
    timestamp: float
    command: SerializedCommand


def class_name_from_repr(name: str):
    return name.split("'")[1].split(".")[-1]


class Task(NamedTuple):
    id: UUID
    priority: int
    state: str
    timestamp: float
    command: Command

    def run(self) -> None:
        self.command.run()

    def serialize(self) -> SerializedTask:
        return SerializedTask(
            id=str(self.id),
            priority=self.priority,
            state=self.state,
            timestamp=self.timestamp,
            command=self.command.serialize(),
        )

    def as_json(self) -> str:
        return json.dumps(self.serialize())

    @classmethod
    def from_json(cls, data: SerializedTask) -> Task:
        task = Task(
            id=UUID(data["id"]),
            priority=data["priority"],
            state=data["state"],
            timestamp=data["timestamp"],
            command=Command.from_json(data["command"]),
        )
        return task

    @classmethod
    def fields(cls) -> str:
        return f"({','.join([f.upper() for f in cls._fields])})"


class TaskManager:
    def __init__(self, task: Optional[Task | Iterable[Task]] = None) -> None:
        if task:
            self.add_task(task)

    def add_task(self, task: Task | Iterable[Task]) -> None:
        if isinstance(task, Task):
            db.insert_task(task)
            return

        for t in task:
            db.insert_task(t)

    def pop_task(self) -> Optional[Task]:
        task = db.select_next_task()
        if task:
            return Task.from_json(task)

        return

    @classmethod
    def create_task(cls, command: Command, priority: int = 50) -> Task:
        task = Task(uuid4(), priority, "waiting", time.time(), command)
        return task

    def register_worker(self, worker: WorkerMetadata) -> None:
        db.insert_worker(worker)

    def get_all_tasks(self) -> list[SerializedTask]:
        return db.select_all_tasks()

    def get_all_worker(self) -> list[WorkerMetadata]:
        return db.select_all_worker()

    def update_task(self, task: Task) -> None:
        db.update_task(task)


class WorkerState(StrEnum):
    Idle = "idle"
    Active = "active"
    Offline = "offline"


class WorkerMetadata(NamedTuple):
    name: str
    state: str
    timestamp: float
    task_id: Optional[UUID]

    @classmethod
    def fields(cls) -> str:
        return f"({','.join([f.upper() for f in cls._fields])})"

    def serialize(self) -> dict[str, Any]:
        return self._asdict()

    def as_json(self) -> str:
        return json.dumps(self.serialize())
