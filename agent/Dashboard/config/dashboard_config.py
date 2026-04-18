import typing as t
import logging
import multiprocessing
from time import time

from utils.dataclass import DataclassBaseModel
from utils.agent import Agent
from utils.dc.agent_stats import AgentStats

class DashboardConfig(DataclassBaseModel):

    logger: logging.Logger = None
    
    host: str = "127.0.0.1"
    port: int = 8050

    update_ms:  int = 1000

    file: str = None
    
    logging_queue: multiprocessing.Queue = None
    
    before_startup_callback: t.Callable[[], t.Awaitable[None]] = None
    after_startup_callback: t.Callable[[], t.Awaitable[None]] = None
    before_shutdown_callback: t.Callable[[], t.Awaitable[None]] = None
    after_shutdown_callback: t.Callable[[], t.Awaitable[None]] = None

    worker_process_start_callback: t.Callable = None
    
    worker_process_start_kwargs: dict[str, t.Any] = {}
    
    worker_exit_callback: t.Callable[[str], None] = None
    
    worker_restarted_callback: t.Callable[[str], None] = None
    
    agent: Agent = None
    agent_stats: AgentStats = None
    
    __main_worker_instance: bool = False
    
    __server_start_time: int = None
    
    @property
    def main_worker_instance(self):
        return self.__main_worker_instance
    
    @property
    def server_start_time(self):
        return self.__server_start_time

    def set_logger(self) -> None:

        self.logger = logging.getLogger(self.logger.name if self.logger is not None else "Dashboard")

    def __post_init__(self):

        self.logger = self.logger if self.logger is not None else logging.getLogger("Dashboard")
        
        self.__server_start_time = int(time())

    def set_main_instance(self):

        self.__main_worker_instance = True
