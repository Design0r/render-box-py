import socket
from threading import Thread
from typing import Any, Optional

from render_box.server import db
from render_box.server.job_manager import JobManager
from render_box.shared.job import Job, JobState
from render_box.shared.worker import WorkerState

from ..server.connection import Connection
from ..shared.message import Message
from ..shared.task import Task, TaskState
from ..shared.worker import Worker


class CloseConnectionException(Exception): ...


class ClientHandler:
    def __init__(self, connection: Connection, job_manager: JobManager) -> None:
        self.connection = connection
        self.job_manager = job_manager
        self.worker = Worker(len(self.job_manager.worker) + 1, "unknown")
        self.task: Optional[Task] = None
        self.job: Optional[Job] = None

        ip, port = connection.socket.getpeername()
        self.client_ip = f"{ip}:{port}"

        print(f"client {self.client_ip} connected")

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
        match message.message:
            case "register_worker":
                worker = Worker.deserialize(message.data)
                if not worker:
                    return

                registered_worker = self.job_manager.worker.get(worker.name)
                if registered_worker:
                    self.worker = registered_worker
                    self.update_worker(state="idle")
                else:
                    self.worker.name = worker.name
                    self.job_manager.register_worker(self.worker)
                self.connection.send(Message("success").as_json())

            case "buffer_size":
                size = message.data
                if not isinstance(size, int):
                    return
                self.buffer_size = size
                self.connection.send(Message("changed_buffer").as_json())

            case "job":
                job = Job.deserialize(message.data)
                if not job:
                    return
                self.job_manager.add_job(job)
                print("job added")
                self.connection.send(Message("job_created").as_json())

            case "task":
                job = Task.deserialize(message.data)
                if not job:
                    return
                self.job_manager.add_task(job)
                self.connection.send(Message("task_created").as_json())

            case "get_task":
                result = self.job_manager.pop_task()
                if not result:
                    self.connection.send(Message("no_tasks").as_json())
                    print(f"{self.worker.name} asked for task, none exist...")
                    return
                self.task, self.job = result

                self.update_worker(task_id=str(self.task.id), state="working")
                self.update_job(state=JobState.Progress)
                message = print(f"sending task to {self.worker.name}")
                self.connection.send(Message.from_task(self.task).as_json())

            case "completed":
                self.update_task(state=TaskState.Completed)
                self.update_worker(task_id=None, state=WorkerState.Idle)
                if self.task:
                    self.job_manager.cleanup_jobs(self.task)
                    self.job = self.job_manager.get_job_by_task(self.task)
                self.connection.send(Message("ok").as_json())

            case "all_jobs":
                message = Message(
                    "all_jobs",
                    data=self.job_manager.get_all_jobs(),
                )
                self.connection.send(message.as_json())

            case "all_tasks":
                message = Message(
                    "all_tasks",
                    data=self.job_manager.get_all_tasks(message.data),
                )
                self.connection.send(message.as_json())

            case "all_workers":
                message = Message(
                    "all_worker",
                    data=self.job_manager.get_all_worker_dict(),
                )
                self.connection.send(message.as_json())

            case "close":
                print(f"close message from {self.worker.name}")
                raise CloseConnectionException(self.worker.name)

            case _:
                raise ValueError(f"unexpected message {message.message}")

    def run(self) -> None:
        while True:
            try:
                data = self.connection.recv()
                message = Message(**data)
                self.handle_message(message)
            except Exception as e:
                print(e)
                self.update_worker(state="offline", task_id=None)
                if self.task and self.task.state == TaskState.Progress:
                    self.update_task(state="waiting")
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

    while True:
        try:
            connection = server_socket.accept()
            client_handler = ClientHandler(Connection(connection), job_manager)
            thread = Thread(target=client_handler.run)
            thread.start()
        except socket.timeout:
            continue


if __name__ == "__main__":
    start_server()
