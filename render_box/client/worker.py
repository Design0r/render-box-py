import json
import socket
import time

from render_box.shared.message import Message
from render_box.shared.task import SerializedTask, Task


def start_worker():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ("localhost", 65432)
    client_socket.connect(server_address)

    while True:
        try:
            start_time = time.perf_counter()

            message = Message(message="get_task", data=None)
            client_socket.sendall(message.as_json())
            response = client_socket.recv(1024).decode("utf-8")
            json_data = json.loads(response)
            message = Message(**json_data)
            print(json_data)

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

    client_socket.close()


if __name__ == "__main__":
    start_worker()
