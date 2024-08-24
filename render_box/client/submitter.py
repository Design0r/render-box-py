from uuid import uuid4

from render_box.shared.task import Task

from ..server.connection import Connection
from ..shared.commands import TestCommand
from ..shared.message import Message


def start_submitter(count: int = 1):
    connection = Connection.client_connection()
    server_address = ("localhost", 65432)
    connection.connect(server_address)

    for _ in range(count):
        try:
            command = TestCommand(5)
            task = Task(uuid4(), 50, command)
            message = Message.from_task(task)

            response = connection.send_recv(message.as_json())
            print(response)
            print("submitted command")

        except Exception as e:
            print(e)

    close_msg = Message("close")
    connection.send(close_msg.as_json())
    connection.close()


if __name__ == "__main__":
    start_submitter()
