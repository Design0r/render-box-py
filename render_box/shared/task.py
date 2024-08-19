from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from enum import StrEnum
from typing import Deque, NamedTuple, Optional, TypedDict

from render_box.shared.commands import Command, SerializedCommand


class SerializedTask(TypedDict):
    id: int
    command: SerializedCommand


def class_name_from_repr(name: str):
    return name.split("'")[1].split(".")[-1]


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
    workers: dict[str, WorkerMetadata] = {}

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

    def register_worker(self, data: dict[str, str]) -> None:
        worker_name = data["name"]

        if worker_name in self.workers:
            print(f'worker: "{worker_name}" already registered.')
            return

        self.workers[worker_name] = WorkerMetadata(
            worker_name, WorkerState.Active, None
        )
        print(f'registered worker: "{worker_name}".')


class WorkerState(StrEnum):
    Idle = "idle"
    Active = "active"
    Offline = "offline"


class WorkerMetadata(NamedTuple):
    name: str
    state: WorkerState
    current_task: Optional[Task]
