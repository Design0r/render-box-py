from dataclasses import dataclass
from typing import Optional

from render_box.shared.job import Job
from render_box.shared.task import Task
from render_box.shared.worker import Worker


@dataclass
class AppState:
    worker: Optional[Worker] = None
    task: Optional[Task] = None
    job: Optional[Job] = None
