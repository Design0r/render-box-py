from __future__ import annotations

import json
import time
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from render_box.shared.task import Task

from .serialize import (
    Serializable,
    SerializedJob,
)


class JobState(StrEnum):
    Waiting = "waiting"
    Progress = "progress"
    Completed = "completed"


class Job(Serializable["Job", SerializedJob]):
    def __init__(
        self,
        name: str,
        id: Optional[UUID] = None,
        priority: int = 50,
        state: JobState = JobState.Waiting,
        timestamp: Optional[float] = None,
        tasks: Optional[list[Task]] = None,
    ) -> None:
        self.id = id or uuid4()
        self.priority = priority
        self.name = name
        self.state = state
        self.timestamp = timestamp or time.time()
        self.tasks = tasks or []

    def serialize(self) -> SerializedJob:
        task: SerializedJob = {}
        for k, v in self.__dict__.items():
            if k == "tasks":
                v = [t.serialize() for t in v]
            elif isinstance(v, UUID):
                v = str(v)
            task[k] = v

        return task

    @classmethod
    def deserialize(cls, data: Optional[SerializedJob]) -> Optional[Job]:
        if not data:
            return

        return Job(
            id=UUID(data["id"]),
            name=data["name"],
            priority=data["priority"],
            state=JobState(data["state"]),
            timestamp=data["timestamp"],
            tasks=[task for t in data["tasks"] if (task := Task.deserialize(t))],
        )

    @classmethod
    def from_json(cls, data: bytes) -> Optional[Job]:
        return cls.deserialize(json.loads(data.decode("utf-8")))

    def as_json(self) -> bytes:
        return json.dumps(self.serialize()).encode("utf-8")

    def add_task(self, task: Task) -> None:
        task.job_id = self.id
        self.tasks.append(task)

    def __repr__(self) -> str:
        return str(self.__dict__)
