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
        # Check if the event matches any registered wildcard event
        matched_events = [
            e for e in cls._events if fnmatch(event, e) or fnmatch(e, event)
        ]

        if not matched_events:
            print(
                f"No matching wildcard event found for '{event}'. Please register the event or a matching wildcard."
            )
            return

        for matched_event in matched_events:
            if callable in cls._events[matched_event]:
                print(f"Callable already registered for event '{matched_event}'")
                return

            cls._events[matched_event].append(callable)
            print(f"Callable connected to event '{matched_event}'")

    @classmethod
    def emit(cls, event: str, *args: Any, **kwargs: Any) -> None:
        matched_events = [e for e in cls._events if fnmatch(e, event)]

        if not matched_events:
            print(f"No matching events found for {event}")
            return

        for matched_event in matched_events:
            for fn in cls._events[matched_event]:
                fn(*args, **kwargs)
