import json
from typing import NamedTuple, Optional

from render_box.shared.task import SerializedCommand, SerializedTask


class Message(NamedTuple):
    message: str
    data: Optional[SerializedTask | SerializedCommand]

    def as_json(self, encoding: str = "utf-8") -> bytes:
        return json.dumps(self._asdict()).encode(encoding)
