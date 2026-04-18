import random
from collections import deque

import numpy as np

class ReplayBuffer:

    def __init__(self, capacity: int):
        
        self._buf: deque = deque(maxlen = capacity)

    def push(self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: float,
        ) -> None:
        
        self._buf.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        
        batch = random.sample(self._buf, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        return (
            np.stack(states).astype(np.float32),
            np.array(actions, dtype = np.int64),
            np.array(rewards, dtype = np.float32),
            np.stack(next_states).astype(np.float32),
            np.array(dones, dtype = np.float32),
        )

    def __len__(self) -> int:
        return len(self._buf)
