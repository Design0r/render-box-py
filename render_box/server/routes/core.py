from typing import TYPE_CHECKING

from render_box.shared.exceptions import CloseConnectionException
from render_box.shared.message import Message, MessageRouter

if TYPE_CHECKING:
    from render_box.server.server import ClientHandler

core_router = MessageRouter("")


@core_router.register("close")
def close(ctx: "ClientHandler", message: Message):
    print(f"close message from {ctx.worker.name}")
    raise CloseConnectionException(ctx.worker.name)


@core_router.register("docs")
def docs(ctx: "ClientHandler", message: Message):
    data = tuple(ctx.router.routes.keys())
    message = Message("docs", data=data)
    ctx.send(message.as_json())
