import logging

import torch
import torch.nn as nn
import torch.nn.functional as F

from config import Config


class DQN(nn.Module):

    def __init__(self, obs_size: int, action_count: int):
        
        super().__init__()
        
        self.log = logging.getLogger(self.__class__.__name__)

        self._grid_c = Config.maze.channels
        self._grid_h = Config.maze.height
        self._grid_w = Config.maze.width
        self._grid_size = self._grid_c * self._grid_h * self._grid_w
        self._scalar_size = obs_size - self._grid_size

        self.conv1 = nn.Conv2d(self._grid_c, 32, kernel_size = 3, padding = 1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size = 3, padding = 1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 64, kernel_size = 3, padding = 1)
        self.bn3 = nn.BatchNorm2d(64)
        self.pool = nn.MaxPool2d(2)

        conv_out = self._get_conv_out()

        self.fc1 = nn.Linear(conv_out + self._scalar_size, 256)
        self.fc2 = nn.Linear(256, 128)
        self.out = nn.Linear(128, action_count)

        self.log.debug("CNN created - grid: (%d,%d,%d), scalars: %d, conv_out: %d, actions: %d" % (
            self._grid_c, 
            self._grid_h, 
            self._grid_w,
            self._scalar_size, 
            conv_out, 
            action_count
            )
        )

    def _get_conv_out(self) -> int:

        x = torch.zeros(1, self._grid_c, self._grid_h, self._grid_w)
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = F.relu(self.bn3(self.conv3(x)))

        return x.view(1, -1).size(1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        
        grid = x[:, :self._grid_size].view(-1, self._grid_c, self._grid_h, self._grid_w)
        scalars = x[:, self._grid_size:]

        g = self.pool(F.relu(self.bn1(self.conv1(grid))))
        g = self.pool(F.relu(self.bn2(self.conv2(g))))
        g = F.relu(self.bn3(self.conv3(g)))
        g = g.view(g.size(0), -1)

        combined = torch.cat([g, scalars], dim = 1)
        combined = F.relu(self.fc1(combined))
        combined = F.relu(self.fc2(combined))
        
        return self.out(combined)
