from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Optional


@dataclass
class WorkerMetadata:
    id: Optional[int]
    name: str
    state: WorkerState
    timestamp: float
    task_id: Optional[str]

    def serialize(self) -> dict[str, Any]:
        return asdict(self)

    def as_json(self) -> str:
        return json.dumps(self.serialize())


class WorkerState(StrEnum):
    Idle = "idle"
    Working = "working"
    Offline = "offline"
