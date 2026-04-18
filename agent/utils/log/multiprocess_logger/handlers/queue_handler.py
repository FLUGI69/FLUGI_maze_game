import logging
from logging import handlers
from typing import Any
from dataclasses import dataclass
import multiprocessing
from ..logging_levels import loglevel

@dataclass
class HandlerConfig:

    name: str

    file_handler_enable: bool = None
    file_handler_level: loglevel = None

    console_handler_enable: bool = None
    console_handler_level: loglevel = None

    unique_file_handler_enabled: bool = None
    unique_file_handler_log_file: str = None
    unique_file_handler_rotation_enable: bool = None
    unique_file_handler_rotation_size_mb: int = None
    unique_file_handler_rotation_backup_count: int = None
    unique_file_handler_clear_old_logs: bool = None
    unique_file_handler_max_retained_logs: int = None
    unique_file_handler_format: str = None
    unique_file_handler_level: loglevel = None

    def __post_init__(self):

        self.file_handler_level = self.__get_level(self.file_handler_level)
        self.console_handler_level = self.__get_level(self.console_handler_level)
        self.unique_file_handler_level = self.__get_level(self.unique_file_handler_level)

        if isinstance(self.unique_file_handler_log_file, str) == True and self.unique_file_handler_log_file.endswith(".log") == False:
            self.unique_file_handler_log_file = "%s.log" % (str(self.unique_file_handler_log_file))

    def __get_level(self, level: loglevel | str) -> loglevel:
        if isinstance(level, str) == True:
            return getattr(loglevel, str(level).upper())
        else:
            return level

import sys 
class QueueHandler(handlers.QueueHandler):

    queue: multiprocessing.Queue

    def __init__(self, 
                queue: multiprocessing.Queue,
                handler_config: HandlerConfig,
                ) -> None:
        
        self.__handler_config = handler_config

        super().__init__(queue)

    def prepare(self, record: logging.LogRecord) -> Any:

        setattr(record, 'handler_config', self.__handler_config)

        if hasattr(record, "websocket"):
            setattr(record, "websocket", None)

        return super().prepare(record)
    
    def enqueue(self, record: logging.LogRecord):
        if self.queue._closed == False:
            try:
                self.queue.put_nowait(record)
            except Exception as e:
                print(f'Error in queue handler: {e}')

    def emit(self, record):
        try:
            self.enqueue(self.prepare(record))
        except Exception:
            self.handleError(record)
