from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Iterable
from typing import Any, Deque, NamedTuple, Optional, Type, TypedDict, override


class SerializedCommand(TypedDict):
    name: str
    data: dict[str, Any]


class SerializedTask(TypedDict):
    id: int
    command: SerializedCommand


def _class_name_from_repr(name: str):
    return name.split("'")[1].split(".")[-1]


class Command(ABC):
    commands: dict[str, Type[Command]] = {}

    def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        super().__init_subclass__(**kwargs)
        if cls not in cls.commands.values():
            name = _class_name_from_repr(str(cls))
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
        return _class_name_from_repr(str(type(self)))

    def __repr__(self) -> str:
        return _class_name_from_repr(str(type(self)))


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


class Task(NamedTuple):
    id: int
    command: Command

    def run(self) -> None:
        self.command.run()

    def serialize(self) -> SerializedTask:
        return SerializedTask(id=self.id, command=self.command.serialize())

    @classmethod
    def from_json(cls, data: SerializedTask) -> Task:
        task = Task(id=data["id"], command=Command.from_json(data["command"]))
        return task


class TaskManager:
    tasks: Deque[Task] = deque()

    def __init__(self, task: Optional[Task | Iterable[Task]] = None) -> None:
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
        self.add_task(task)
        print(f"created task {task}")
        return task
