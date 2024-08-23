from __future__ import annotations

import json
from typing import NamedTuple, Optional

import render_box.shared.task as task
from render_box.shared.serialize import Serializable


class Message(NamedTuple):
    message: str
    data: Optional[Serializable] = None

    def as_json(self, encoding: str = "utf-8") -> bytes:
        return json.dumps(self._asdict()).encode(encoding)

    @classmethod
    def from_command(cls, command: task.Command) -> Message:
        return Message(message="command", data=command.serialize())

    @classmethod
    def from_task(cls, task: task.Task) -> Message:
        return Message(message="task", data=task.serialize())
