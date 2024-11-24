from typing import TYPE_CHECKING

from render_box.shared.message import Message, MessageRouter
from render_box.shared.worker import Worker

if TYPE_CHECKING:
    from render_box.server.server import ClientHandler

worker_router = MessageRouter(prefix="workers")


@worker_router.register(".register")
def register_worker(ctx: "ClientHandler", message: Message):
    worker = Worker.deserialize(message.data)
    if not worker:
        return

    registered_worker = ctx.job_manager.worker.get(worker.name)
    if registered_worker:
        ctx.worker = registered_worker
        ctx.update_worker(state="idle")
    else:
        ctx.worker.name = worker.name
        ctx.job_manager.register_worker(ctx.worker)

    ctx.send(Message("success").as_json())


@worker_router.register(".all")
def all_workers(ctx: "ClientHandler", message: Message):
    data = ctx.job_manager.get_all_worker_dict()
    message = Message("success", data=data)
    ctx.send(message.as_json())
