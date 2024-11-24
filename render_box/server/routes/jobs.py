from typing import TYPE_CHECKING

from render_box.shared.job import Job
from render_box.shared.message import Message, MessageRouter

if TYPE_CHECKING:
    from render_box.server.server import ClientHandler

job_router = MessageRouter("jobs")


@job_router.register(".create")
def create_job(ctx: "ClientHandler", message: Message):
    job = Job.deserialize(message.data)
    if not job:
        return
    ctx.job_manager.add_job(job)
    print("job added")
    ctx.send(Message("job_created").as_json())


@job_router.register(".all")
def all_jobs(ctx: "ClientHandler", message: Message):
    data = ctx.job_manager.get_all_jobs()
    message = Message("all_jobs", data=data)
    ctx.send(message.as_json())
