import socket
from threading import Thread
from typing import Any, Optional

from render_box.server import db
from render_box.shared.worker import WorkerState

from ..server.connection import Connection
from ..shared.message import Message
from ..shared.task import Task, TaskManager, TaskState, Worker


class CloseConnectionException(Exception): ...


class ClientHandler:
    def __init__(self, connection: Connection, task_manager: TaskManager) -> None:
        self.connection = connection
        self.task_manager = task_manager
        self.worker = Worker(len(self.task_manager.worker) + 1, "unknown")
        self.task: Optional[Task] = None

        ip, port = connection.socket.getpeername()
        self.client_ip = f"{ip}:{port}"

        print(f"client {self.client_ip} connected")

    def update_worker(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self.worker, k, v)
        self.task_manager.update_worker(self.worker)

    def update_task(self, **kwargs: Any) -> None:
        if not self.task:
            return
        for k, v in kwargs.items():
            setattr(self.task, k, v)

        self.task_manager.update_task(self.task)

    def handle_message(self, message: Message) -> None:
        match message.message:
            case "register_worker":
                worker = Worker.deserialize(message.data)
                if not worker:
                    return

                registered_worker = self.task_manager.worker.get(worker.name)
                if registered_worker:
                    self.worker = registered_worker
                    self.update_worker(state="idle")
                else:
                    self.worker.name = worker.name
                    self.task_manager.register_worker(self.worker)
                self.connection.send(Message("success").as_json())

            case "task":
                task = Task.deserialize(message.data)
                if not task:
                    return
                self.task_manager.add_task(task)
                self.connection.send(Message("task_created").as_json())

            case "get_task":
                self.task = self.task_manager.pop_task()
                if not self.task:
                    self.connection.send(Message("no_tasks").as_json())
                    print(f"{self.worker.name} asked for task, none exist...")
                    return

                self.update_worker(task_id=str(self.task.id), state="working")
                message = Message.from_task(self.task)
                print(f"sending task to {self.worker.name}")
                self.connection.send(message.as_json())

            case "completed":
                self.update_task(state=TaskState.Completed)
                self.update_worker(task_id=None, state=WorkerState.Idle)

            case "all_tasks":
                message = Message(
                    "all_tasks",
                    data=self.task_manager.get_all_tasks(),
                )
                self.connection.send(message.as_json())

            case "all_workers":
                message = Message(
                    "all_worker",
                    data=self.task_manager.get_all_worker_dict(),
                )
                self.connection.send(message.as_json())

            case "close":
                print(f"close message from {self.worker.name}")
                raise CloseConnectionException(self.worker.name)

            case _:
                return

    def run(self) -> None:
        while True:
            try:
                data = self.connection.recv()
                message = Message(**data)
                self.handle_message(message)

            except Exception as e:
                print(e)
                self.update_worker(state="offline", task_id=None)
                self.update_task(state="waiting")
                break

        print(f"client {self.worker.name} disconnected")
        self.connection.close()


def start_server() -> None:
    server_address = ("localhost", 65432)
    server_socket = Connection.server_connection(server_address)
    print("RenderBox server listening on", server_address)

    db.init_db()

    task_manager = TaskManager()

    while True:
        try:
            connection = server_socket.accept()
            client_handler = ClientHandler(Connection(connection), task_manager)
            thread = Thread(
                target=client_handler.run,
            )
            thread.start()
        except socket.timeout:
            continue


if __name__ == "__main__":
    start_server()
