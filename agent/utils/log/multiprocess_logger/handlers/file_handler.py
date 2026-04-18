import logging
from logging.handlers import RotatingFileHandler, WatchedFileHandler
import os
import multiprocessing
import re

class CreateFileHandler:
    
    def __init__(self, 
                filename : str, 
                mode: str = 'a',
                rotation_enable = False, 
                rotation_maxBytes = 0, 
                rotation_backupCount = 0, 
                encoding: str | None = 'utf-8',
                delay: bool = False,
                errors: str | None = None,
                clear_old_logs: bool = True,
                max_retained_logs: int | None = 100,
                unique_file_handler_name: str = None
                ):

        self.__filename = filename
        self.__log_dir = os.path.dirname(self.__filename)
        self.__clear_old_logs = clear_old_logs
        self.__max_retained_logs = max_retained_logs

        self.__create_log_dir()

        self.__clean_logs()

        if rotation_enable == True:

            self.handler = RotatingFileHandler(
                filename = self.__filename, 
                mode = mode,
                maxBytes = rotation_maxBytes, 
                backupCount = rotation_backupCount, 
                encoding = encoding,
                delay = delay,
                errors = errors
            )
            
        else:

            self.handler = WatchedFileHandler(
                filename = self.__filename, 
                mode = mode, 
                encoding = encoding, 
                delay = delay,
                errors = errors
                )
            
        if isinstance(unique_file_handler_name, str):

            self.handler.name = unique_file_handler_name

            self.handler.unique_file_handler = True
            
    def get_handler(self):

        return self.handler

    def __create_log_dir(self) -> None:

        try:
            os.makedirs(os.path.join(os.getcwd(), self.__log_dir))
        except OSError:
            pass
            
    def __clean_logs(self):

        if multiprocessing.current_process().name == 'MainProcess':

            if os.path.exists(self.__log_dir):
                
                if self.__clear_old_logs == True and isinstance(self.__max_retained_logs, int):

                    kept_logs = []

                    files = os.listdir(self.__log_dir)
                    logfiles = [os.path.join(self.__log_dir, file) for file in files if re.search(r"\.log(\.\d+)?$", file)]

                    sorted_logfiles = reversed(list(sorted(logfiles, key=os.path.getmtime)))
                    for i, logfile in enumerate(sorted_logfiles):
                        if i == self.__max_retained_logs - 2:
                            break
                        kept_logs.append(logfile)
                    
                    removable_logs = list(set(sorted_logfiles) - set(kept_logs))

                    for rem_log in removable_logs:
                        os.remove(rem_log)
