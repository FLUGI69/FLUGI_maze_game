import logging
import click
from .logging_levels import loglevel

class AntiColorFormatter(logging.Formatter):
    
    def format(self, record: logging.LogRecord) -> str:
        return click.unstyle(super().format(record))
    
class ConsoleFormatter(logging.Formatter):

        def __init__(self, 
            format: str, 
            color: bool = True
            ):

            if color == True:
                colors = Colors
                
            else:
                colors = NoColors

            format = format

            self.FORMATS = {
                loglevel.TRACE: colors.cyan + format + colors.reset,
                loglevel.DEBUG: colors.blue + format + colors.reset,
                loglevel.INFO: colors.grey + format + colors.reset,
                loglevel.SUCCESS: colors.green + format + colors.reset,
                loglevel.WARNING: colors.yellow + format + colors.reset,
                loglevel.ERROR: colors.red + format + colors.reset,
                loglevel.ERROR_NOTIFY: colors.bold_dark_red + format + colors.reset,
                loglevel.CRITICAL: colors.bold_red + format + colors.reset
            }

        def format(self, record):
            
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            
            return formatter.format(record)
        
class Colors:

    grey = ""
    cyan = "\x1B[96m"
    blue = "\033[94m"
    green = "\x1B[92m"
    yellow = "\x1B[33m"
    dark_red = "\x1B[91m"
    bold_dark_red = "\x1B[91m;1m"
    red = "\x1B[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1B[0m"

class NoColors:
    
    grey = ""
    blue = ""
    cyan = ""
    green = ""
    yellow = ""
    dark_red = ""
    bold_dark_red = ""
    red = ""
    bold_red = ""
    reset = ""
