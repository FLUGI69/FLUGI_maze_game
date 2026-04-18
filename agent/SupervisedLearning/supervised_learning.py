import os, sys
import traceback
import subprocess
import pickle
from collections import deque
from threading import Thread
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch._C import _CudaDeviceProperties
from torch.utils.data import DataLoader, TensorDataset
from utils.process_manager import ProcessManager

from utils.dc.game_state import GameState
from utils.dc.agent_stats import EpisodeResult
from MazeAgent import MazeAgentConfig
from .cnn_module import PolicyCNN

class SupervisedLearning:

    def __init__(self, config: MazeAgentConfig):

        self.__agent_running = False

        self.config = config
        
        self.process_manager = config.process_manager
        
        self.subprocess: subprocess.Popen | None = None
        
        self.log = config.logger
        
        self.stats = self.config.agent_stats
        
        self.channel = config.cnn_channels
        
        self.data_file = config.cnn_data_file
        
        self.model_file = config.cnn_model_file
        
        self.train_every = config.cnn_train_every
        
        self.max_samples = self.config.cnn_max_samples
        self.min_samples = config.cnn_min_samples
        
        self.batch_size = config.cnn_batch_size

        self.__setup()
        
    @property
    def agent_running(self) -> bool:
        return self.__agent_running
    
    @agent_running.setter
    def agent_running(self, value: bool):
        self.__agent_running = value

    def __setup(self) -> None:

        self.__file__ = __file__
        
        self.game_state = GameState()

        Path("models").mkdir(exist_ok = True)

        self._samples_X: list[np.ndarray] = []
        self._samples_y: list[int] = []

        self._log_device_info()
        self._load_data()
        self._load_model()

    def _log_device_info(self) -> None:
        
        if torch.cuda.is_available() == True:
            
            self._device = torch.device("cuda")
            
            prop_device: _CudaDeviceProperties = torch.cuda.get_device_properties(0)

            cc = (prop_device.major, prop_device.minor)
            sm_count = prop_device.multi_processor_count
            c_per_sm = self.config.cnn_cores_per_sm.get(cc, 64)
            cuda_cores = sm_count * c_per_sm
            vram_mb = prop_device.total_memory / (1024 ** 2)
            vram_gb = prop_device.total_memory / (1024 ** 3)

            self.log.info("=" * 50)
            self.log.info("CUDA ENABLED -> running on GPU")
            self.log.info("Device     : %s" % prop_device.name)
            self.log.info("Compute    : %d.%d" % (prop_device.major, prop_device.minor))
            self.log.info("SMs        : %d" % sm_count)
            self.log.info("CUDA cores : ~%d  (%d cores / SM)" % (cuda_cores, c_per_sm))
            self.log.info("VRAM       : %.0f MB  (%.1f GB)" % (vram_mb, vram_gb))
            self.log.info("=" * 50)
        
        else:
           
            self._device = torch.device("cpu")
            
            self.log.info("=" * 50)
            self.log.info("CUDA not available -> running on CPU")
            self.log.info("=" * 50)

    def _load_data(self) -> None:
        
        if Path(self.data_file).exists() == True:
            
            try:
                
                with open(self.data_file, "rb") as fh:
                    saved = pickle.load(fh)
                    
                self._samples_X = saved.get("X", [])
                self._samples_y = saved.get("y", [])
                
                self.log.debug("Loaded %d training samples from %s" % (len(self._samples_y), self.data_file))
            
            except Exception:
                self.log.warning("Could not load training data - starting fresh:\n" + traceback.format_exc())

    def _save_data(self) -> None:
        
        try:
            
            tmp_file = self.data_file + ".tmp"
            
            with open(tmp_file, "wb") as fh:
                pickle.dump({"X": self._samples_X, "y": self._samples_y}, fh)
                
            os.replace(tmp_file, self.data_file)
       
        except Exception:
            self.log.warning("Could not save training data:\n" + traceback.format_exc())

    def _load_model(self) -> None:
        
        self._model = PolicyCNN(channels = self.channel).to(self._device)
        self._optimizer = optim.Adam(self._model.parameters(), lr = 1e-3)
        self._criterion = nn.CrossEntropyLoss()
        
        if Path(self.model_file).exists() == True:
            
            try:
                
                self._model.load_state_dict(
                    torch.load(
                        self.model_file, 
                        map_location = self._device, 
                        weights_only = True
                    )
                )
                
                self.log.info("Loaded CNN model from %s" % self.model_file)
                
            except Exception:
                self.log.warning("Could not load model - starting fresh:\n" + traceback.format_exc())

    def _save_model(self) -> None:
        
        try:
            
            torch.save(self._model.state_dict(), self.model_file)
      
        except Exception:
            self.log.warning("Could not save model:\n" + traceback.format_exc())

    def _encode_state(self, state: GameState) -> np.ndarray:

        h, w = state.height, state.width
        x = np.zeros((self.channel, h, w), dtype = np.float32)

        for y in range(h):
            
            for xx in range(w):
                
                if state.grid[y][xx] != 0:
                    x[0, y, xx] = 1.0

        x[1, state.py, state.px] = 1.0

        for cx, cy in state.active_coins:
            x[2, cy, cx] = 1.0

        for sx, sy in state.active_shields:
            x[3, sy, sx] = 1.0

        for tx, ty in state.active_traps:
            x[4, ty, tx] = 1.0

        x[5, state.exit_y, state.exit_x] = 1.0

        return x

    def _bfs(self, start, goals, grid, width, height):

        queue = deque([(start, [])])
        visited = {start}

        while queue:

            (x, y), path = queue.popleft()

            if (x, y) in goals:
                return path

            for a, (dx, dy) in (
                (0, (0, -1)),
                (1, (0, 1)),
                (2, (-1, 0)),
                (3, (1, 0))):
                
                nx, ny = x + dx, y + dy

                if not (0 <= nx < width and 0 <= ny < height):
                    continue

                if grid[ny][nx] == 0:
                    continue

                if (nx, ny) in visited:
                    continue

                visited.add((nx, ny))
                queue.append(((nx, ny), path + [a]))

        return None

    def _expert_action(self, state: GameState) -> int:

        start = (state.px, state.py)

        if state.active_coins:

            path = self._bfs(
                start,
                set(state.active_coins),
                state.grid,
                state.width,
                state.height,
            )
           
            if path:
                return path[0]
            
        if state.exit_open:

            path = self._bfs(
                start,
                {(state.exit_x, state.exit_y)},
                state.grid,
                state.width,
                state.height,
            )
       
            if path:
                return path[0]

        return np.random.randint(0, 4)

    def _train(self) -> None:

        n = len(self._samples_y)

        if n < self.min_samples:
            self.log.info("Not enough samples (%d/%d)" % (n, self.min_samples))
            return

        X = torch.tensor(np.stack(self._samples_X), dtype = torch.float32)
        y = torch.tensor(self._samples_y, dtype = torch.long)

        loader = DataLoader(TensorDataset(X, y), batch_size = self.batch_size, shuffle = True)

        self._model.train()

        total_loss = 0
        correct = 0

        for xb, yb in loader:

            xb: torch.Tensor = xb.to(self._device)
            yb: torch.Tensor = yb.to(self._device)

            self._optimizer.zero_grad()

            logits: torch.Tensor = self._model(xb)
            loss: torch.Tensor = self._criterion(logits, yb)

            loss.backward()
            self._optimizer.step()

            total_loss: float = total_loss + loss.item() * len(yb)
            correct: int = correct + (logits.argmax(1) == yb).sum().item()

        self.log.debug("Training completed: processed %d samples in %d batches, average loss was %.4f (total: %.4f), accuracy reached %.2f%% (%d correct predictions). Model saved to '%s', data file: '%s', device: %s, channels: %d, batch size: %d, min samples: %d, train interval: %d." % (
            n,
            len(loader),
            total_loss / n,
            total_loss,
            100 * correct / n,
            correct,
            self.model_file,
            self.data_file,
            str(self._device),
            self.channel,
            self.batch_size,
            self.min_samples,
            self.train_every
        ))

        self._save_model()

    def __start(self) -> None:

        try:

            self.log.info("SupervisedLearning (CNN) started")

            exe = self.config.exe_name

            args = ([str(exe), "--ai"] if self.config.headless
                else [str(exe), "--ai", "--render"])

            self.subprocess = subprocess.Popen(
                args,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                text = True
            )

            samples_since_train = 0

            maze_count: int = 0
            step_count: int = 0

            ep_hp_start: int = 3
            ep_coins_start: int = 0
            ep_shields: int = 0
            ep_prev_shield: bool = False

            total_won: int = 0
            total_died: int = 0
            total_timeout: int = 0
            total_steps: int = 0
            total_coins: int = 0
            total_coins_possible: int = 0

            while self.agent_running == True:
                
                if self.subprocess.poll() is not None:
                    self.log.warning("Subprocess exited with code %s" % self.subprocess.returncode)
                    break

                line = self.subprocess.stdout.readline()
             
                new_maze = self.game_state.update(line)
                
                if new_maze == True:
                        
                    ep_hp_start = self.game_state.hp
                    ep_coins_start = self.game_state.coins
                    ep_shields = 0
                    ep_prev_shield = self.game_state.shield
            
                game_state = self._encode_state(self.game_state)
                action = self._expert_action(self.game_state)

                self._samples_X.append(game_state)
                self._samples_y.append(action)
                
                if len(self._samples_X) > self.max_samples:
                    self._samples_X = self._samples_X[-self.max_samples:]
                    self._samples_y = self._samples_y[-self.max_samples:]
                             
                samples_since_train += 1
                
                if samples_since_train >= self.train_every:
                    
                    self._save_data()
                    self._train()
                    
                    samples_since_train = 0
                    
                if ep_prev_shield == False and self.game_state.shield:
                    ep_shields += 1
                    
                ep_prev_shield = self.game_state.shield

                game_state: int = self.game_state.game_state

                if game_state == 2:
                    
                    ep_coins = max(0, self.game_state.coins - ep_coins_start)
                    ep_possible = self.game_state.total_coins
                    
                    if self.stats is not None:
                        
                        self.stats.add(EpisodeResult(
                            maze_id = maze_count + 1,
                            won = True,
                            died = False,
                            steps = step_count,
                            coins_collected = ep_coins,
                            coins_possible = ep_possible,
                            hp_lost = max(0, ep_hp_start - self.game_state.hp),
                            shields_picked = ep_shields,
                        ))
                        
                    total_won += 1
                    total_steps += step_count
                    total_coins += ep_coins
                    total_coins_possible += ep_possible
                    
                    maze_count += 1
                    
                    step_count = 0
                    
                    self.log.info("Won maze %d" % maze_count)
                    
                    if maze_count >= self.config.max_mazes:
                        self.log.info("Maximum number of mazes reached: %d out of %d. Stopping training", maze_count, self.config.max_mazes)
                        break
                    
                    self.subprocess.stdin.write("new\n")
                    self.subprocess.stdin.flush()
                    
                    continue

                timed_out: bool = step_count >= self.config.max_steps

                if game_state == 3 or timed_out:
                    
                    ep_coins = max(0, self.game_state.coins - ep_coins_start)
                    ep_possible = self.game_state.total_coins
                    
                    if self.stats is not None:
                        
                        self.stats.add(EpisodeResult(
                            maze_id = maze_count + 1,
                            won = False,
                            died = (game_state == 3),
                            steps = step_count,
                            coins_collected = ep_coins,
                            coins_possible = ep_possible,
                            hp_lost = max(0, ep_hp_start - self.game_state.hp),
                            shields_picked = ep_shields,
                        ))
                        
                    if game_state == 3:
                        total_died += 1
                    else:
                        total_timeout += 1
                        
                    total_steps += step_count
                    total_coins += ep_coins
                    total_coins_possible += ep_possible
                    
                    maze_count += 1
                    
                    step_count = 0
                    
                    if maze_count >= self.config.max_mazes:
                        self.log.info("Maximum number of mazes reached: %d out of %d. Stopping training", maze_count, self.config.max_mazes)
                        break
                    
                    self.subprocess.stdin.write("new\n")
                    self.subprocess.stdin.flush()
                    
                    continue
                
                self.subprocess.stdin.write(self._action_to_str(action) + "\n")
                self.subprocess.stdin.flush()
                
                step_count += 1
                
            self.subprocess.stdin.write("quit\n")
            self.subprocess.stdin.flush()
        
        except OSError:
            pass
        
        except Exception:
            self.log.error(traceback.format_exc())

        finally:
        
            self.__agent_running = False
            
            self.log.info("=" * 50)
            self.log.info("SupervisedLearning SUMMARY")
            self.log.info("=" * 50)
            self.log.info("Total mazes        : %d", maze_count)
            self.log.info("Total samples      : %d", len(self._samples_X))
            
            if self._samples_X:
                
                first_hash = hash(str(self._samples_X[0]))
                last_hash = hash(str(self._samples_X[-1]))
                
                self.log.info("First maze hash    : %s", first_hash)
                self.log.info("Last maze hash     : %s", last_hash)
                
            self.log.info("Model file         : %s", self.model_file)
            self.log.info("Data file          : %s", self.data_file)
            self.log.info("Device             : %s", str(self._device))
            self.log.info("Batch size         : %d", 32)
            self.log.info("Min samples        : %d", self.min_samples)
            self.log.info("Train interval     : %d", self.train_every)
            self.log.info("=" * 50)
            
            self.log.info("SupervisedLearning Thread stopped!")

    def _action_to_str(self, action: int) -> str:
        action_map = {0: "up", 1: "down", 2: "left", 3: "right"}
        return action_map.get(action, "up") 
    
    def _start_bot(self) -> None:

        self.log.info("Run SupervisedLearning Thread!")

        self.thread = Thread(name = "CNNThread", target = self.__start, daemon = True)

        self.__agent_running = True
        
        self.thread.start()

    def run(self) -> None:
        
        self._start_bot()

        try:
            
            while self.thread.is_alive():
                self.thread.join(timeout = 1)
                
        except KeyboardInterrupt:
            pass