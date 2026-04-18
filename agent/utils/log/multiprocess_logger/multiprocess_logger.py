'''Simple wrapper around python's logging package'''

import os
import logging
from logging import handlers
import sys
import click
from logging import StreamHandler
import traceback
import inspect
from datetime import datetime

from .logging_levels import loglevel
from .logging_formatter import AntiColorFormatter, ConsoleFormatter
from .stream_to_logger import StreamToLogger

import multiprocessing
from multiprocessing import Process, current_process
from .handlers.queue_listener import QueueListener
from .handlers.queue_handler import QueueHandler
from .logger_base import Logger, getLogger
from .handlers.file_handler import CreateFileHandler
from logging.handlers import RotatingFileHandler, WatchedFileHandler
from .handlers.queue_handler import HandlerConfig

class MultiprocessLogger:

    listener: QueueListener
    queue: multiprocessing.Queue

    _handlers: list = []

    file_handler: RotatingFileHandler | WatchedFileHandler | None = None
    file_handler_enable: bool
    file_handler_log_dir: str
    file_handler_log_file: str
    file_handler_format: str
    file_handler_level: str
    file_handler_rotation_enable: bool
    file_handler_rotation_size_mb: int
    file_handler_rotation_backup_count: int

    console_handler: StreamHandler | None = None
    console_handler_enable: bool
    console_handler_format: str
    console_handler_level: str | int
    console_handler_color: bool

    clear_old_logs: bool
    max_retained_logs: int | None

    @classmethod
    def setup(cls,
        queue: multiprocessing.Queue = None
        ):

        loglevel.setup()

        cls.queue = queue

    @classmethod
    def setQueueListener(cls,
        file_handler_enable: bool = True,
        file_handler_log_dir: str = "log",
        file_handler_log_file: str = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.now()),
        file_handler_rotation_enable: bool = True,
        file_handler_rotation_size_mb: int = 10,
        file_handler_rotation_backup_count: int = 10,
        file_handler_format: str = "%(asctime)s %(process)d %(processName)s %(threadName)s %(levelname)s %(name)s # %(message)s",
        file_handler_level: str | int = logging.DEBUG,

        console_handler_enable: bool = True,
        console_handler_format: str = "%(asctime)s %(process)d %(processName)s %(threadName)s %(levelname)s %(name)s # %(message)s",
        console_handler_level: str | int = logging.DEBUG,
        console_handler_color: bool = True,

        clear_old_logs: bool = True,
        max_retained_logs: int = 10
        ) -> tuple[multiprocessing.Queue, QueueListener]:
    
        cls.file_handler_enable = file_handler_enable
        cls.file_handler_log_dir = file_handler_log_dir
        cls.file_handler_log_file = file_handler_log_file if file_handler_log_file.endswith(".log") else "%s.log" % (str(file_handler_log_file))
        cls.file_handler_format = file_handler_format
        cls.file_handler_level = file_handler_level
        cls.file_handler_rotation_enable = file_handler_rotation_enable
        cls.file_handler_rotation_size_mb = file_handler_rotation_size_mb
        cls.file_handler_rotation_backup_count = file_handler_rotation_backup_count

        cls.console_handler_enable = console_handler_enable
        cls.console_handler_format = console_handler_format
        cls.console_handler_level = console_handler_level
        cls.console_handler_color = console_handler_color

        cls.clear_old_logs = clear_old_logs
        cls.max_retained_logs = max_retained_logs

        if current_process().name != 'MainProcess':
            raise Exception("Queue listener can only be created on the main process!")

        cls.__set_file_handler()

        if cls.file_handler is not None:
            cls._handlers.append(cls.file_handler)

        cls.__set_console_handler()

        if cls.console_handler is not None:
            cls._handlers.append(cls.console_handler)

        cls.queue = multiprocessing.Queue()

        cls.listener = QueueListener(cls.queue, *cls._handlers)

        cls.listener.setup_unique_file_handler(
            file_handler_log_dir = cls.file_handler_log_dir
        )

        cls.listener.start()

    @classmethod
    def setLogger(cls,
        name: str | None,
        level: str | int = logging.DEBUG,
        handler_config_kwargs: dict = {},
        clear: bool = True
        ) -> Logger:

        if cls.queue is None:
            raise Exception("Logger queue is None")
        
        handler_config_kwargs['name'] = name

        handler_config = HandlerConfig(
                **handler_config_kwargs
            )

        if clear == True:
            cls.__clear_log_name(name)

        logger = getLogger(name)

        q_handler = QueueHandler(
            queue = cls.queue,
            handler_config = handler_config
            )

        logger.addHandler(q_handler)

        if isinstance(level, str) == True:
            
            logger.setLevel(getattr(logging, level.upper()))

        else:

            logger.setLevel(level)

        return logger

    @classmethod
    def __clear_log_name(cls, name: str) -> None:

        for logger_name, logger in logging.getLoggerClass().manager.loggerDict.copy().items():

            if logger_name == name:
                project_base_logger = logging.getLoggerClass().manager.loggerDict.get('ProjectBase', None)

                if project_base_logger is not None:
                    project_base_logger.trace("Clear logger: %s" % (str(name)))

                del logging.getLoggerClass().manager.loggerDict[name]
                break

    @classmethod
    def __set_console_handler(cls) -> None:

        if cls.console_handler_enable == True:

            cls.console_handler = logging.StreamHandler()

            if sys.stdout is not None:
                cls.console_handler.flush = sys.stdout.flush

            if isinstance(cls.console_handler_level, str) == True:
                
                cls.console_handler.setLevel(getattr(logging, cls.console_handler_level.upper()))

            else:

                cls.console_handler.setLevel(cls.console_handler_level)

            console_formatter = ConsoleFormatter(
                format = cls.console_handler_format,
                color = cls.console_handler_color
            )

            cls.console_handler.setFormatter(console_formatter)

    @classmethod
    def __set_file_handler(cls) -> None:

        if cls.file_handler_enable == True:

            cls.file_handler = CreateFileHandler(
                filename = os.path.join(cls.file_handler_log_dir, cls.file_handler_log_file),
                rotation_enable = cls.file_handler_rotation_enable,
                rotation_maxBytes = int(cls.file_handler_rotation_size_mb * 1024 * 1024), 
                rotation_backupCount = cls.file_handler_rotation_backup_count, 
                clear_old_logs = cls.clear_old_logs, 
                max_retained_logs = cls.max_retained_logs
            ).get_handler()

            if isinstance(cls.file_handler_level, str) == True:
                
                cls.file_handler.setLevel(getattr(logging, cls.file_handler_level.upper()))

            else:

                cls.file_handler.setLevel(cls.file_handler_level)
            
            fmt = AntiColorFormatter(cls.file_handler_format)

            cls.file_handler.setFormatter(fmt)
