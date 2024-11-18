from render_box.server.connection import Connection
from render_box.shared.message import Message
from render_box.shared.serialize import SerializedJob, SerializedTask, SerializedWorker


class Controller:
    def __init__(self) -> None:
        self.connection = Connection.client_connection()
        server_address = ("localhost", 65432)
        self.connection.connect(server_address)

    def get_tasks(self, job_id: str) -> dict[str, SerializedTask]:
        msg = Message("all_tasks", data=job_id)
        data: dict[str, list[SerializedTask]] = self.connection.send_recv(msg.as_json())

        return {str(task["id"]): task for task in data["data"]}

    def get_workers(self) -> dict[str, SerializedWorker]:
        msg = Message("all_workers")
        data: dict[str, list[SerializedWorker]] = self.connection.send_recv(
            msg.as_json()
        )

        return {w["name"]: w for w in data["data"]}

    def get_jobs(self) -> dict[str, SerializedJob]:
        msg = Message("all_jobs")
        data: dict[str, list[SerializedJob]] = self.connection.send_recv(msg.as_json())

        return {job["name"]: job for job in data["data"]}
