from typing import TYPE_CHECKING

from render_box.shared.job import Job, JobState
from render_box.shared.message import Message, MessageRouter
from render_box.shared.task import Task, TaskState
from render_box.shared.worker import WorkerState

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


task_router = MessageRouter("tasks")


@task_router.register(".create")
def create_task(ctx: "ClientHandler", message: Message):
    job = Task.deserialize(message.data)
    if not job:
        return
    ctx.job_manager.add_task(job)
    ctx.send(Message("task_created").as_json())


@task_router.register(".next")
def next_task(ctx: "ClientHandler", message: Message):
    result = ctx.job_manager.pop_task()
    if not result:
        ctx.send(Message("tasks").as_json())
        print(f"{ctx.worker.name} asked for task, none exist...")
        return
    ctx.task, ctx.job = result

    ctx.update_worker(task_id=str(ctx.task.id), state="working")
    ctx.update_job(state=JobState.Progress)
    print(f"sending task to {ctx.worker.name}")
    ctx.send(Message("tasks", ctx.task.serialize()).as_json())


@task_router.register(".complete")
def complete_task(ctx: "ClientHandler", message: Message):
    ctx.update_task(state=TaskState.Completed)
    ctx.update_worker(task_id=None, state=WorkerState.Idle)
    if ctx.task:
        ctx.job_manager.cleanup_jobs(ctx.task)
        ctx.job = ctx.job_manager.get_job_by_task(ctx.task)
    ctx.send(Message("ok").as_json())


@task_router.register(".all")
def all_tasks(ctx: "ClientHandler", message: Message):
    if not message.data:
        return
    data = ctx.job_manager.get_all_tasks(message.data)
    message = Message("all_tasks", data=data)
    ctx.send(message.as_json())
