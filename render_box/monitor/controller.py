import json

from render_box.server.connection import Connection
from render_box.shared.message import Message
from render_box.shared.task import SerializedTask, Task


class Controller:
    def __init__(self) -> None:
        self.connection = Connection.client_connection()
        server_address = ("localhost", 65432)
        self.connection.connect(server_address)

    def get_tasks(self) -> dict[str, SerializedTask]:
        msg = Message("all_tasks")
        response = self.connection.send_recv(msg.as_json())
        data = json.loads(response)

        return {
            str(task["id"]): SerializedTask(**task) for task in data["data"]["tasks"]
        }
