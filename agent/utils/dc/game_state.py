import json
import re
from pydantic import Field, PrivateAttr
from threading import Lock

from utils.dataclass import DataclassBaseModel

class GameState(DataclassBaseModel):

    px: int = 1
    py: int = 1
    hp: int = 3
    coins: int = 0
    total_coins: int = 10
    shield: bool = False
    exit_open: bool = False
    game_state: int = 1 # 0=Title 1=Playing 2=Won 3=Dead
    move_count: int = 0
    width: int = 41
    height: int = 25
    grid: list = Field(default_factory = list)
    active_coins: set = Field(default_factory = set)
    active_shields: set = Field(default_factory = set)
    active_traps: set = Field(default_factory = set)
    exit_x: int = 39
    exit_y: int = 23
    survivable: bool = True

    _lock: Lock = PrivateAttr(default_factory = Lock)

    def update(self, line: str) -> bool:

        line = line.strip()
        
        if line == "":
            return

        if line.startswith('{'):
            
            new_maze = True
       
            json_str = self._extract_first_json(line)
            
            if json_str is not None:
                
                try:
                    
                    data = json.loads(json_str)
                    self.update_full(data)
                
                except Exception as e:
                    pass
                    
            else:
                pass
            
        else:
            
            new_maze = False
   
            self.update_compact(line)
        
        return new_maze

    @staticmethod
    def _extract_first_json(s: str) -> str | None:

        match = re.search(r'\{.*\}', s)
        
        if match is not None:
            return match.group(0)
        
        return None
    
    def update_full(self, data: dict) -> None:

        with self._lock:

            p = data["player"]
            self.px = p["x"]
            self.py = p["y"]
            self.hp = p["hp"]
            self.coins = p["coins"]
            self.total_coins = p.get("totalCoins", 10)
            self.shield = p["shield"]

            maze = data["maze"]
            self.width = maze["width"]
            self.height = maze["height"]
            
            if "grid" in maze:
                self.grid = maze["grid"]

            self.active_coins = {(c["x"], c["y"]) for c in data.get("coins",   [])}
            self.active_shields = {(s["x"], s["y"]) for s in data.get("shields", [])}
            self.active_traps = {(t["x"], t["y"]) for t in data.get("traps",   [])}

            maze_exfil = data.get("exit", {})
            
            self.exit_x = maze_exfil.get("x", self.width  - 2)
            self.exit_y = maze_exfil.get("y", self.height - 2)
            self.exit_open = maze_exfil.get("open", False)
            self.move_count = data.get("moves", 0)
            self.survivable = data.get("survivable", True)

            state_map = {
                "playing": 1, 
                "won": 2, 
                "dead": 3, 
                "title": 0
            }
            
            self.game_state = state_map.get(data.get("state", "playing"), 1)

    def update_compact(self, line: str) -> None:
        """
        Parse the compact tab-separated update sent every subsequent step.

        Format (8 fields):  px  py  hp  coins  shield  exit_open  state_int  moves
        With items changed: ...  coins_xy  shields_xy  traps_xy
          where *_xy = "x1,y1,x2,y2,..." pairs
        """
        parts = line.split('\t')
        
        if len(parts) < 8:
            return

        with self._lock:

            self.px = int(parts[0])
            self.py = int(parts[1])
            self.hp = int(parts[2])
            self.coins = int(parts[3])
            self.shield = bool(int(parts[4]))
            self.exit_open = bool(int(parts[5]))
            self.game_state = int(parts[6])
            self.move_count = int(parts[7])

            if len(parts) >= 11:
                
                self.active_coins = self._parse_pairs(parts[8])
                self.active_shields = self._parse_pairs(parts[9])
                self.active_traps = self._parse_pairs(parts[10])

    @staticmethod
    def _parse_pairs(s: str) -> set:
        
        if not s.strip():
            return set()
        
        nums = list(map(int, s.split(',')))
        
        return {(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)}
