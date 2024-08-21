import socket
from threading import Thread

from render_box.server import db

from ..server.connection import Connection
from ..shared.message import Message
from ..shared.task import SerializedTask, Task, TaskManager, WorkerMetadata


class CloseConnectionException(Exception): ...


class ClientHandler:
    def __init__(self, connection: Connection, task_manager: TaskManager) -> None:
        self.connection = connection
        self.task_manager = task_manager
        self.worker: WorkerMetadata = None

        ip, port = connection.socket.getpeername()
        self.client_ip = f"{ip}:{port}"

        print(f"client {self.client_ip} connected")

    def update_worker(self, worker: WorkerMetadata) -> None:
        self.worker = worker
        self.task_manager.update_worker(worker)

    def handle_message(self, message: Message) -> None:
        match message.message:
            case "register_worker":
                worker = WorkerMetadata(**message.data)
                self.worker = worker._replace(id=len(self.task_manager.worker) + 1)
                self.task_manager.register_worker(self.worker)
                self.connection.send(Message("success").as_json())

            case "task":
                data = SerializedTask(**message.data)
                task = Task.from_json(data)
                self.task_manager.add_task(task)
                self.connection.send(Message("task_created").as_json())

            case "get_task":
                task = self.task_manager.pop_task()
                if not task:
                    self.connection.send(Message("no_tasks").as_json())
                    print(f"{self.worker.name} asked for task, none exist...")
                    return

                self.worker = self.worker._replace(
                    task_id=str(task.id), state="working"
                )
                self.task_manager.update_worker(self.worker)
                message = Message.from_task(task)
                print(f"sending task to {self.worker.name}")
                response = self.connection.send_recv(message.as_json())
                message = Message(**response)
                if message.message == "finished":
                    updated_task = task._replace(state="finished")
                    self.task_manager.update_task(updated_task)
                    self.worker = self.worker._replace(task_id=None, state="idle")
                    self.task_manager.update_worker(self.worker)

            case "all_tasks":
                message = Message(
                    "all_tasks",
                    data=self.task_manager.get_all_tasks(),
                )
                self.connection.send(message.as_json())

            case "all_workers":
                message = Message(
                    "all_worker",
                    data=self.task_manager.get_all_worker(),
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

            except CloseConnectionException as e:
                print(e)
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

    server_socket.close()
    print("RenderBox server has been stopped.")


if __name__ == "__main__":
    start_server()
