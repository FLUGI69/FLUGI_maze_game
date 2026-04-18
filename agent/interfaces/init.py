import os
import subprocess
import json
import signal
import threading
import multiprocessing
from datetime import datetime

from ProjectBase import Setup
from .interfaces import Interfaces
from .callbacks import Callbacks

class Init:
    
    @classmethod
    def setup_project_base(cls, 
        file: __file__,
        ):
        
        os.environ["PYTHONWARNINGS"] = "ignore"
        
        try:

            if Interfaces.is_main_process == True:
 
                cls.__setup_main_SIGINT()

            log_src_path = " %(module)s.%(funcName)s:%(lineno)d"

            Setup(
                import_file = file,
                debug = True,
                timezone = Interfaces.config.time.timezone,
                timeFormat = Interfaces.config.time.timeformat,
                exitSleep = 1 if Interfaces.is_main_process == True else 0,
                beforeExitCallback = Callbacks.main_process_before_exit if Interfaces.is_main_process == True else None,
                exitCallback = Callbacks.main_process_exit if Interfaces.is_main_process == True else Callbacks.sub_process_exit,
                sigintHandler = False,

                log_names = Interfaces.log,

                level = Interfaces.config.log.level,

                file_handler_enable = True,
                file_handler_log_dir = "log",
                file_handler_log_file = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.now()),
                file_handler_rotation_enable = True,
                file_handler_rotation_size_mb = 10,
                file_handler_rotation_backup_count = 10,
                file_handler_format = "%(asctime)s %(process)d %(processName)s %(threadName)s %(levelname)s %(name)s" + (log_src_path if Interfaces.debug == True else "") + " # %(message)s",
                file_handler_level = Interfaces.config.log.level,

                console_handler_enable = True,
                console_handler_format = "%(asctime)s %(process)d %(processName)s %(threadName)s %(levelname)s %(name)s" + log_src_path + " # %(message)s",
                console_handler_level = Interfaces.config.log.level,
                console_handler_color = True,

                clear_old_logs = True,
                max_retained_logs = 10
            )

        except Exception as err:
            
            Interfaces.traceback()
            Interfaces.exit()
            
    @classmethod
    def setup_modules(cls):

        import sys

        from pathlib import Path
        
        from utils.agent import Agent
        
        from MazeAgent import MazeAgentConfig

        from utils.lifespan import before_startup, after_startup, after_shutdown, before_shutdown
        
        from utils.config_callbacks import ConfigCallbacks
        
        from utils.dc.agent_stats import AgentStats

        from utils.web import Web
        
        from Dashboard import DashboardConfig

        stats = AgentStats(
            max_render_points = Interfaces.config.dashboard.max_render_points
        )

        if Interfaces.config.dashboard.enabled == True:

            Interfaces.Web = Web(DashboardConfig(
                
                logger = Interfaces.log.Dashboard,
                
                host = Interfaces.config.dashboard.host,
                port = Interfaces.config.dashboard.port,
                
                update_ms = Interfaces.config.dashboard.update_ms,
                
                before_startup_callback = before_startup,
                after_startup_callback = after_startup,
                before_shutdown_callback = before_shutdown,
                after_shutdown_callback = after_shutdown,
                
                worker_process_start_callback = ConfigCallbacks.worker_process_start_callback,
                
                worker_process_start_kwargs = {
                    'file': Interfaces.__file__,
                    'logging_queue': Interfaces.logging.multiprocessing_queue,
                },
                
                worker_exit_callback = ConfigCallbacks.worker_exit_callback,
                
                worker_restarted_callback = ConfigCallbacks.worker_restarted_callback,
                
                agent_stats = stats,
            ))

        maze_cfg = MazeAgentConfig(
            
            logger = Interfaces.log.Dashboard.MazeAgent,
            
            exe_name = str(Path(Interfaces.rootPath) / Interfaces.config.agent.exe_name),
            max_mazes = Interfaces.config.agent.max_mazes,
            max_steps = Interfaces.config.agent.max_steps,
            headless = Interfaces.config.agent.headless,
            
            agent_stats = stats,
            
            process_manager = Interfaces.Web.process_manager if Interfaces.config.dashboard.enabled == True else None,
            
            cnn_channels = Interfaces.config.supervised_learning.channels,
            cnn_max_samples = Interfaces.config.supervised_learning.max_samples,
            cnn_data_file = Interfaces.config.supervised_learning.data_file,
            cnn_model_file = Interfaces.config.supervised_learning.model_file,
            cnn_train_every = Interfaces.config.supervised_learning.train_every,
            cnn_min_samples = Interfaces.config.supervised_learning.min_samples,
            cnn_batch_size = Interfaces.config.supervised_learning.batch_size,
            cnn_cores_per_sm = Interfaces.config.supervised_learning.cores_per_sm,
            
            dqn_actions = Interfaces.config.reinforcement_learning.actions,
            dqn_file = Interfaces.config.reinforcement_learning.file,
        )

        Interfaces.Agent = Agent(maze_cfg)

        if Interfaces.config.dashboard.enabled == True:

            Interfaces.Web.process_manager.agent = Interfaces.Agent

    @classmethod
    def __setup_main_SIGINT(cls):

        def main_signal_handler(signum, frame):

            Interfaces.exit(handler = True, sigterm = True if signum == signal.SIGTERM else False)

        signal.signal(signal.SIGINT, main_signal_handler)
        signal.signal(signal.SIGTERM, main_signal_handler)   
