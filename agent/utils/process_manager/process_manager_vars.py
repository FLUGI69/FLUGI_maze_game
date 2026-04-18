from dataclasses import dataclass
from threading import Lock

@dataclass
class ProcessManagerVars:

    lock: Lock = None
    should_exit: bool = False

    def __post_init__(self):

        self.lock = Lock() if self.lock is None else self.lock
