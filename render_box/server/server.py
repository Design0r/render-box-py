import json
import socket
from threading import Thread

from render_box.shared.task import Command, TaskManager, init_commands


def handle_client(connection: socket.socket, task_manager: TaskManager):
    ip, port = connection.getpeername()
    client = f"{ip}:{port}"
    print(f"client {client} connected")

    while True:
        try:
            data = connection.recv(1024).decode("utf-8")
            json_data = json.loads(data)

            if json_data["message"] == "command":
                command = Command.from_json(json_data["command"])
                print(command.duration)
                task_manager.create_task(command)
                message = {"message": "task_created"}
                connection.sendall(json.dumps(message).encode("utf-8"))

            elif json_data["message"] == "get_task":
                task = task_manager.pop_task()
                if not task:
                    message = {"message": "no_tasks"}
                    connection.sendall(json.dumps(message).encode("utf-8"))
                    print(f"{client} asked for task, none exist...")
                    continue

                message = {"message": "task", "data": task.serialize()}
                connection.sendall(json.dumps(message).encode("utf-8"))
                print(f"sending {task} to {client}")

            elif json_data["message"] == "close":
                break

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
    init_commands()

    while True:
        try:
            connection, client_address = server_socket.accept()
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

