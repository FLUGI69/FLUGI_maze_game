from logging import handlers, LogRecord, StreamHandler, Handler
from logging.handlers import RotatingFileHandler, WatchedFileHandler
from .queue_handler import HandlerConfig
from ..logging_levels import loglevel
import threading
from multiprocessing import Queue
import queue
from .file_handler import CreateFileHandler
import os
from ..logging_formatter import AntiColorFormatter
import typing as t

class QueueListener(handlers.QueueListener):

    _lock = threading.Lock()

    handlers: tuple

    unique_file_handler: list

    file_handler_log_dir: str = None

    def __init__(self, queue: Queue, *handlers: Handler, respect_handler_level: bool = False) -> None:

        self.unique_file_handler = []

        super().__init__(queue, *handlers, respect_handler_level=respect_handler_level)

    def add_handler(self, handler: Handler):

        with self._lock:

            self.handlers = self.handlers + (handler,)
    
    def __add_unique_file_handler(self, handler: RotatingFileHandler | WatchedFileHandler):

        with self._lock:

            self.unique_file_handler.append(handler)

    def handle(self, record: LogRecord) -> None:

        handlers = self.handlers

        handler_config = getattr(record, 'handler_config', None)

        if isinstance(handler_config, HandlerConfig):

            if handler_config.file_handler_enable is not None:

                if handler_config.file_handler_enable == False:

                    handlers = [handler for handler in handlers if not isinstance(handler, (RotatingFileHandler, WatchedFileHandler))]
            
            if handler_config.console_handler_enable is not None:

                if handler_config.console_handler_enable == False:

                    handlers = [handler for handler in handlers if not isinstance(handler, StreamHandler)]

            if handler_config.unique_file_handler_enabled == True:

                if next((True for handler in self.handlers if getattr(handler, 'name', None) is not None and getattr(handler, 'name') == handler_config.name), False) == False:

                    self.__trigger_unique_file_handler(handler_config)

        record = self.prepare(record)
        for handler in handlers:
            if not self.respect_handler_level:
                process = True
            else:
                process = record.levelno >= handler.level

            if isinstance(handler_config, HandlerConfig):

                if isinstance(handler, (RotatingFileHandler, WatchedFileHandler)) == True:
                    handler: RotatingFileHandler | WatchedFileHandler

                    if getattr(handler, 'unique_file_handler', False) == True and handler.name is not None:
   
                        if handler.name != handler_config.name:
                            continue

                        process = record.levelno >= handler.level

                    else:

                        if handler_config.file_handler_level is not None:
                            if loglevel.is_exist_level(handler_config.file_handler_level) == True:
                                process = record.levelno >= handler_config.file_handler_level

                elif isinstance(handler, StreamHandler) == True:
                    if handler_config.console_handler_level is not None:
                        if loglevel.is_exist_level(handler_config.console_handler_level) == True:
                            process = record.levelno >= handler_config.console_handler_level

            if process:
                handler.handle(record)

    def setup_unique_file_handler(self, file_handler_log_dir: str):

        self.file_handler_log_dir = file_handler_log_dir

    def __trigger_unique_file_handler(self, handler_config: HandlerConfig):

        print("add_unique_file_handler -> %s" % (str(handler_config.name)))

        return
