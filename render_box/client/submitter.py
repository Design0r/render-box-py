import socket

from render_box.shared.message import Message
from render_box.shared.task import TestCommand


def start_submitter(count: int = 1):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ("localhost", 65432)
    client_socket.connect(server_address)

    for _ in range(count):
        try:
            command = TestCommand(5)
            message = Message(message="command", data=command.serialize())
            print(message)

            client_socket.sendall(message.as_json())
            client_socket.recv(1024).decode("utf-8")

        except Exception as e:
            print(e)

    close_msg = Message(message="close", data=None)
    client_socket.sendall(close_msg.as_json())
    client_socket.recv(1024).decode("utf-8")
    client_socket.close()


if __name__ == "__main__":
    start_submitter()
