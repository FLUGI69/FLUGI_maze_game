import logging
import inspect

class StreamToLogger(object):

    def __init__(self, logger, log_level=logging.INFO):
        self.logger: logging.Logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf: str):
        
        for line in buf.rstrip().splitlines():
            
            try:
                strLine = line.rstrip().decode("utf-8", "replace")
            except:
                strLine = line.rstrip()
                
            self.logger.log(self.log_level, strLine, stacklevel=2)

    def flush(self):
        pass
