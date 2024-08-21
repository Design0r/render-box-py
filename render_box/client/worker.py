import json
import socket
import time

from ..server.connection import Connection
from ..shared.message import Message
from ..shared.task import SerializedTask, Task, WorkerMetadata


def register_worker(connection: Connection) -> None:
    worker_name = socket.gethostname()
    metadata = WorkerMetadata(worker_name, "idle", time.time(), None)
    msg = Message(message="register_worker", data=metadata.serialize())
    connection.send_recv(msg.as_json())


def start_worker():
    connection = Connection.client_connection()
    server_address = ("localhost", 65432)
    connection.connect(server_address)

    register_worker(connection)

    while True:
        try:
            start_time = time.perf_counter()

            message = Message(message="get_task")
            response = connection.send_recv(message.as_json())
            message = Message(**json.loads(response))

            if message.message == "task":
                if not message.data:
                    print(f'message {message} has no field "data"')
                    continue

                command = Task.from_json(SerializedTask(**message.data))
                command.run()
                connection.send(Message("finished").as_json())

            elif message.message == "no_tasks":
                print("no task, waiting...")
                time.sleep(2)

            end_time = time.perf_counter()
            print(f"Task finished in {end_time - start_time:.2f}\n")

        except json.JSONDecodeError:
            print("connection to server lost")
            break

    connection.close()


if __name__ == "__main__":
    start_worker()
