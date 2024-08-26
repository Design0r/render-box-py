from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

import render_box.shared.job as job
from render_box.server import db
from render_box.shared.serialize import (
    SerializedJob,
    SerializedTask,
    SerializedWorker,
)
from render_box.shared.task import Task
from render_box.shared.worker import Worker


class JobManager:
    worker: dict[str, Worker] = {}

    def __init__(self, task: Optional[Task | Iterable[Task]] = None) -> None:
        if task:
            self.add_task(task)

        self.worker = {worker.name: worker for worker in self.get_all_worker()}

    def add_job(self, job: job.Job) -> None:
        db.insert_job(job)

        for task in job.tasks:
            db.insert_task(task)

    def add_task(self, task: Task | Iterable[Task]) -> None:
        if isinstance(task, Task):
            db.insert_task(task)
            return

        for t in task:
            db.insert_task(t)

    def pop_task(self) -> Optional[tuple[Task, job.Job]]:
        ser_task = db.select_next_task()
        if not ser_task:
            return
        ser_job = db.select_job(ser_task["id"])
        if not ser_job:
            return

        task, j = Task.deserialize(ser_task), job.Job.deserialize(ser_job)
        if not task or not j:
            return

        return (task, j)

    def register_worker(self, worker: Worker) -> None:
        self.worker[worker.name] = worker
        db.insert_worker(worker)

    def get_all_tasks(self, job_id: str) -> list[SerializedTask]:
        return db.select_all_tasks(job_id)

    def get_all_jobs(self) -> list[SerializedJob]:
        return db.select_all_jobs()

    def get_all_worker(self) -> list[Worker]:
        return db.select_all_worker()

    def get_all_worker_dict(self) -> list[SerializedWorker]:
        return [w.serialize() for w in db.select_all_worker()]

    def update_task(self, task: Task) -> None:
        db.update_task(task)

    def update_worker(self, worker: Worker) -> None:
        db.update_worker(worker)

    def update_job(self, job: job.Job) -> None:
        db.update_job(job)

    def cleanup_jobs(self, task: Task) -> None:
        db.cleanup_completed_jobs(str(task.id))

    def get_job_by_task(self, task: Task) -> Optional[job.Job]:
        ser_job = db.select_job(str(task.id))
        if not ser_job:
            return

        return job.Job.deserialize(ser_job)
