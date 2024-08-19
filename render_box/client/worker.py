import json
import time

from render_box.server.connection import Connection
from render_box.shared.message import Message
from render_box.shared.task import SerializedTask, Task


def start_worker():
    connection = Connection.client_connection()
    server_address = ("localhost", 65432)
    connection.connect(server_address)

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
