import logging

import numpy as np

class GameState:

    def __init__(self, 
        data: dict, 
        walls_cache: np.ndarray = None
        ):
        
        self.log = logging.getLogger(self.__class__.__name__)

        try:
            
            self.state = data["state"]
            self.moves = data["moves"]

            p = data["player"]
            self.player_pos = (p["x"], p["y"])
            self.hp = p["hp"]
            self.coins_collected = p["coins"]
            self.total_coins = p["totalCoins"]
            self.has_shield = p["shield"]

            m = data["maze"]
            self.width = m["width"]
            self.height = m["height"]

            if walls_cache is not None:
                
                self.walls_array = walls_cache
                self.grid = None
                
            else:
                
                self.grid = m["grid"]
                self.walls_array = (1.0 - np.array(self.grid, dtype = np.float32)).ravel()

            self.coins = [(c["x"], c["y"]) for c in data["coins"]]
            self.shields = [(s["x"], s["y"]) for s in data["shields"]]
            self.traps = [(t["x"], t["y"]) for t in data["traps"]]
            self.exit_pos = (data["exit"]["x"], data["exit"]["y"])
            self.exit_open = data["exit"]["open"]

        except KeyError as e:
            self.log.error("invalid game state data - missing key: %s" % (e))
            raise
        
    _STATE_MAP = {0: "title", 1: "playing", 2: "won", 3: "dead"}

    @classmethod
    def from_compact(cls, parts, cache):
        
        obj = cls.__new__(cls)
        obj.player_pos = (int(parts[0]), int(parts[1]))
        obj.hp = int(parts[2])
        obj.coins_collected = int(parts[3])
        obj.has_shield = parts[4] == b'1'
        obj.exit_open = parts[5] == b'1'
        obj.state = cls._STATE_MAP[int(parts[6])]
        obj.moves = int(parts[7])
        obj.width = cache["width"]
        obj.height = cache["height"]
        obj.walls_array = cache["walls"]
        obj.exit_pos = cache["exit_pos"]
        obj.total_coins = cache["total_coins"]
        obj.grid = None

        if len(parts) > 8:
            
            obj.coins = cls._parse_coords(parts[8])
            obj.shields = cls._parse_coords(parts[9])
            obj.traps = cls._parse_coords(parts[10])
            
        else:
            
            obj.coins = cache["coins"]
            obj.shields = cache["shields"]
            obj.traps = cache["traps"]

        return obj

    @staticmethod
    def _parse_coords(data):
        
        if len(data) == 0:
            return []
        
        nums = data.split(b',')
        
        return [(int(nums[i]), int(nums[i + 1])) for i in range(0, len(nums), 2)]
    
    def to_observation(self) -> np.ndarray:

        w = self.width
        wh = w * self.height

        obs = np.zeros(6 * wh + 4, dtype = np.float32)

        obs[:wh] = self.walls_array

        px, py = self.player_pos
        obs[wh + py * w + px] = 1.0

        off = 2 * wh
        for cx, cy in self.coins:
            obs[off + cy * w + cx] = 1.0

        off = 3 * wh
        for tx, ty in self.traps:
            obs[off + ty * w + tx] = 1.0

        off = 4 * wh
        for sx, sy in self.shields:
            obs[off + sy * w + sx] = 1.0

        ex, ey = self.exit_pos
        obs[5 * wh + ey * w + ex] = 1.0

        base = 6 * wh
        
        obs[base] = self.hp / 3.0
        obs[base + 1] = self.coins_collected / max(self.total_coins, 1)
        obs[base + 2] = 1.0 if self.has_shield else 0.0
        obs[base + 3] = 1.0 if self.exit_open else 0.0

        return obs
