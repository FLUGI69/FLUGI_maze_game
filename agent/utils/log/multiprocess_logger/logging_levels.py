import logging
from enum import IntEnum

class loglevel:
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    SUCCESS = 25
    ERROR_NOTIFY = 41
    TRACE =  1

    @classmethod
    def setup(cls):

        for name, level in vars(loglevel).items():

            if not hasattr(logging, name):

                if not name.startswith('__'):
                    cls.add_logging_level(name.upper(), level)

    @classmethod
    def is_exist_level(cls, level: int) -> dict:
        return True if level in logging._levelToName.keys() else False

    @classmethod
    def get_log_levels(cls) -> dict:
        levels = {}
        for level, name in sorted(logging._levelToName.items()):
            levels[str(name)] = level
        return levels

    @classmethod
    def add_logging_level(cls, levelName, levelNum, methodName=None):

        if not methodName:
            methodName = levelName.lower()

        if not hasattr(logging, levelName):
            
            logging.addLevelName(levelNum, levelName)
            setattr(logging, levelName, levelNum)

        if not hasattr(logging.getLoggerClass(), methodName):
            
            def logForLevel(self, message, *args, **kwargs):
                
                if self.isEnabledFor(levelNum):
                    self._log(levelNum, message, args, **kwargs)
                    
            logForLevel.__name__ = methodName
            
            setattr(logging.getLoggerClass(), methodName, logForLevel)

        if not hasattr(logging, methodName):
            
            def logToRoot(message, *args, **kwargs):
                logging.log(levelNum, message, *args, **kwargs)
                
            logToRoot.__name__ = methodName
            
            setattr(logging, methodName, logToRoot)
