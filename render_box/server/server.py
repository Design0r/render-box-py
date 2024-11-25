import socket
from threading import Thread
from typing import Any, Optional

from render_box.server import db
from render_box.server.job_manager import JobManager
from render_box.shared.job import Job, JobState
from render_box.shared.worker import WorkerState

from ..server.connection import Connection
from ..shared.message import Message, MessageRouter
from ..shared.task import Task, TaskState
from ..shared.worker import Worker
from .routes import core_router, job_router, task_router, worker_router


class ClientHandler:
    def __init__(
        self, connection: Connection, job_manager: JobManager, router: MessageRouter
    ) -> None:
        self.connection = connection
        self.job_manager = job_manager
        self.router = router
        self.worker = Worker(len(self.job_manager.worker) + 1, "unknown")
        self.task: Optional[Task] = None
        self.job: Optional[Job] = None

        ip, port = connection.socket.getpeername()
        self.client_ip = f"{ip}:{port}"

        print(f"client: {self.client_ip} connected")

    def update_worker(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self.worker, k, v)
        self.job_manager.update_worker(self.worker)

    def update_task(self, **kwargs: Any) -> None:
        if not self.task:
            return
        for k, v in kwargs.items():
            setattr(self.task, k, v)

        self.job_manager.update_task(self.task)

    def update_job(self, **kwargs: Any) -> None:
        if not self.job:
            return
        for k, v in kwargs.items():
            setattr(self.job, k, v)

        self.job_manager.update_job(self.job)

    def handle_message(self, message: Message) -> None:
        print(f"MSG: {message}")
        self.router.serve(self, message)

    def send(self, data: bytes):
        self.connection.send(data)

    def run(self) -> None:
        while True:
            try:
                data = self.connection.recv()
                message = Message(**data)
                self.handle_message(message)
            except Exception as e:
                print(e)
                self.update_worker(state=WorkerState.Offline, task_id=None)
                if self.task and self.task.state == TaskState.Progress:
                    self.update_task(state=TaskState.Waiting)
                if self.job and not self.job.state == JobState.Completed:
                    self.update_job(state=JobState.Waiting)
                break

        print(f"client {self.worker.name} disconnected")
        self.connection.close()


def start_server() -> None:
    server_address = ("localhost", 65432)
    server_socket = Connection.server_connection(server_address)
    print("RenderBox server listening on", server_address)

    db.init_db()

    job_manager = JobManager()
    router = MessageRouter()
    router.include_router(core_router)
    router.include_router(worker_router)
    router.include_router(task_router)
    router.include_router(job_router)

    while True:
        try:
            sock = server_socket.accept()
            client_handler = ClientHandler(Connection(sock), job_manager, router)
            thread = Thread(target=client_handler.run, daemon=True)
            thread.start()
        except socket.timeout:
            continue


if __name__ == "__main__":
    start_server()
