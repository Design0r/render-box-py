from render_box.server.connection import Connection
from render_box.shared.message import Message
from render_box.shared.serialize import SerializedJob, SerializedWorker
from render_box.shared.task import SerializedTask, Worker


class Controller:
    def __init__(self) -> None:
        self.connection = Connection.client_connection()
        server_address = ("localhost", 65432)
        self.connection.connect(server_address)

    def get_tasks(self, job_id: str) -> dict[str, SerializedTask]:
        msg = Message("all_tasks", data=job_id)
        data: dict[str, list[SerializedTask]] = self.connection.send_recv(
            msg.as_json(), buffer_size=100000
        )

        return {str(task["id"]): task for task in data["data"]}

    def get_workers(self) -> dict[str, Worker]:
        msg = Message("all_workers")
        data: dict[str, list[SerializedWorker]] = self.connection.send_recv(
            msg.as_json(), buffer_size=10000
        )

        response: dict[str, Worker] = {}
        for worker in data["data"]:
            new_worker = Worker.deserialize(worker)
            if not new_worker:
                continue
            response[new_worker.name] = new_worker

        return response

    def get_jobs(self) -> dict[str, SerializedJob]:
        msg = Message("all_jobs")
        data: dict[str, list[SerializedJob]] = self.connection.send_recv(
            msg.as_json(), buffer_size=100000
        )

        return {job["name"]: job for job in data["data"]}
