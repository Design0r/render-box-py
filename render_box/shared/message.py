from __future__ import annotations

import json
from enum import StrEnum
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, NamedTuple, Optional

import render_box.shared.task as task
from render_box.shared.job import Job

if TYPE_CHECKING:
    from render_box.server.server import ClientHandler


class MessageType(StrEnum):
    pass


class Message(NamedTuple):
    message: str
    data: Optional[Any] = None

    def as_json(self, encoding: str = "utf-8") -> bytes:
        message = self._asdict()
        return json.dumps(message).encode(encoding)

    @classmethod
    def from_task(cls, task: task.Task) -> Message:
        return Message(message="tasks.create", data=task.serialize())

    @classmethod
    def from_job(cls, job: Job) -> Message:
        return Message(message="jobs.create", data=job.serialize())


type MsgHandlerFunc = Callable[[ClientHandler, Message], None]


class MessageRouter:
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.routes: dict[str, list[MsgHandlerFunc]] = DefaultDict(list)

    def serve(self, ctx: ClientHandler, message: Message):
        routes = self.routes.get(message.message)
        if not routes:
            ctx.connection.send(Message("unregistered message").as_json())
            return

        for handler in routes:
            handler(ctx, message)

    def register(self, message: str) -> Callable[[MsgHandlerFunc], MsgHandlerFunc]:
        def decorator(fn: MsgHandlerFunc) -> MsgHandlerFunc:
            self.routes[self.prefix + message].append(fn)

            @wraps(fn)
            def wrapper(ctx: ClientHandler, msg: Message):
                fn(ctx, msg)

            return wrapper

        return decorator

    def include_router(self, sub_router: MessageRouter):
        for k, v in sub_router.routes.items():
            self.routes[k].extend(v)
