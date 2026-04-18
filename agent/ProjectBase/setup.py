from utils.patch import disableDistutilsWarning

disableDistutilsWarning()

import threading
from pathlib import Path
from datetime import datetime
import sys
import os
import signal
import psutil
import traceback
import types as types
import inspect
import time
import multiprocessing
import logging
import builtins

from beartype import beartype
from .base import ProjectBase
from types import ModuleType
import builtins
import typing
from utils.log.multiprocess_logger.logger_base import Logger
from utils.time import Time

from utils.string import String

from utils.log.multiprocess_logger.default_log import defaultLoggers
from utils.log.multiprocess_logger.logging_levels import loglevel
from utils.log.multiprocess_logger.logger_base import Logger, getLogger
from utils.log.multiprocess_logger.handlers.queue_handler import HandlerConfig
from utils.log.multiprocess_logger.multiprocess_logger import MultiprocessLogger
from utils.log.multiprocess_logger.stream_to_logger import StreamToLogger
from utils.classes import get_all_subclasses


class Setup:

    init_finished: bool = False

    log: Logger = ProjectBase.getLogger('ProjectBase')

    @beartype
    def __init__(self,
        import_file: str = __file__,
        debug: bool = True,
        timezone: str = "Europe/Budapest",
        timeFormat: str = "%Y-%m-%d %H:%M:%S.%f",
        exitSleep: int = 1,
        beforeExitCallback: object | None = None,
        exitCallback: object | None = None,
        exitQuestion: bool = True,
        sigintHandler: bool = True,
        log_names: object | None = None,
        level: str | int = loglevel.DEBUG,
        stdout_level: str | int = loglevel.TRACE,
        
        file_handler_enable: bool = True,
        file_handler_log_dir: str = "log",
        file_handler_log_file: str = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.now()),
        file_handler_rotation_enable: bool = True,
        file_handler_rotation_size_mb: int = 10,
        file_handler_rotation_backup_count: int = 10,
        file_handler_format: str = "%(asctime)s %(process)d %(processName)s %(threadName)s %(levelname)s %(name)s # %(message)s",
        file_handler_level: str | int = loglevel.DEBUG,
        
        console_handler_enable: bool = True,
        console_handler_format: str = "%(asctime)s %(process)d %(processName)s %(threadName)s %(levelname)s %(name)s # %(message)s",
        console_handler_level: str | int = loglevel.DEBUG,
        console_handler_color: bool = True,
        
        clear_old_logs: bool = True,
        max_retained_logs: int = 10
        ) -> None:

        if Setup.init_finished == True:
            raise Exception("Already initialized!")


        # Filter the setuptools UserWarning until we stop relying on distutils

        ProjectBase.exit_sleep = exitSleep

        ProjectBase.exit_question = exitQuestion

        ProjectBase.before_exit_callback = beforeExitCallback

        ProjectBase.exit_callback = exitCallback

        ProjectBase.debug = debug

        ProjectBase.pid = os.getpid()

        if sigintHandler == True:

            signal.signal(signal.SIGINT, ProjectBase.sigint_handler)

        ProjectBase.exit_bak = sys.exit
        ProjectBase.quit_bak = builtins.quit

        sys.exit = ProjectBase.exit
        builtins.exit = ProjectBase.exit
        builtins.quit = ProjectBase.exit

        ProjectBase.__file__ = import_file

        ProjectBase.rootPath = os.path.abspath(os.curdir)

        ProjectBase.currentDir = ProjectBase.rootPath
        
        ProjectBase.filePath = os.path.dirname(ProjectBase.__file__)

        ProjectBase.homePath = str(Path.home())

        ProjectBase.process = psutil.Process(ProjectBase.pid)

        ProjectBase.Time = Time(
            timezone = timezone, 
            timeformat = timeFormat
        )

        if log_names is None:
            log_names = ProjectBase.log

        if ProjectBase.debug == False: 
            setattr(ProjectBase.log.ProjectBase, 'level', loglevel.INFO)
            # ProjectBase.log.ProjectBase = hiddenLogger

        # from .utils.log import multiprocess_logger
            
        MultiprocessLogger.setup(
            # file_handler_log_dir = file_handler_log_dir,
            queue = None if ProjectBase.is_main_process == True else ProjectBase.logging.multiprocessing_queue
        )

        if ProjectBase.is_main_process == True:

            MultiprocessLogger.setQueueListener(
                file_handler_enable = file_handler_enable,
                file_handler_log_dir = file_handler_log_dir,
                file_handler_log_file = file_handler_log_file,
                file_handler_rotation_enable = file_handler_rotation_enable,
                file_handler_rotation_size_mb = file_handler_rotation_size_mb,
                file_handler_rotation_backup_count = file_handler_rotation_backup_count,
                file_handler_format = file_handler_format,
                file_handler_level = file_handler_level,

                console_handler_enable = console_handler_enable,
                console_handler_format = console_handler_format,
                console_handler_level = console_handler_level,
                console_handler_color = console_handler_color,

                clear_old_logs = clear_old_logs,
                max_retained_logs = max_retained_logs,
            )

            ProjectBase.logging.multiprocessing_queue, ProjectBase.logging.multiprocessing_queue_listener = MultiprocessLogger.queue, MultiprocessLogger.listener

        else:

            if ProjectBase.logging.multiprocessing_queue is None:
                raise Exception("ProjectBase.logging.multiprocessing_queue is None. Set it before setup logger. This is created by the main process when you call this function there.")

        # ProjectBase.logging.logger = multiprocess_logger

        self.__set_loggers(
            logObjs = log_names,
            level = level
        )
        
        logging.captureWarnings(True)

        if sys.stdout is not None:

            stdout_level = getattr(logging, stdout_level.upper()) if isinstance(stdout_level, str) == True else stdout_level

            sys.stdout = StreamToLogger(ProjectBase.log.stdout, stdout_level)

        if sys.stderr is not None:

            ProjectBase.stderr_bak = sys.stderr

            sys.stderr = StreamToLogger(ProjectBase.log.stderr, loglevel.ERROR)

        self.log = ProjectBase.getLogger('ProjectBase')

        if ProjectBase.is_main_process == True:
            
            self.log.trace("rootPath: %s" % str(ProjectBase.rootPath)) # mostani mappa utvonala ahhol az exe inditva lett

            self.log.trace("filePath: %s" % str(ProjectBase.filePath)) # Exe inditasanal fontos mert tempbe rakja és ez annak az utvonala

            self.log.trace("Home Path: %s" % str(ProjectBase.homePath))

            self.log.trace("Pid: %s" % str(ProjectBase.pid))

            self.log.trace('TimeZone: %s' % str(ProjectBase.Time.timezone))

            self.log.trace('TimeFormat: %s' % str(ProjectBase.Time.strfTime()))

            # self.log.warning("Press CTRL+C to quit")

        Setup.init_finished = True

    def __get_child_wrapper(self):

        def getChild(self: 'Logger', suffix_name: str) -> 'Logger':

            logger_name = '.'.join((self.name, suffix_name))

            child_logger = logging.getLoggerClass().manager.loggerDict.get(logger_name, None)

            if child_logger is not None:
                return child_logger

            return self.getChildLogger(suffix_name = suffix_name)
        
        return getChild

    def __get_child_logger_wrapper(self):

        def getChildLogger(self: Logger,
            suffix_name: str, 
            level: loglevel = None,
            propagate: bool = False,
            **kwargs
            ) -> Logger: 
            
            handler_config_kwargs = {param_name: kwargs[param_name] for param_name in inspect.getfullargspec(HandlerConfig).args if param_name != 'self' and param_name in kwargs and kwargs[param_name] is not None}

            name = '.'.join((self.name, suffix_name))

            ProjectBase.log.ProjectBase.trace("'%s' child logger handler_config_kwargs: %s" % (str(name), str(handler_config_kwargs)))

            if level is None:
                
                level = self.level
                
            else:
                
                level = getattr(loglevel, str(level).upper()) if isinstance(level, str) == True else level
                
            # print(logging.Logger.manager.loggerDict)
            # if name not in logging.Logger.manager.loggerDict.keys():

            if next((True for logger_name in list(logging.Logger.manager.loggerDict.keys()) if name == logger_name), False) == False:

                child_logger = MultiprocessLogger.setLogger(
                    name = name,
                    # listener = ProjectBase.logging.multiprocessing_queue_listener,
                    # queue = ProjectBase.logging.multiprocessing_queue,
                    level = self.level if loglevel.is_exist_level(level) == False else level,
                    handler_config_kwargs = handler_config_kwargs
                )
            
                child_logger.propagate = propagate

                log_item = '_'.join(name.split("."))

                subclasses = ProjectBase.__subclasses__()

                for subclass in subclasses:
                    
                    setattr(subclass.log, str(log_item), child_logger)

                setattr(ProjectBase.log, log_item, child_logger)

                ProjectBase.log.ProjectBase.trace("Set '%s' logger" % (str(name)))

            else:

                child_logger = logging.Logger.manager.loggerDict[name]
            
            return child_logger
        
        return getChildLogger

    def __set_loggers(self,
        logObjs,
        level: str | int
        ):

        defaultLogNames = [attr for attr in vars(defaultLoggers) if not attr.startswith("__")]
        newLogNames = [attr for attr in vars(logObjs) if not attr.startswith("__")]

        logNames = []

        for item in defaultLogNames:
            
            if item not in logNames:
                logNames.append(item)    

        for item in newLogNames:
            
            if item not in logNames:
                logNames.append(item)

        for log_item in logNames:

            set_logger = True

            if log_item.lower() == "ProjectBase".lower() and ProjectBase.debug == False: 
                set_logger = False

            if set_logger == True:

                # log = ProjectBase.logging.logger.MultiprocessLogger.getLogger(
                #     name = log_item,
                #     queue = ProjectBase.logging.multiprocessing_queue,
                #     level = level
                #     )

                log_name = log_item

                log_level = level

                if hasattr(logObjs, log_item) == True:
                    log_attr = getattr(logObjs, log_item)
                    # if hasattr(log_attr, "name") == True and getattr(log_attr, "name") is not None:
                    #     log_name = getattr(log_attr, "name")
                    # if hasattr(log_attr, "level") == True and getattr(log_attr, "level") != loglevel.NOTSET:
                    #     log_level = getattr(log_attr, "level")

                    # if hasattr(log_attr, "file_handler_enable") == True and getattr(log_attr, "file_handler_enable") is not None:
                    #     kwargs['file_handler_enable'] = getattr(log_attr, "file_handler_enable")

                elif hasattr(defaultLoggers, log_item) == True:
                    log_attr = getattr(defaultLoggers, log_item)

                if hasattr(log_attr, "name") == True and getattr(log_attr, "name") is not None:
                    log_name = getattr(log_attr, "name")
                    
                if hasattr(log_attr, "level") == True and getattr(log_attr, "level") != loglevel.NOTSET:
                    log_level = getattr(log_attr, "level")

                handler_config_kwargs = {}
                
                for handle_config_param in inspect.getfullargspec(HandlerConfig).args:
                    
                    if handle_config_param != 'self':
                        
                        if hasattr(log_attr, handle_config_param) == True and getattr(log_attr, handle_config_param) is not None:
                            handler_config_kwargs[handle_config_param] = getattr(log_attr, handle_config_param)

                logger = MultiprocessLogger.setLogger(
                    name = log_name,
                    # listener = ProjectBase.logging.multiprocessing_queue_listener,
                    # queue = ProjectBase.logging.multiprocessing_queue,
                    level = log_level,
                    handler_config_kwargs = handler_config_kwargs,
                    clear = False if log_item.lower() == "ProjectBase".lower() else True
                )

                if not hasattr(logging.getLoggerClass(), 'getChildLogger'):
                    setattr(logging.getLoggerClass(), 'getChildLogger', self.__get_child_logger_wrapper())

                setattr(logging.getLoggerClass(), 'getChild', self.__get_child_wrapper())

                child_loggers = [attr for attr in vars(log_attr) if Logger in get_all_subclasses(getattr(log_attr, str(attr)))]

                if len(child_loggers) > 0:

                    self.log.trace("'%s' child loggers: %s" % (
                        str(log_name),
                        str(', '.join(child_loggers))
                    ))

                for child_logger_name in child_loggers:

                    logger = self.__set_child_logger(
                        base_logger = logger,
                        child_log_attr = getattr(log_attr, str(child_logger_name)),
                    )

                subclasses = ProjectBase.__subclasses__()

                for subclass in subclasses:
                    setattr(subclass.log, str(log_item), logger)

                setattr(ProjectBase.log, log_item, logger)

                self.log.trace("Set '%s' logger" % (str(log_name)))

    def __set_child_logger(self, base_logger: Logger, child_log_attr) -> Logger:

        child_log_name = child_log_attr.__name__

        child_log_level = base_logger.level

        propagate = False

        if hasattr(child_log_attr, "name") == True and getattr(child_log_attr, "name") is not None:
            child_log_name = getattr(child_log_attr, "name")
            
        if hasattr(child_log_attr, "level") == True and getattr(child_log_attr, "level") != loglevel.NOTSET:
            child_log_level = getattr(child_log_attr, "level")
            
        if hasattr(child_log_attr, "propagate") == True and isinstance(getattr(child_log_attr, "propagate"), bool):
            propagate = getattr(child_log_attr, "propagate")

        handler_config_kwargs = {}
        
        for handle_config_param in inspect.getfullargspec(HandlerConfig).args:
            
            if handle_config_param != 'self':
                
                if hasattr(child_log_attr, handle_config_param) == True and getattr(child_log_attr, handle_config_param) is not None:
                    handler_config_kwargs[handle_config_param] = getattr(child_log_attr, handle_config_param)

        child_logger = base_logger.getChildLogger(
            suffix_name = child_log_name,
            level = child_log_level,
            propagate = propagate,
            **handler_config_kwargs
        )

        child_loggers = [attr for attr in vars(child_log_attr) if Logger in get_all_subclasses(getattr(child_log_attr, str(attr)))]

        if len(child_loggers) > 0:

            self.log.trace("'%s' child loggers: %s" % (
                str('.'.join((base_logger.name, child_log_name))),
                str(', '.join(child_loggers))
            ))

        for child_logger_name in child_loggers:

            _logger = self.__set_child_logger(
                base_logger = child_logger,
                child_log_attr = getattr(child_log_attr, str(child_logger_name)),
            )

            setattr(child_logger, child_log_attr.__name__, _logger)

        setattr(base_logger, child_log_attr.__name__, child_logger)

        return base_logger