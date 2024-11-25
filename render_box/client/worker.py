import json
import socket
import time

from ..server.connection import Connection
from ..shared.message import Message
from ..shared.task import Task
from ..shared.worker import Worker


def register_worker(connection: Connection) -> None:
    worker_name = socket.gethostname()
    metadata = Worker(None, worker_name)
    msg = Message(message="workers.register", data=metadata.serialize()).as_json()
    print(connection.send_recv(msg))


def start_worker():
    connection = Connection.client_connection()
    server_address = ("localhost", 65432)
    connection.connect(server_address)

    register_worker(connection)

    next_msg = Message("tasks.next").as_json()
    while True:
        try:
            start_time = time.perf_counter()

            response = connection.send_recv(next_msg)
            message = Message(**response)
            print(message)

            if message.data:
                command = Task.deserialize(message.data)
                if not command:
                    continue

                command.run()
                connection.send_recv(Message("tasks.complete").as_json())

            else:
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
