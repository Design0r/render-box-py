from __future__ import annotations

import json
from typing import NamedTuple, Optional

from render_box.shared.task import Command, SerializedCommand, SerializedTask, Task


class Message(NamedTuple):
    message: str
    data: Optional[SerializedTask | SerializedCommand] = None

    def as_json(self, encoding: str = "utf-8") -> bytes:
        return json.dumps(self._asdict()).encode(encoding)

    @classmethod
    def from_command(cls, command: Command) -> Message:
        return Message(message="command", data=command.serialize())

    @classmethod
    def from_task(cls, task: Task) -> Message:
        return Message(message="task", data=task.serialize())
