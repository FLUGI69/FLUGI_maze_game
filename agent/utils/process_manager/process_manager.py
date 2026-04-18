import logging
import traceback
import typing as t
import subprocess
from time import sleep

from .process_manager_vars import ProcessManagerVars
from .worker import Worker

if t.TYPE_CHECKING:
    from Dashboard import Dashboard
    from utils.agent import Agent

class ProcessManager:

    def __init__(self, 
        parent: 'Dashboard',
        agent: 'Agent',
        ) -> None:

        self.dashboard = parent
        
        self.agent = agent

        self.log = self.dashboard.config.logger.getChild('ProcessManager')

        self.process_manager_vars = ProcessManagerVars()
        
        self.workers: dict[str, Worker] = {}

    def __setup_workers(self) -> bool:

        self.log.info("Start workers")

        try:

            self.dashboard._start_dashboard()

            self.workers['Dashboard'] = Worker(name = 'Dashboard', running = True, started = True)

            self.log.debug("Dashboard worker started")

        except Exception:

            error = traceback.format_exc()
            
            self.log.error(error)
            
            self.workers['Dashboard'] = Worker(name = 'Dashboard', setup_error = error)

            return False

        try:

            self.agent._start_bot()

            self.workers['Agent'] = Worker(name = 'Agent', running = True, started = True)

            self.log.debug("Agent worker started")

        except Exception:

            error = traceback.format_exc()
            
            self.log.error(error)
            
            self.workers['Agent'] = Worker(name = 'Agent', setup_error = error)

            return False

        return True

    def __worker_loop(self):

        while True:

            try:

                should_exit = False

                with self.process_manager_vars.lock:

                    if self.process_manager_vars.should_exit == True:
                        should_exit = True

                if should_exit == True:
                    break

                sleep(1)

            except KeyboardInterrupt:
                pass

            except Exception:

                self.log.error(traceback.format_exc())

    def stop(self) -> None:

        with self.process_manager_vars.lock:
            self.process_manager_vars.should_exit = True

    def start_main_process_loop(self) -> None:

        if self.__setup_workers() == False:
            return

        self.__worker_loop()

        self.log.info("ProcessManager terminated!")