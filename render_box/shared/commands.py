from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Type, TypedDict, override


def class_name_from_repr(name: str):
    return name.split("'")[1].split(".")[-1]


class SerializedCommand(TypedDict):
    name: str
    data: dict[str, Any]


class Command(ABC):
    commands: dict[str, Type[Command]] = {}

    def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        super().__init_subclass__(**kwargs)
        if cls not in cls.commands.values():
            name = class_name_from_repr(str(cls))
            cls.commands[name] = cls

    @abstractmethod
    def run(self) -> None: ...

    @abstractmethod
    def serialize(self) -> SerializedCommand: ...

    @classmethod
    def from_json(cls, data: SerializedCommand) -> Command:
        cmd_class = cls.commands[data["name"]]
        cmd = cmd_class(**data["data"])
        return cmd

    def __str__(self) -> str:
        return class_name_from_repr(str(type(self)))

    def __repr__(self) -> str:
        return class_name_from_repr(str(type(self)))


class TestCommand(Command):
    def __init__(self, duration: int) -> None:
        super().__init__()
        self.duration = duration

    @override
    def run(self) -> None:
        print(f"starting command {self}")
        time.sleep(self.duration)
        print(f"finished command {self}")

    @override
    def serialize(self) -> SerializedCommand:
        return SerializedCommand(name=str(self), data=self.__dict__)

    @override
    def __repr__(self) -> str:
        return f"{super().__repr__()}(duration={self.duration})"
