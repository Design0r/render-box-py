import json
import socket
from threading import Thread

from render_box.server import db

from ..server.connection import Connection
from ..shared.message import Message
from ..shared.task import SerializedTask, Task, TaskManager, WorkerMetadata


def handle_client(connection: Connection, task_manager: TaskManager):
    ip, port = connection.socket.getpeername()
    client = f"{ip}:{port}"

    print(f"client {client} connected")

    while True:
        try:
            data = connection.recv()
            json_data = json.loads(data)
            message = Message(**json_data)

            match message.message:
                case "register_worker":
                    worker = WorkerMetadata(**message.data)
                    task_manager.register_worker(worker)
                    connection.send(Message(message="success").as_json())

                case "task":
                    data = SerializedTask(**json_data["data"])
                    task = Task.from_json(data)
                    task_manager.add_task(task)
                    return_msg = Message(message="task_created")
                    connection.send(return_msg.as_json())

                case "get_task":
                    task = task_manager.pop_task()
                    if not task:
                        message = Message(message="no_tasks")
                        connection.send(message.as_json())
                        print(f"{client} asked for task, none exist...")
                        continue

                    message = Message.from_task(task)
                    print(f"sending task to {client}")
                    response = connection.send_recv(message.as_json())
                    message = Message(**json.loads(response))
                    if message.message == "finished":
                        updated_task = task._replace(state="finished")
                        task_manager.update_task(updated_task)

                case "all_tasks":
                    message = Message(
                        message="all_tasks",
                        data={"tasks": task_manager.get_all_tasks()},
                    )
                    connection.send(message.as_json())

                case "all_workers":
                    message = Message(
                        message="all_worker",
                        data={"worker": task_manager.get_all_worker()},
                    )
                    connection.send(message.as_json())

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
    server_address = ("localhost", 65432)
    server_socket = Connection.server_connection(server_address)
    print("RenderBox server listening on", server_address)

    db.init_db()

    task_manager = TaskManager()

    while True:
        try:
            connection = server_socket.accept()
            thread = Thread(
                target=handle_client,
                args=(Connection(connection), task_manager),
                daemon=True,
            )
            thread.start()
        except socket.timeout:
            continue

    server_socket.close()
    print("RenderBox server has been stopped.")


if __name__ == "__main__":
    start_server()
