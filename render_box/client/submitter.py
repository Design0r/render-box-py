import uuid
from random import randint

from render_box.shared.job import Job
from render_box.shared.task import Task

from ..server.connection import Connection
from ..shared.commands import TestCommand
from ..shared.message import Message


def start_submitter(count: int = 1):
    connection = Connection.client_connection()
    server_address = ("localhost", 65432)
    connection.connect(server_address)

    m = Message("docs")
    print(connection.send_recv(m.as_json()))

    for _ in range(count):
        try:
            job = Job(f"Job {uuid.uuid4()}")
            for i in range(randint(1, 10)):
                task = Task(TestCommand((i // 2) + 1))
                job.add_task(task)
            message = Message.from_job(job)
            buffer = message.as_json()

            connection.send_recv(buffer)
            print("submitted Job")

        except Exception as e:
            print(e)

    close_msg = Message("close")
    connection.send(close_msg.as_json())
    connection.close()


if __name__ == "__main__":
    start_submitter()
