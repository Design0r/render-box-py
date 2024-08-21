from datetime import datetime


def format_timestamp(timestamp: float, format: str = r"%d-%m-%Y, %H:%M-%S") -> str:
    return datetime.fromtimestamp(timestamp).strftime(format)
