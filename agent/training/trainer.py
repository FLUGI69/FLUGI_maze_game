import logging
import time
from pathlib import Path

import numpy as np
import torch
import torch.optim as optim
import torch.nn.functional as F
import torch.optim.lr_scheduler as lr_scheduler

from config import Config
from .environment import MazeEnvironment
from .dqn import DQN
from .replay_memory import ReplayMemory
from .chart import TrainingChart


class Trainer:

    def __init__(self, device_mode: str = "auto"):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self._env = MazeEnvironment()
        self._obs_size = self._env.observation_size
        self._action_count = self._env.action_count
        self._device = self._resolve_device(device_mode)

        self._policy_net = DQN(self._obs_size, self._action_count).to(self._device)
        
        # Load pre-trained conv weights if available
        pretrained_path = (Config.root_dir / Config.training.model_dir / "pretrained.pt")
        
        if pretrained_path.exists() == True:
            
            pretrained = torch.load(pretrained_path, map_location = self._device, weights_only = True)
            missing, unexpected = self._policy_net.load_state_dict(pretrained, strict = False)
            
            self.log.info("loaded pre-trained weights from %s (missing: %d, unexpected: %d)" % (
                pretrained_path.name, 
                len(missing), 
                len(unexpected)
                )
            )
        
        # Resume from previous training if final.pt exists
        final_path = (Config.root_dir / Config.training.model_dir / "final.pt")
        
        if final_path.exists() == True:
            
            saved = torch.load(final_path, map_location = self._device, weights_only = True)
            self._policy_net.load_state_dict(saved)
            
            self.log.info("resumed training from %s" % final_path.name)
        
        self._target_net = DQN(self._obs_size, self._action_count).to(self._device)
        self._target_net.load_state_dict(self._policy_net.state_dict())

        self._optimizer = optim.Adam(self._policy_net.parameters(), lr = Config.training.learning_rate)
        self._scheduler = lr_scheduler.ReduceLROnPlateau(self._optimizer, mode = "max", factor = 0.5, patience = 100)
        self._memory = ReplayMemory()
        self._epsilon = Config.training.epsilon_start

        self._model_dir = Config.root_dir / Config.training.model_dir
        self._model_dir.mkdir(exist_ok = True)

        self.log.info("Trainer initialized - device: %s, obs: %d, actions: %d" % (
            self._device, 
            self._obs_size, 
            self._action_count
            )
        )

        if self._device.type == "cuda":
            
            self.log.info("GPU: %s - VRAM: %.0f MB" % (
                torch.cuda.get_device_name(0),
                torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
                )
            )
            
        else:
            
            self.log.info("running on CPU - use --gpu to enable CUDA")

    def _resolve_device(self, mode: str) -> torch.device:
        
        if mode == "cpu":
            
            self.log.info("forced CPU mode (--cpu)")
            
            return torch.device("cpu")
        
        if mode == "gpu":
            
            if torch.cuda.is_available() == False:
                
                self.log.warning("--gpu requested but CUDA not available - falling back to CPU")
                
                return torch.device("cpu")
            
            self.log.info("forced GPU mode (--gpu)")
            
            return torch.device("cuda")

        if torch.cuda.is_available() == True:
            
            self.log.info("auto-detected CUDA")
            
            return torch.device("cuda")
        
        return torch.device("cpu")

    def train(self):
        
        chart = TrainingChart()

        self.log.info("training started on %s (stop: close chart or Ctrl+C)" % (self._device))

        best_reward = float("-inf")
        total_wins = 0
        total_losses = 0
        total_skips = 0
        total_good_skips = 0
        optimize_steps = 0
        total_steps = 0
        ep = 0
        train_start = time.perf_counter()

        try:

            while chart.stopped == False:
                
                ep += 1
                ep_start = time.perf_counter()
                step_count = 0
                
                gs = self._env.reset()
                state = gs.to_observation()
                episode_reward = 0.0
                episode_loss = 0.0
                episode_optimize_steps = 0
                done = False
                info = {}

                while done == False:
                    
                    action = self._select_action(state)
                    next_gs, reward, done, info = self._env.step(action)

                    if next_gs is None:
                        
                        self.log.warning("environment returned None at episode %d" % (ep))
                        break

                    next_state = next_gs.to_observation()
                    
                    self._memory.push(state, action, reward, next_state, done)
                    state = next_state           
                    episode_reward += reward
                    step_count += 1

                    if step_count % 50 == 0:
                        
                        chart.pump()

                    if step_count % Config.training.optimize_interval == 0:
                        
                        loss = self._optimize()
                        
                    else:
                        
                        loss = None
                    
                    if loss is not None:
                        
                        episode_loss += loss
                        episode_optimize_steps += 1
                        optimize_steps += 1

                ep_elapsed = time.perf_counter() - ep_start
                ep_steps = info.get("moves", 0)
                total_steps += ep_steps

                self._epsilon = max(
                    Config.training.epsilon_end,
                    self._epsilon * Config.training.epsilon_decay,
                )

                won = info.get("state") == "won"
                skipped = info.get("state") == "skipped"
                died = info.get("state") == "dead"
                
                if won == True:
                    
                    total_wins += 1

                if died == True:
                    
                    total_losses += 1

                if skipped == True:
                    
                    total_skips += 1
                    
                    if info.get("survivable") == False:
                        
                        total_good_skips += 1

                if ep % Config.training.target_sync == 0:
                    
                    self._target_net.load_state_dict(self._policy_net.state_dict())
                    
                    self.log.debug("target network synced at episode %d" % (ep))

                if episode_reward > best_reward:
                    
                    best_reward = episode_reward
                    self._save_model("best.pt")
                    
                    self.log.info("new best reward: %.1f at episode %d" % (best_reward, ep))

                avg_loss = episode_loss / max(episode_optimize_steps, 1)

                old_lr = self._optimizer.param_groups[0]["lr"]
                self._scheduler.step(episode_reward)
                new_lr = self._optimizer.param_groups[0]["lr"]

                if new_lr < old_lr:
                    
                    self.log.info("learning rate reduced: %.6f -> %.6f" % (old_lr, new_lr))
                
                chart.update(ep, episode_reward, self._epsilon, won, avg_loss, skipped)

                elapsed = time.perf_counter() - train_start
                steps_per_sec = total_steps / max(elapsed, 0.001)
                ep_per_sec = ep / max(elapsed, 0.001)

                if skipped == True:
                    
                    outcome = "GOOD SKIP" if info.get("survivable") == False else "BAD SKIP"
                    
                elif won == True:
                    
                    outcome = "WON"
                    
                else:
                    
                    outcome = "DIED"

                self.log.info("ep %d \u2014 reward: %.1f \u2014 best: %.1f \u2014 eps: %.3f \u2014 loss: %.4f \u2014 %s \u2014 moves: %d \u2014 %.1fs (%.1f ep/s, %.0f step/s)" % (
                    ep, 
                    episode_reward,
                    best_reward, 
                    self._epsilon, 
                    avg_loss,
                    outcome, ep_steps,
                    ep_elapsed, ep_per_sec, steps_per_sec
                    )
                )

                if ep % 100 == 0:
                    
                    self._save_model(f"checkpoint_{ep}.pt")
                    
                    played = total_wins + total_losses
                    win_rate = total_wins / max(played, 1)
                    skip_rate = total_skips / ep
                    
                    self.log.info("checkpoint %d - win: %d/%d (%.1f%%) - skip: %d (%d good) - memory: %d - optimize steps: %d" % (
                        ep, 
                        total_wins,
                        played,
                        win_rate * 100, 
                        total_skips,
                        total_good_skips,
                        len(self._memory), 
                        optimize_steps
                        )
                    )

        except KeyboardInterrupt:
            self.log.warning("training interrupted at episode %d" % (ep))

        finally:
            
            self._save_model("final.pt")
            self._env.close()
            
            chart.save()
            chart.close()

        total_elapsed = time.perf_counter() - train_start
        minutes = total_elapsed / 60

        played = total_wins + total_losses

        self.log.info("training complete \u2014 %d/%d wins (%.1f%%) \u2014 %d skips (%d good) \u2014 %.1f min \u2014 %s \u2014 models in %s" % (
            total_wins, 
            played,
            total_wins / max(played, 1) * 100,
            total_skips,
            total_good_skips,
            minutes,
            self._device,
            self._model_dir
            )
        )

    def predict(self, observation: np.ndarray) -> int:
        
        with torch.inference_mode():
            
            tensor = torch.from_numpy(observation).unsqueeze(0).to(self._device)
            
            q_values = self._policy_net(tensor)
            
            return q_values.argmax(dim = 1).item()

    def _select_action(self, state: np.ndarray) -> int:
        
        if np.random.random() < self._epsilon:
            
            # Only explore movement actions — skip is never chosen randomly.
            # The policy net can still select skip when it learns to identify
            # impossible mazes.  This prevents bad skips from random exploration.
            action = np.random.randint(4)
            
            self.log.debug("action: %d (random, eps=%.3f)" % (
                action, 
                self._epsilon
                )
            )
            
            return action

        with torch.inference_mode():
            
            tensor = torch.from_numpy(state).unsqueeze(0).to(self._device)
            
            q_values = self._policy_net(tensor)
            
            action = q_values.argmax(dim = 1).item()
            
            self.log.debug("action: %d (greedy, q_max=%.3f)" % (
                action, 
                q_values.max().item()
                )
            )
            
            return action

    def _optimize(self) -> float | None:
        
        if len(self._memory) < Config.training.batch_size:
            return None

        states, actions, rewards, next_states, dones = self._memory.sample()

        states_t = torch.from_numpy(states).to(self._device)
        actions_t = torch.from_numpy(actions).long().unsqueeze(1).to(self._device)
        rewards_t = torch.from_numpy(rewards).to(self._device)
        next_states_t = torch.from_numpy(next_states).to(self._device)
        dones_t = torch.from_numpy(dones).to(self._device)

        q_values = self._policy_net(states_t).gather(1, actions_t).squeeze(1)

        with torch.no_grad():
            
            next_actions = self._policy_net(next_states_t).argmax(dim = 1, keepdim = True)
            next_q = self._target_net(next_states_t).gather(1, next_actions).squeeze(1)
            
            target = rewards_t + Config.training.gamma * next_q * (1.0 - dones_t)

        loss = F.smooth_l1_loss(q_values, target)
        
        self._optimizer.zero_grad(set_to_none = True)
        loss.backward()
        
        torch.nn.utils.clip_grad_norm_(self._policy_net.parameters(), 1.0)
        
        self._optimizer.step()
        loss_val = loss.item()
        
        self.log.debug("optimize - loss: %.4f, memory: %d" % (loss_val, len(self._memory)))
        
        return loss_val

    def _save_model(self, filename: str):
        
        path = self._model_dir / filename
        torch.save(self._policy_net.state_dict(), path)
        
        self.log.debug("model saved: %s" % (path))

    def load_model(self, filename: str = "best.pt"):
        
        path = self._model_dir / filename
        self._policy_net.load_state_dict(torch.load(path, weights_only = True))
        self._policy_net.eval()
        
        self.log.info("model loaded from %s" % (path))
