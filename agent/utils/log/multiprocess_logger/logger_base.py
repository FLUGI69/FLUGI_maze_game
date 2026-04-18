import logging
from .logging_levels import loglevel
from multiprocessing import Queue
import inspect
from .handlers.queue_listener import HandlerConfig
from abc import abstractmethod
import warnings

warnings_captured = False

class Logger(logging.Logger):

    level = logging.NOTSET

    name: str

    file_handler_enable: bool
    file_handler_level: loglevel

    console_handler_enable: bool
    console_handler_level: loglevel

    unique_file_handler_enabled: bool
    unique_file_handler_log_file: str
    unique_file_handler_level: loglevel
    unique_file_handler_format: str
    unique_file_handler_rotation_enable: bool
    unique_file_handler_rotation_size_mb: int
    unique_file_handler_rotation_backup_count: int
    unique_file_handler_clear_old_logs: bool
    unique_file_handler_max_retained_logs: int

    @classmethod
    def basic_setup(cls, 
        level: loglevel = loglevel.DEBUG,
        format: str = "%(asctime)s %(process)d %(processName)s %(threadName)s %(levelname)s %(name)s %(module)s.%(funcName)s:%(lineno)d # %(message)s",
        filename: str | None = None
        ):
        
        loglevel.setup()

        handlers = []

        if filename is not None:
            
            file_handler = logging.FileHandler(
                filename, 'a', 
                encoding='utf-8',
                errors = 'backslashreplace'
            )
            
            handlers.append(file_handler)

        stream_handler = logging.StreamHandler()
        handlers.append(stream_handler)

        logging.basicConfig(
            format = format,
            level = level,
            handlers = handlers
        )

    @abstractmethod
    def trace(self, msg, *args, **kwargs): pass

    @abstractmethod
    def success(self, msg, *args, **kwargs): pass

    @abstractmethod
    def error_notify(self, msg, *args, **kwargs): pass

    @classmethod
    def getChildLogger(
        self,
        suffix_name: str,
        level: loglevel = None,
        propagate: bool = False,

        file_handler_enable: bool = None,
        file_handler_level: bool = None,

        console_handler_enable: bool = None,
        console_handler_level: loglevel = None,

        unique_file_handler_enabled: bool = None,
        unique_file_handler_log_file: str = None,
        unique_file_handler_format: str = None,
        unique_file_handler_level: loglevel = None,

        unique_file_handler_rotation_enable: bool = None,
        unique_file_handler_rotation_size_mb: int = None,
        unique_file_handler_rotation_backup_count: int = None,
        unique_file_handler_clear_old_logs: bool = None,
        unique_file_handler_max_retained_logs: int = None,

        **kwargs
        ) -> 'Logger': pass

    @classmethod
    def getLogger(cls, name: str | None = None) -> 'Logger':
        return logging.getLogger(name)
    
    def getChild(self, suffix_name: str) -> 'Logger': pass

    @classmethod
    def captureWarnings(cls, capture: bool):
        
        warnings.simplefilter('always')
        global warnings_captured
        
        if capture == True:
            
            if warnings_captured == False:
                
                warnings.showwarning = cls.__showwarning
                warnings_captured = True
                
        else:
            warnings_captured = False

    @classmethod
    def __showwarning(cls, message, category, filename, lineno, file = None, line = None):
        
        s = warnings.formatwarning(message, category, filename, lineno, line)
        
        logger = Logger.getLogger("PyWarnings")
        logger.log(level=logging.ERROR, msg = str(s), stacklevel = 1)

def getLogger(name: str | None = None) -> Logger:
    return Logger.getLogger(name)

logging.captureWarnings = Logger.captureWarnings
