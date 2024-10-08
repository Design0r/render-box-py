import json
import socket
import time

from ..server.connection import Connection
from ..shared.message import Message
from ..shared.task import Task, TaskState
from ..shared.worker import Worker


def register_worker(connection: Connection) -> None:
    worker_name = socket.gethostname()
    metadata = Worker(None, worker_name)
    msg = Message(message="register_worker", data=metadata.serialize()).as_json()
    connection.send_recv(msg)


def start_worker():
    connection = Connection.client_connection()
    server_address = ("localhost", 65432)
    connection.connect(server_address)

    register_worker(connection)

    while True:
        try:
            start_time = time.perf_counter()

            message = Message("get_task").as_json()
            response = connection.send_recv(message)
            message = Message(**response)

            if message.message == "task":
                if not message.data:
                    print(f'message {message} has no field "data"')
                    continue

                command = Task.deserialize(message.data)
                if not command:
                    continue

                command.run()
                connection.send_recv(Message(TaskState.Completed).as_json())

            elif message.message == "no_tasks":
                print("no task, waiting...")
                time.sleep(2)
                continue

            end_time = time.perf_counter()
            print(f"Task finished in {end_time - start_time:.2f}s\n")

        except json.JSONDecodeError:
            print("connection to server lost")
            break

    connection.close()


if __name__ == "__main__":
    start_worker()
