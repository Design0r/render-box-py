from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Iterable
from typing import Deque, NamedTuple, Optional, Self, TypedDict


class SerializedCommand(TypedDict):
    name: str
    data: dict


def _class_name_from_repr(name: str):
    return name.split("'")[1].split(".")[-1]


class Command(ABC):
    commands: dict[str, type(Command)] = {}

    def __new__(cls, *args, **kwargs) -> Self:
        if cls not in cls.commands:
            name = _class_name_from_repr(str(cls))
            cls.commands[name] = cls
        return super().__new__(cls)

    @abstractmethod
    def run(self) -> None: ...

    @abstractmethod
    def serialize(self) -> dict: ...

    @classmethod
    def from_json(cls, data: SerializedCommand) -> Self:
        cmd_class = cls.commands[data["name"]]
        cmd = cmd_class(**data["data"])
        return cmd

    def __str__(self) -> str:
        return _class_name_from_repr(str(type(self)))

    def __repr__(self) -> str:
        return _class_name_from_repr(str(type(self)))


class TestCommand(Command):
    def __init__(self, duration: int) -> None:
        super().__init__()
        self.duration = duration

    def run(self) -> None:
        print(f"starting command {self}")
        time.sleep(self.duration)
        print(f"finished command {self}")

    def serialize(self) -> dict:
        return {"name": str(self), "data": self.__dict__}

    def __repr__(self) -> str:
        return f"{_class_name_from_repr(str(type(self)))}(duration={self.duration})"


def init_commands() -> None:
    TestCommand(5)


class Task(NamedTuple):
    id: int
    command: Command

    def run(self) -> None:
        self.command.run()

    def serialize(self) -> dict:
        s = {"id": self.id, "command": self.command.serialize()}
        return s

    @classmethod
    def from_json(cls, data: dict) -> Task:
        task = Task(id=data["id"], command=Command.from_json(data["command"]))
        return task


class TaskManager:
    tasks: Deque[Task] = deque()

    def __init__(self, task: Task | Iterable[Task] = None) -> None:
        if task:
            self.add_task(task)

    def add_task(self, task: Task | Iterable[Task]) -> None:
        if isinstance(task, Task):
            self.tasks.append(task)
        else:
            self.tasks.extend(task)

    def pop_task(self) -> Optional[Task]:
        try:
            task = self.tasks.popleft()
        except IndexError:
            task = None

        return task

    def create_task(self, command: Command) -> Task:
        task = Task(len(self.tasks) + 1, command)
        print(command)
        self.add_task(task)
        print(f"created task {task}")
        return task
