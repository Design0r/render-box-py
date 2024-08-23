from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, NamedTuple, Optional

import render_box.shared.task as task
from render_box.shared.serialize import (
    Command,
)


class MessageType(StrEnum):
    pass


class Message(NamedTuple):
    message: str
    data: Optional[Any] = None

    def as_json(self, encoding: str = "utf-8") -> bytes:
        message = self._asdict()
        return json.dumps(message).encode(encoding)

    @classmethod
    def from_command(cls, command: Command) -> Message:
        return Message(message="command", data=command.serialize())

    @classmethod
    def from_task(cls, task: task.Task) -> Message:
        return Message(message="task", data=task.serialize())
