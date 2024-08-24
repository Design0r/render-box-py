from __future__ import annotations

from typing import Any, Optional, Protocol, TypedDict


class SerializedCommand(TypedDict):
    name: str
    data: dict[str, Any]


class SerializedTask(TypedDict):
    id: str
    priority: int
    command: SerializedCommand
    job_id: str
    state: str
    timestamp: Optional[float]


class SerializedJob(TypedDict):
    id: str
    name: str
    priority: int
    timestamp: Optional[float]
    state: str
    tasks: list[SerializedTask]


class SerializedWorker(TypedDict):
    id: Optional[int]
    name: str
    state: str
    timestamp: float
    task_id: Optional[str]


class Serializable[T, S](Protocol):
    def serialize(self) -> S: ...
    @classmethod
    def deserialize(cls, data: S) -> Optional[T]: ...
    def as_json(self) -> bytes: ...
    @classmethod
    def from_json(cls, data: bytes) -> Optional[T]: ...


class Command(Serializable["Command", SerializedCommand]):
    def run(self) -> None: ...
