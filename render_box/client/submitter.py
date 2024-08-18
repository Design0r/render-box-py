import json
import socket

from render_box.shared.task import TestCommand


def start_submitter(count=1):
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the server's address and port
    server_address = ("localhost", 65432)
    client_socket.connect(server_address)

    for i in range(count):
        try:
            command = TestCommand(5)
            message = {"message": "command", "command": command.serialize()}
            print(message)
            json_data = json.dumps(message)

            client_socket.sendall(json_data.encode("utf-8"))
            client_socket.recv(1024).decode("utf-8")

        except Exception as e:
            print(e)

    client_socket.sendall(json.dumps({"message": "close"}).encode("utf-8"))
    client_socket.recv(1024).decode("utf-8")
    client_socket.close()


if __name__ == "__main__":
    start_submitter()
