from render_box.server.connection import Connection
from render_box.shared.message import Message
from render_box.shared.task import SerializedTask, WorkerMetadata


class Controller:
    def __init__(self) -> None:
        self.connection = Connection.client_connection()
        server_address = ("localhost", 65432)
        self.connection.connect(server_address)

    def get_tasks(self) -> dict[str, SerializedTask]:
        msg = Message("all_tasks")
        data: dict[str, list[SerializedTask]] = self.connection.send_recv(
            msg.as_json(), buffer_size=100000
        )

        return {str(task["id"]): SerializedTask(**task) for task in data["data"]}

    def get_workers(self) -> dict[str, WorkerMetadata]:
        msg = Message("all_workers")
        data: dict[str, list[WorkerMetadata]] = self.connection.send_recv(
            msg.as_json(), buffer_size=10000
        )

        return {str(worker[0]): WorkerMetadata(*worker) for worker in data["data"]}
