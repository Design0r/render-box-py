from __future__ import annotations

import socket


class Connection:
    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket

    def send(self, data: bytes):
        self.socket.sendall(data)

    def send_recv(self, data: bytes, buffer_size: int = 1024) -> str:
        self.socket.sendall(data)
        response = self.socket.recv(buffer_size).decode("utf-8")

        return response

    def recv(self) -> str:
        return self.socket.recv(1024).decode("utf-8")

    def close(self) -> None:
        self.socket.close()

    def connect(self, adress: tuple[str, int]) -> None:
        self.socket.connect(adress)

    @classmethod
    def client_connection(cls) -> Connection:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return Connection(client_socket)

    @classmethod
    def server_connection(cls, adress: tuple[str, int]) -> Connection:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(adress)
        server_socket.listen(1)
        server_socket.settimeout(1.0)

        return Connection(server_socket)

    def accept(self) -> socket.socket:
        socket, _ = self.socket.accept()

        return socket
