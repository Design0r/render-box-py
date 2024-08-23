from __future__ import annotations

import json
from enum import StrEnum
from time import time
from typing import Optional

from render_box.shared.serialize import Serializable, SerializedWorker


class WorkerState(StrEnum):
    Idle = "idle"
    Working = "working"
    Offline = "offline"


class Worker(Serializable["Worker", SerializedWorker]):
    def __init__(
        self,
        id: Optional[int],
        name: str,
        task_id: Optional[str],
        state: WorkerState = WorkerState.Idle,
        timestamp: Optional[float] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.timestamp = timestamp or time()
        self.task_id = task_id
        self.state = state

    def serialize(self) -> SerializedWorker:
        return self.__dict__

    @classmethod
    def deserialize(cls, data: SerializedWorker) -> Optional[Worker]:
        return Worker(
            id=data["id"],
            name=data["name"],
            task_id=data["task_id"],
            state=WorkerState(data["state"]),
            timestamp=data["timestamp"],
        )

    def as_json(self) -> bytes:
        return json.dumps(self.serialize()).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> Optional[Worker]:
        try:
            worker = json.loads(data.decode("utf-8"))
        except Exception:
            print("error converting from json to worker")
            return
        return cls.deserialize(worker)
