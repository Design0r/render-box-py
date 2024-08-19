import json
import socket
from threading import Thread

from render_box.shared.message import Message
from render_box.shared.task import Command, SerializedCommand, TaskManager


def handle_client(connection: socket.socket, task_manager: TaskManager):
    ip, port = connection.getpeername()
    client = f"{ip}:{port}"
    print(f"client {client} connected")

    while True:
        try:
            data = connection.recv(1024).decode("utf-8")
            json_data = json.loads(data)
            message = Message(**json_data)

            match message.message:
                case "command":
                    ser_cmd = SerializedCommand(**json_data["data"])
                    command = Command.from_json(ser_cmd)
                    task_manager.create_task(command)
                    return_msg = Message(message="task_created", data=None)
                    connection.sendall(return_msg.as_json())

                case "get_task":
                    task = task_manager.pop_task()
                    if not task:
                        message = Message(message="no_tasks", data=None)
                        connection.sendall(message.as_json())
                        print(f"{client} asked for task, none exist...")
                        continue

                    message = Message(message="task", data=task.serialize())
                    print(message.as_json())
                    connection.sendall(message.as_json())
                    print(f"sending {task} to {client}")

                case "close":
                    print(f"close message from {client}")
                    break

                case _:
                    continue

        except Exception as e:
            print(e)
            break

    print(f"client {client} disconnected")
    connection.close()


def start_server() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ("localhost", 65432)
    server_socket.bind(server_address)
    server_socket.listen(1)
    print("RenderBox server listening on", server_address)
    server_socket.settimeout(1.0)

    task_manager = TaskManager()

    while True:
        try:
            connection, _ = server_socket.accept()
            thread = Thread(
                target=handle_client, args=(connection, task_manager), daemon=True
            )
            thread.start()
        except socket.timeout:
            continue

    server_socket.close()
    print("RenderBox server has been stopped.")


if __name__ == "__main__":
    start_server()
