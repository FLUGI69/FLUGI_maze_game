from dataclasses import dataclass, field
import typing as t

@dataclass
class Worker:

    name: str
    running: bool = False
    started: bool = False
    setup_error: str | None = None
