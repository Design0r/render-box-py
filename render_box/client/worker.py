import json
import socket
import time

from render_box.shared.task import Task, init_commands


def start_worker():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ("localhost", 65432)
    client_socket.connect(server_address)
    init_commands()

    while True:
        try:
            start_time = time.perf_counter()

            message = {"message": "get_task"}
            json_data = json.dumps(message)

            client_socket.sendall(json_data.encode("utf-8"))
            response = client_socket.recv(1024).decode("utf-8")
            json_data = json.loads(response)

            if json_data["message"] == "task":
                command = Task.from_json(json_data["data"])
                command.run()

            elif json_data["message"] == "no_tasks":
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
