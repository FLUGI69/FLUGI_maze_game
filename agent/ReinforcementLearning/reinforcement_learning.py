import json
import random
import traceback
import subprocess
from collections import deque
from threading import Thread
from pathlib import Path
from subprocess import PIPE

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch._C import _CudaDeviceProperties

from utils.dc.game_state import GameState
from utils.dc.agent_stats import EpisodeResult
from MazeAgent import MazeAgentConfig
from SupervisedLearning.cnn_module import PolicyCNN
from .dqn_module import DQNNetwork
from .replay_buffer import ReplayBuffer


class ReinforcementLearning:

    def __init__(self, config: MazeAgentConfig):

        self.__agent_running = False

        self.config = config
        
        self.log = config.logger
        
        self.channel = config.dqn_channels

        self.__setup()
        
    @property
    def agent_running(self) -> bool:
        return self.__agent_running

    def __setup(self) -> None:

        self.__file__ = __file__

        Path("models").mkdir(exist_ok = True)

        self._log_device_info()
        self._load_models()

        self._replay = ReplayBuffer(self.config.dqn_buffer_capacity)
        self._epsilon = self.config.dqn_epsilon_start
        self._total_steps = 0

    def _log_device_info(self) -> None:

        if torch.cuda.is_available():

            self._device = torch.device("cuda")

            device_properties: _CudaDeviceProperties = torch.cuda.get_device_properties(0)

            compute_capability = (device_properties.major, device_properties.minor)
            sm_count = device_properties.multi_processor_count
            c_per_sm = (self.config.cores_per_sm or {}).get(compute_capability, 64)
            cuda_cores = sm_count * c_per_sm
            vram_mb = device_properties.total_memory / (1024 ** 2)
            vram_gb = device_properties.total_memory / (1024 ** 3)

            self.log.info("=" * 50)
            self.log.info("CUDA ENABLED -> running on GPU")
            self.log.info("Device     : %s" % device_properties.name)
            self.log.info("Compute    : %d.%d" % (device_properties.major, device_properties.minor))
            self.log.info("SMs        : %d" % sm_count)
            self.log.info("CUDA cores : ~%d  (%d cores / SM)" % (cuda_cores, c_per_sm))
            self.log.info("VRAM       : %.0f MB  (%.1f GB)" % (vram_mb, vram_gb))
            self.log.info("=" * 50)

        else:

            self._device = torch.device("cpu")

            self.log.info("=" * 50)
            self.log.info("CUDA not available -> running on CPU")
            self.log.info("=" * 50)



    def __start(self) -> None:

        try:

            self.log.info("ReinforcementLearning (DQN) started")

            exe = self.config.exe_name
            args = ([str(exe), "--ai"] if self.config.headless
                else [str(exe), "--ai", "--render"])

            process = subprocess.Popen(
                args, 
                stdin = PIPE, 
                stdout = PIPE, 
                bufsize = 1,
                text = True
            )

  
            self.log.info("=" * 50)
            self.log.info("ReinforcementLearning SUMMARY")
            self.log.info("=" * 50)
            self.log.info("Total mazes        : %d" % maze_count)
            self.log.info("   Won             : %d  (%.1f%%)" % (total_won, win_rate))
            self.log.info("   Died            : %d" % total_died)
            self.log.info("   Timeout         : %d" % total_timeout)
            cnn_skip_total = cnn_correct_skips + cnn_wrong_skips
            cnn_accuracy = cnn_correct_skips / cnn_skip_total * 100 if cnn_skip_total > 0 else 0.0
            self.log.info("  Skipped          : %d  (correct=%d wrong=%d acc=%.1f%%)" % (
                total_skipped, 
                cnn_correct_skips, 
                cnn_wrong_skips, 
                cnn_accuracy
            ))
            self.log.info("Epsilon            : %.4f" % self._epsilon)
            self.log.info("Total steps        : %d" % self._total_steps)
            self.log.info("Replay buffer      : %d transitions" % len(self._replay))
            self.log.info("=" * 50)


        except OSError:
            pass

        except Exception:
            self.log.error(traceback.format_exc())

        finally:
            self.__agent_running = False
            self.log.info("ReinforcementLearning Thread stopped!")

    def _start_bot(self):

        self.log.info("Run ReinforcementLearning Thread!")

        self.thread = Thread(name = "DQNThread", target=self.__start, daemon = True)

        self.__agent_running = True

        self.thread.start()

    def run(self, **kwargs) -> None:

        self._start_bot()

        try:
            
            while self.thread.is_alive():
                self.thread.join(timeout = 1)
                
        except KeyboardInterrupt:
            pass
