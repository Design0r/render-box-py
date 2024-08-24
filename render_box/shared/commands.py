from __future__ import annotations

import json
import time
from typing import Any, Optional, Type

from render_box.shared.serialize import Command, SerializedCommand
from render_box.shared.utils import class_name_from_repr


class CommandManager:
    commands: dict[str, Type[Command]] = {}

    @classmethod
    def get_command(cls, name: str) -> Optional[Type[Command]]:
        cmd_type = cls.commands.get(name)
        if not cmd_type:
            print(f'invalid command type: "{name}" not found')
        return cmd_type


def register_command(command: Type[Any]) -> Type[Any]:
    cmd_name = command.__name__
    if cmd_name not in CommandManager.commands:
        CommandManager.commands[cmd_name] = command
        print(f"Registered Command {cmd_name}")

    return command


@register_command
class TestCommand(Command):
    def __init__(self, duration: int) -> None:
        super().__init__()
        self.duration = duration

    def run(self) -> None:
        print(f"starting command {self}")
        time.sleep(self.duration)
        print(f"finished command {self}")

    def serialize(self) -> SerializedCommand:
        return {"name": class_name_from_repr(self.__repr__()), "data": self.__dict__}

    @classmethod
    def deserialize(cls, data: SerializedCommand) -> Optional[TestCommand]:
        try:
            command = TestCommand(**data["data"])
        except Exception:
            print("error deserializing SerializedCommand")
            command = None

        return command

    def as_json(self) -> bytes:
        return json.dumps(self.serialize()).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> Optional[TestCommand]:
        try:
            command = json.loads(data.decode("utf-8"))
        except Exception:
            print("error converting json data to Command")
            command = None

        if not command:
            return

        return cls.deserialize(command)
