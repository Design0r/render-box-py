from fnmatch import fnmatch
from typing import Any, Callable

Callback = Callable[..., Any]


class EventSystem:
    _events: dict[str, list[Callback]] = {}

    @classmethod
    def register_event(cls, event: str) -> None:
        if event in cls._events:
            print(f"event {event} already registered")
            return
        cls._events[event] = []

    @classmethod
    def connect(cls, event: str, callable: Callback) -> None:
        events = (e for e in cls._events if fnmatch(event, e) or fnmatch(e, event))

        if not events:
            print(f"no matching event found for '{event}'")
            return

        for e in events:
            if callable in cls._events[e]:
                print(f"callable already registered for event '{e}'")
                return

            cls._events[e].append(callable)
            print(f"callable connected to event '{e}'")

    @classmethod
    def emit(cls, event: str, *args: Any, **kwargs: Any) -> None:
        matched_events = (e for e in cls._events if fnmatch(e, event))

        if not matched_events:
            print(f"no matching events found for {event}")
            return

        for matched_event in matched_events:
            for fn in cls._events[matched_event]:
                fn(*args, **kwargs)
