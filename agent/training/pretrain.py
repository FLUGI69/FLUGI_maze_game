"""Supervised pre-training: teach the CNN to classify mazes as survivable or impossible.

Generates N mazes from the game, labels each with pathfinder.check_survivability(),
and trains a binary classifier head on the CNN backbone. The learned conv weights
are then transferred to the DQN for RL fine-tuning.
"""

import logging
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from config import Config
from obj.game_process import GameProcess
from obj.pathfinder import Pathfinder


class _ClassifierHead(nn.Module):
    """Temporary binary classifier that shares the CNN backbone with DQN."""

    def __init__(self, dqn):
        
        super().__init__()
        
        self.dqn = dqn

        self.head = nn.Linear(128, 1)

    def forward(self, x):
        
        grid = x[:, :self.dqn._grid_size].view(-1, self.dqn._grid_c, self.dqn._grid_h, self.dqn._grid_w)
        scalars = x[:, self.dqn._grid_size:]

        g = self.dqn.pool(torch.relu(self.dqn.bn1(self.dqn.conv1(grid))))
        g = self.dqn.pool(torch.relu(self.dqn.bn2(self.dqn.conv2(g))))
        g = torch.relu(self.dqn.bn3(self.dqn.conv3(g)))
        g = g.view(g.size(0), -1)

        combined = torch.cat([g, scalars], dim=1)
        combined = torch.relu(self.dqn.fc1(combined))
        combined = torch.relu(self.dqn.fc2(combined))

        return self.head(combined).squeeze(-1)


class Pretrainer:

    def __init__(self, device_mode: str = "auto"):

        self.log = logging.getLogger(self.__class__.__name__)
        
        self._device = self._resolve_device(device_mode)
        
        self._pathfinder = Pathfinder()
        
        self._exe_path = Config.root_dir / Config.agent.exe_name
        
        self._model_dir = Config.root_dir / Config.training.model_dir
        self._model_dir.mkdir(exist_ok=True)

    def _resolve_device(self, mode: str) -> torch.device:
        
        if mode == "gpu" and torch.cuda.is_available():
            
            return torch.device("cuda")
        
        if mode == "cpu" or not torch.cuda.is_available():
            
            return torch.device("cpu")
        
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def run(self, num_samples: int = 3000, epochs: int = 30, batch_size: int = 64):

        self.log.info("SUPERVISED PRE-TRAINING STARTED - device: %s" % (self._device))
        self.log.info("collecting %d maze samples..." % num_samples)

        observations, labels = self._collect_data(num_samples)

        survivable_count = int(labels.sum())
        
        impossible_count = len(labels) - survivable_count
        
        self.log.info("dataset: %d samples - %d survivable (%.1f%%) - %d impossible (%.1f%%)" % (
            len(labels), 
            survivable_count, 
            survivable_count / len(labels) * 100,
            impossible_count, 
            impossible_count / len(labels) * 100
            )
        )

        self._train_classifier(observations, labels, epochs, batch_size)

    def _collect_data(self, num_samples: int):

        observations = []
        labels = []

        game = GameProcess(self._exe_path)

        try:
            for i in range(num_samples):

                gs = game.read_state()

                if gs is None:
                    
                    self.log.warning("game ended at sample %d - restarting" % i)
                    
                    game.close()
                    game = GameProcess(self._exe_path)
                    gs = game.read_state()
                    
                    if gs is None:
                        break

                obs = gs.to_observation()
                
                survivable = self._pathfinder.check_survivability(
                    gs.walls_array, 
                    gs.player_pos,
                    gs.coins, 
                    gs.shields,
                    gs.traps,
                    gs.exit_pos,
                    gs.hp, 
                    gs.has_shield,
                    gs.width, 
                    gs.height
                )

                observations.append(obs)
                labels.append(1.0 if survivable else 0.0)

                game.send("new")

                if (i + 1) % 500 == 0:
                    surv = sum(labels)
                    self.log.info("collected %d/%d (%.1f%% survivable so far)" % (
                        i + 1, num_samples, surv / (i + 1) * 100))

        finally:
            
            game.send("quit")
            game.close()

        return np.array(observations, dtype=np.float32), np.array(labels, dtype=np.float32)

    def _train_classifier(self, observations, labels, epochs, batch_size):

        from .dqn import DQN

        obs_size = observations.shape[1]
        action_count = 5  # up, down, left, right, skip

        dqn = DQN(obs_size, action_count)
        classifier = _ClassifierHead(dqn).to(self._device)

        optimizer = optim.Adam(classifier.parameters(), lr=0.001)
        criterion = nn.BCEWithLogitsLoss()

        X = torch.from_numpy(observations)
        y = torch.from_numpy(labels)

        n = len(X)
        indices = np.arange(n)

        self.log.info("training classifier - %d epochs, batch_size=%d, device=%s" % (
            epochs,
            batch_size, 
            self._device
            )
        )

        t0 = time.perf_counter()

        for epoch in range(1, epochs + 1):

            np.random.shuffle(indices)
            
            epoch_loss = 0.0
            correct = 0
            total = 0

            classifier.train()

            for start in range(0, n, batch_size):

                batch_idx = indices[start:start + batch_size]
                
                xb = X[batch_idx].to(self._device)
                yb = y[batch_idx].to(self._device)

                logits = classifier(xb)
                loss = criterion(logits, yb)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item() * len(batch_idx)
                preds = (logits > 0).float()
                correct += (preds == yb).sum().item()
                total += len(batch_idx)

            acc = correct / total * 100
            avg_loss = epoch_loss / total
            elapsed = time.perf_counter() - t0

            self.log.info("epoch %d/%d - loss: %.4f - accuracy: %.1f%% - %.1fs" % (
                epoch, 
                epochs, 
                avg_loss, 
                acc, 
                elapsed
                )
            )

        with torch.no_grad():
            
            dqn.out.weight[4] = -classifier.head.weight[0]
            dqn.out.bias[4] = -classifier.head.bias[0]

        self.log.info("skip action (index 4) initialized from classifier head")

        # Save the DQN weights (conv + fc layers + skip-initialized output)
        save_path = self._model_dir / "pretrained.pt"
        torch.save(dqn.state_dict(), save_path)

        self.log.info("pre-trained weights saved to %s" % save_path)
        self.log.info("PRE-TRAINING COMPLETE - %.1f%% accuracy" % acc)
