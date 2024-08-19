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
            message = Message.from_command(command)

            connection.send_recv(message.as_json())
            print(f"submitted {command}")

        except Exception as e:
            print(e)

    close_msg = Message(message="close")
    connection.send_recv(close_msg.as_json())
    connection.close()


if __name__ == "__main__":
    start_submitter()
