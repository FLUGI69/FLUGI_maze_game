import sys, os
import traceback
import threading
import multiprocessing
from logging import handlers
from typing import Union, Literal, Callable, TYPE_CHECKING
import psutil
from multiprocessing import current_process
import signal
import time

from utils.log.multiprocess_logger.logger_base import getLogger, Logger, loglevel
from utils.log.multiprocess_logger.default_log import defaultLoggers
from utils.log import multiprocess_logger

class classproperty(object):

    def __init__(self, 
        fget, fset = None, 
        fdel = None
        ):
        
        self.fget = fget
        
        self.fset = fset
        
        self.fdel = fdel

    def __get__(self, obj, klass = None):
        
        if klass is None:
            klass = type(obj)

        if isinstance(self.fget, classmethod):
            return self.fget.__get__(obj, klass)()
        
        return self.fget(klass)

    def __set__(self, obj, value):
        
        if not self.fset:
            raise AttributeError("can't set attribute")
        
        type_ = type(obj)
        
        return self.fset.__get__(obj, type_)(value)

    def __delete__(self, obj):
        
        if not self.fdel:
            raise AttributeError("can't delete attribute")
        
        self.fdel.__get__(None, type(obj))()

    def setter(self, func):
        
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
            
        self.fset = func
        
        return self

    def deleter(self, func):
        
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
            
        self.fdel = func
        
        return self

class ProjectBase(object):
    
    if TYPE_CHECKING:
        from utils.time import Time as _Time
        Time: _Time
    
    __file__: str = None
    
    rootPath: str = None

    currentDir: str = None
    
    filePath: str = None

    homePath: str = None

    lock: threading.Lock = threading.Lock()
    
    isRunning = True
    forceExit = False
    exit_sleep: int = 0
    exit_question = True
    before_exit_callback: Callable[[], None] = None
    exit_callback: Callable[[], None] = None
    
    pid: int = None
    
    process: psutil.Process = None

    stderr_bak = None
    exit_bak = None
    quit_bak = None

    debug: bool = True

    class logging:
        
        logger: multiprocess_logger = None

        multiprocessing_queue: multiprocessing.Queue = None
        multiprocessing_queue_listener: handlers.QueueListener = None

        class base(Logger): pass
    
    class log(defaultLoggers): pass
    
    def exit(msg: int | str | bool | None = None, is_error: bool = False,
        error_notify: bool = False, handler: bool = False, internal: bool = True, 
        sigterm: bool = False, 
        **kwargs
        ):
        
        try:

            if ProjectBase.isRunning == True and internal == False and sigterm == False:

                answer = input("Are you sure you want to exit? (Y/N) ").strip().lower()

            else:
                
                answer = 'yes'

            only_y = True
            for let in answer:
                if let != 'y':
                    only_y = False

            if 'yes' in str(answer).lower() or only_y == True:

                if ProjectBase.isRunning == True:
                    
                    if ProjectBase.before_exit_callback is not None and callable(ProjectBase.before_exit_callback):
                        ProjectBase.before_exit_callback()


                if ProjectBase.isRunning == True:
                    
                    ProjectBase.lock.acquire()
                    ProjectBase.isRunning = False
                    ProjectBase.lock.release()

                    if sigterm == True:
                        ProjectBase.log.sigint.warning("Terminated by SIGTERM.")


                elif ProjectBase.forceExit == False:
                    
                    ProjectBase.lock.acquire()
                    ProjectBase.forceExit = True
                    ProjectBase.lock.release()

                    ProjectBase.log.sigint.warning("Force Exit")

                    if internal == False:

                        try:
                            
                            ProjectBase.log.sigint.debug("Kill pid: %s" % str(ProjectBase.pid))
                            os.kill(ProjectBase.pid, signal.SIGTERM)
                            
                        except:
                            pass
                        
                    else:

                        ProjectBase.exit_bak(0)
                else:
                    ProjectBase.exit_bak(0)
                
                if handler == True:

                    ProjectBase.log.sigint.warning("Handler Exit")

                else:

                    if msg is None or msg == "" or msg == True:

                        ProjectBase.log.sigint.warning("Exit")

                    elif msg == False:

                        pass

                    else:
                        
                        if is_error == True:
                            
                            if error_notify == True:
                                ProjectBase.log.sigint.log(loglevel.ERROR_NOTIFY, "%s" % (str(msg)), stacklevel = 2)
                                # ProjectBase.log.sigint.error_notify("%s" % (str(msg)))
                                
                            else:
                                # ProjectBase.log.sigint.error("%s" % (str(msg)))
                                ProjectBase.log.sigint.log(loglevel.ERROR, "%s" % (str(msg)), stacklevel = 2)
                                
                        else:
                            # ProjectBase.log.sigint.warning("%s" % (str(msg)))
                            ProjectBase.log.sigint.log(loglevel.WARNING, "%s" % (str(msg)), stacklevel = 2)


                if ProjectBase.exit_sleep > 0:
                    # ProjectBase.log.sigint.warning("Wait %s sec before exit..." % (str(ProjectBase.exit_sleep)))
                    time.sleep(ProjectBase.exit_sleep)

                if ProjectBase.exit_callback is not None and callable(ProjectBase.exit_callback):
                    ProjectBase.exit_callback()

                try:
                    
                    if ProjectBase.logging.multiprocessing_queue_listener is not None:
                        ProjectBase.logging.multiprocessing_queue_listener.stop()
               
                except Exception as err:
                    ProjectBase.log.sigint.error(traceback.format_exc())
                
                if multiprocessing.current_process().name == 'MainProcess':

                    # ProjectBase.log.sigint.debug("Kill pid: %s" % str(ProjectBase.pid))

                    ProjectBase.logging.multiprocessing_queue.close()
                    ProjectBase.logging.multiprocessing_queue.join_thread()

                    # try:
                    #     os.kill(ProjectBase.pid, signal.SIGTERM)
                    # except:
                    #     pass

                    ProjectBase.exit_bak(0)

        except Exception as err:
            ProjectBase.stderr_bak(traceback.format_exc(), file = sys.stderr)

    @classproperty
    def is_main_process(cls) -> bool:

        return True if current_process().name == 'MainProcess' else False

    @classmethod
    def sigint_handler(cls, _signal, frame):

        if cls.exit_question == True:
            internal = False
            
        else:
            internal = True

        cls.exit(handler = True, internal = internal)

    @classmethod
    def traceback(cls, err = None, limit = None):

        traceback_err = traceback.format_exc(limit)

        cls.log.traceback.error(traceback_err)

        if err is not None:
            cls.log.stderr.error(err)
            
    @classmethod
    def getLogger(cls, name: str | None = None) -> Logger:

        return getLogger(name)