from interfaces import Interfaces
import multiprocessing
from interfaces.init import Init

from datetime import timedelta

class ConfigCallbacks:

    @classmethod
    def worker_process_start_callback(cls,
        file: __file__,
        logging_queue: multiprocessing.Queue
        ):
        
        Interfaces.logging.multiprocessing_queue = logging_queue

        Init.setup_project_base(file = file)

        Interfaces.config.log = Interfaces.log.Dashboard

    @classmethod
    def worker_exit_callback(cls, port: int):

        print("Dashboard worker %s stopped!" % (str(port)))

    @classmethod
    def worker_restarted_callback(cls, port: int):

        print("Dashboard worker %s restarted!" % (str(port)))