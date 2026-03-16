import subprocess
import orjson
import sys
import logging
from pathlib import Path

from .game_state import GameState

class GameProcess:

    _ACTION_BYTES = {
        "up": b"up\n",
        "down": b"down\n",
        "left": b"left\n",
        "right": b"right\n",
        "new": b"new\n",
        "restart": b"restart\n",
        "quit": b"quit\n",
    }

    def __init__(self, exe_path: Path):
        
        self._log = logging.getLogger(self.__class__.__name__)
        
        self._log.debug("starting game process: %s" % (exe_path))

        self._proc = subprocess.Popen(
            [str(exe_path), "--ai"],
            stdin  = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = sys.stderr,
        )
        
        self._walls_cache = None
        self._state_cache = None
        
        self._log.info("game process started (pid: %d)" % (self._proc.pid))

    def read_state(self) -> GameState | None:
        
        line = self._proc.stdout.readline()
        
        if line == b"":
            
            self._log.warning("stdout closed - game process ended")
            return None
        
        if line[0:1] == b'{':
            
            try:
                
                data = orjson.loads(line)
                
            except orjson.JSONDecodeError:
                
                self._log.error("invalid JSON from game: %s" % (line.strip()))
                return None
            
            gs = GameState(data, self._walls_cache)
            
            if self._walls_cache is None:
                self._walls_cache = gs.walls_array
            
            self._state_cache = {
                "width": gs.width,
                "height": gs.height,
                "walls": gs.walls_array,
                "exit_pos": gs.exit_pos,
                "total_coins": gs.total_coins,
                "coins": gs.coins,
                "shields": gs.shields,
                "traps": gs.traps,
            }
            
            return gs
        
        parts = line.rstrip(b'\r\n').split(b'\t')
        
        gs = GameState.from_compact(parts, self._state_cache)
        
        if len(parts) > 8:
            
            self._state_cache["coins"] = gs.coins
            self._state_cache["shields"] = gs.shields
            self._state_cache["traps"] = gs.traps
        
        return gs

    def is_alive(self) -> bool:
        
        return self._proc.poll() is None

    def send(self, action: str):
        
        if self._proc.poll() is not None:
            
            self._log.debug("skipping send - process already exited")
            return

        if action == "new":
            
            self._walls_cache = None
        
        self._log.debug("sending action: %s" % (action))
        
        try:
            
            self._proc.stdin.write(self._ACTION_BYTES[action])
            self._proc.stdin.flush()
            
        except (OSError, BrokenPipeError):
            
            self._log.warning("broken pipe - game process died")

    def close(self):
        
        if self._proc.poll() is None:
            
            self._proc.terminate()
            self._proc.wait()
            
        self._log.info("game process closed (exit code: %s)" % (self._proc.returncode))
