from __future__ import annotations

import json
import time
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from render_box.shared.commands import CommandManager

from .serialize import (
    Command,
    Serializable,
    SerializedTask,
)


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
