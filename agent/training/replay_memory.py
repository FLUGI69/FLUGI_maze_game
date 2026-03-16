import random
import logging
from collections import deque

import numpy as np

from config import Config

class ReplayMemory:

    def __init__(self, capacity: int = None):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        capacity = capacity or Config.training.memory_size
        self._buffer = deque(maxlen = capacity)
        
        self.log.debug("replay memory created - capacity: %d" % (capacity))

    def push(self, state, action, reward, next_state, done):
        
        self._buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int = None):
        
        batch_size = batch_size or Config.training.batch_size
        batch = random.sample(self._buffer, batch_size)
        
        states, actions, rewards, next_states, dones = zip(*batch)
        
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards, dtype = np.float32),
            np.array(next_states),
            np.array(dones, dtype = np.float32),
        )

    def __len__(self):
        return len(self._buffer)
