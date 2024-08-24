from datetime import datetime


def format_timestamp(timestamp: float, format: str = r"%d-%m-%Y, %H:%M:%S") -> str:
    return datetime.fromtimestamp(timestamp).strftime(format)


def class_name_from_repr(name: str):
    return name.split(".")[-1].split(" ")[0]
