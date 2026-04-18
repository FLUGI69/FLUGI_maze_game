from .logger_base import Logger
from .logger_base import loglevel

class defaultLoggers:

    class ProjectBase(Logger): pass
    
    class Interfaces(Logger): pass
    
    class paramiko(Logger):
        level = loglevel.WARNING
        
    class urllib3(Logger):
        level = loglevel.ERROR
        
    class stdout(Logger): 
        level = loglevel.TRACE

    class werkzeug(Logger):
        level = loglevel.ERROR
    
    class stderr(Logger): pass
    
    class sigint(Logger): pass
    
    class traceback(Logger): pass
    
    class PyWarnings(Logger):
        level = loglevel.WARNING