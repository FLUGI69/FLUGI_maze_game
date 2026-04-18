import json
import traceback
import subprocess
from threading import Thread
from pathlib import Path

import numpy as np
import torch
from torch._C import _CudaDeviceProperties
from utils.dc.agent_stats import EpisodeResult

from utils.dc.game_state import GameState
from MazeAgent import MazeAgentConfig
from SupervisedLearning import PolicyCNN

class TrainedModelPlayer:

    def __init__(self, config: MazeAgentConfig):

        self.__agent_running = False

        self.config = config
        
        self.log = config.logger
        
        self.stats = self.config.agent_stats
        
        self.max_mazes = config.max_mazes
        
        self.channel = config.cnn_channels
        self.cnn_model_file = config.cnn_model_file
        self._cnn_model: PolicyCNN = None

        self.__setup()
    
    @property
    def agent_running(self) -> bool:
        return self.__agent_running

    def __setup(self):

        self.__file__ = __file__
        
        self.game_state = GameState()
        
        self._log_device_info()
        
        if self.config.pretrained_model == True:
            self.__load_policy_model()

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
            
    def __load_policy_model(self) -> None:
        
        self._cnn_model = PolicyCNN(channels = self.channel).to(self._device)
        
        if Path(self.cnn_model_file).exists() == True:
            
            try:
                
                self._cnn_model.load_state_dict(
                    torch.load(
                        self.cnn_model_file, 
                        map_location = self._device, 
                    )
                )
                
                self._cnn_model.eval()
                
                self.log.info("Loaded CNN model from %s" % self.cnn_model_file)
                
            except Exception:
                self.log.warning("Could not load CNN model - starting fresh")
    
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

    def __start(self) -> None:

        try:

            if self.config.pretrained_model == True:
                
                self.log.info("PreTrainedModelPlayer started")
                
                exe = self.config.exe_name

                self.log.info("Starting maze: %s" % str(exe))

                args = [str(exe), "--ai"] if self.config.headless == True \
                    else [str(exe), "--ai", "--render"]
                    
                process = subprocess.Popen(
                    args,
                    stdin = subprocess.PIPE,
                    stdout = subprocess.PIPE,
                    text = True
                )

                maze_count: int = 0
                step_count: int = 0
                first_msg: bool = True

                ep_hp_start: int = 3
                ep_coins_start: int = 0
                ep_shields: int = 0
                ep_prev_shield: bool = False
                ep_init: bool = True # reset on next full JSON

                total_won: int = 0
                total_died: int = 0
                total_timeout: int = 0
                total_steps: int = 0
                total_coins: int = 0
                total_coins_possible: int = 0
                  
                while self.agent_running == True:
                    
                    line = process.stdout.readline()
                    
                    if line == "":
                        break
                    
                    line = line.strip()
                    
                    if first_msg == True or line.startswith("{"):
                        
                        self.game_state.update_full(json.loads(line))
                        
                        first_msg = False
                        
                        if ep_init:
                            
                            ep_hp_start = self.game_state.hp
                            ep_coins_start = self.game_state.coins
                            ep_shields = 0
                            ep_prev_shield = self.game_state.shield
                            ep_init = False
                   
                    else:
                        
                        self.game_state.update_compact(line)
                        
                    if ep_prev_shield == False and self.game_state.shield:
                        ep_shields += 1
                    
                    ep_prev_shield = self.game_state.shield
                        
                    game_state = self._encode_state(self.game_state)
                    
                    with torch.no_grad():
                        
                        inp = torch.tensor(game_state, dtype = torch.float32).unsqueeze(0).to(self._device)
                        logits = self._cnn_model(inp)
                        
                        action = int(torch.argmax(logits, dim = 1).item())
                    
                    process.stdin.write(f"{action}\n")
                    process.stdin.flush()
                    step_count += 1
                    
                    game_state = self.game_state.game_state
                    
                    timed_out: bool = step_count >= self.config.max_steps
                    
                    if game_state == 2:
                        
                        ep_coins = max(0, self.game_state.coins - ep_coins_start)
                        ep_possible = self.game_state.total_coins
                        
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
                        
                        ep_init = True
                        
                        self.log.info("Won maze %d" % maze_count)
                        
                        if maze_count >= self.max_mazes:
                            break
                        
                        process.stdin.write("new\n")
                        process.stdin.flush()
                        
                        first_msg = True
                        
                        continue

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
                        
                        ep_init = True
                        
                        if maze_count >= self.max_mazes:
                            break
                        
                        process.stdin.write("new\n")
                        process.stdin.flush()
                        
                        first_msg = True
                        
                        continue
                
                total_failed = total_died + total_timeout
                win_rate = total_won / maze_count * 100 if maze_count > 0 else 0.0
                avg_steps = total_steps / maze_count if maze_count > 0 else 0.0
                coin_rate = total_coins / total_coins_possible * 100 if total_coins_possible > 0 else 0.0

            else:
                
                self.log.info("TrainedModelPlayer started")

            try:
                process.stdin.write("quit\n")
                process.stdin.flush()
            except OSError:
                pass

            try:
                process.stdin.close()
            except OSError:
                pass

            try:
                process.kill()
            except OSError:
                pass

            process.wait()

            try:
                process.stdout.close()
            except OSError:
                pass
            
        except Exception:
            self.log.error(traceback.format_exc())

        finally:
            
            self.__agent_running = False
            
            self.log.info("=" * 50)
            self.log.info("CNN AGENT SUMMARY")
            self.log.info("=" * 50)
            self.log.info("Total mazes        : %d" % maze_count)
            self.log.info("Won                : %d  (%.1f%%)" % (total_won, win_rate))
            self.log.info("Failed             : %d" % total_failed)
            self.log.info("   Died            : %d" % total_died)
            self.log.info("   Timed out       : %d" % total_timeout)
            self.log.info("Avg steps/maze     : %.1f" % avg_steps)
            self.log.info("Coins collected    : %d / %d  (%.1f%%)" % (total_coins, total_coins_possible, coin_rate))
            self.log.info("=" * 50)
            self.log.info("TrainedModelPlayer Thread stopped!")

    def _start_bot(self):

        self.log.info("Run TrainedModelPlayer Thread!")

        self.thread = Thread(name = "AIThread", target = self.__start, daemon = True)

        self.__agent_running = True

        self.thread.start()
        
    def run(self) -> None:

        self._start_bot()

        try:
            
            while self.thread.is_alive():
                self.thread.join(timeout = 1)
                
        except KeyboardInterrupt:
            pass
