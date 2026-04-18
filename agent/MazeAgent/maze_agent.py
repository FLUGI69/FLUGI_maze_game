import json
import traceback
import subprocess
from collections import deque
from threading import Thread

from utils.dc.game_state import GameState
from utils.dc.agent_stats import EpisodeResult
from .config import MazeAgentConfig

class MazeAgent:

    def __init__(self, config: MazeAgentConfig) -> None:

        self.__agent_running: bool = False

        self.config = config
        
        self.process_manager = config.process_manager
        
        self.log = config.logger
        
        self.stats = self.config.agent_stats
        
        self.subprocess: subprocess.Popen | None = None

        self.__setup()
        
    @property
    def agent_running(self) -> bool:
        return self.__agent_running
    
    @agent_running.setter
    def agent_running(self, value: bool):
        self.__agent_running = value

    def __setup(self) -> None:

        self.__file__: str = __file__
        
        self.game_state = GameState()
        
    def __start(self) -> None:

        try:

            exe = self.config.exe_name

            self.log.info("Starting maze: %s" % str(exe))

            args = [str(exe), "--ai"] if self.config.headless == True \
                else [str(exe), "--ai", "--render"]

            self.subprocess = subprocess.Popen(
                args,
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                bufsize = 1,
                text = True,
            )

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
                    
                    self.log.debug("Failed maze %d (dead=%s, timeout=%s)" % (
                        maze_count, game_state == 3, timed_out,
                    ))
                    
                    if maze_count >= self.config.max_mazes:
                        break
                    
                    self.subprocess.stdin.write("new\n")
                    self.subprocess.stdin.flush()
                    
                    continue

                action = self._decide()
                
                self.subprocess.stdin.write(action + "\n")
                self.subprocess.stdin.flush()
                
                step_count += 1

            total_failed: int = total_died + total_timeout
            win_rate: float = total_won / maze_count * 100 if maze_count > 0 else 0.0
            avg_steps: float = total_steps / maze_count if maze_count > 0 else 0.0
            coin_rate: float = total_coins / total_coins_possible * 100 if total_coins_possible > 0 else 0.0
 
            self.subprocess.stdin.write("quit\n")
            self.subprocess.stdin.flush()
        
        except OSError:
            pass
                
        except Exception:
            self.log.error(traceback.format_exc())

        finally:
            
            self.__agent_running = False
            
            self.log.info("=" * 50)
            self.log.info("POLICY AGENT SUMMARY")
            self.log.info("=" * 50)
            self.log.info("Total mazes played : %d" % maze_count)
            self.log.info("Won                : %d  (%.1f%%)" % (total_won, win_rate))
            self.log.info("Failed             : %d" % total_failed)
            self.log.info("   Died            : %d" % total_died)
            self.log.info("   Timed out       : %d" % total_timeout)
            self.log.info("Avg steps/maze     : %.1f" % avg_steps)
            self.log.info("Coins collected    : %d / %d  (%.1f%%)" % (total_coins, total_coins_possible, coin_rate))
            self.log.info("=" * 50)
            
            self.log.info("MazeAgent Thread stopped!")

    def _start_bot(self) -> None:

        self.log.info("Run MazeAgent Thread!")

        self.thread: Thread = Thread(name = "AgentThread", target = self.__start, daemon = True)

        self.__agent_running = True

        self.thread.start()

    def run(self, **kwargs) -> None:

        self._start_bot()

        try:
            
            while self.thread.is_alive():
                self.thread.join(timeout = 1)
                
        except KeyboardInterrupt:
            pass

    def _decide(self) -> str:

        with self.game_state._lock:
            
            px: int = self.game_state.px
            py: int = self.game_state.py
            shield: bool = self.game_state.shield
            exit_open: bool = self.game_state.exit_open
            ex: int = self.game_state.exit_x
            ey: int = self.game_state.exit_y
            coins: set[tuple[int, int]] = set(self.game_state.active_coins)
            shields: set[tuple[int, int]] = set(self.game_state.active_shields)
            traps: set[tuple[int, int]] = set(self.game_state.active_traps)
            grid: list[list[int]] = self.game_state.grid
            width: int = self.game_state.width
            height: int = self.game_state.height

        start: tuple[int, int] = (px, py)

        if shield == False and len(shields) > 0:
            
            target = self._nearest_reachable_with_fallback(start, shields, grid, traps, shield, width, height)
            
            if target is not None:
                
                path = self._bfs_with_fallback(start, {target}, grid, traps, shield, width, height)
                
                if path:
                    
                    return path[0]

        if len(coins) > 0:
            
            target = self._nearest_reachable_with_fallback(start, coins, grid, traps, shield, width, height)
            
            if target is not None:
                
                path = self._bfs_with_fallback(start, {target}, grid, traps, shield, width, height)
                
                if path:
                    
                    return path[0]

        if exit_open:
            
            path = self._bfs_with_fallback(start, {(ex, ey)}, grid, traps, shield, width, height)
            
            if path:
                
                return path[0]

        for action in ('up', 'down', 'left', 'right'):
            
            nx, ny = self._step(start, action)
            
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] != 0:
                return action

        return 'down'

    def _bfs_with_fallback(self,
        start: tuple[int, int],
        goals: set[tuple[int, int]],
        grid: list[list[int]],
        traps: set[tuple[int, int]],
        shield: bool,
        width: int,
        height: int,
        ) -> list[str] | None:

        path: list[str] | None = self._bfs(start, goals, grid, traps, shield, width, height)
        
        if path is not None:
            return path
        
        return self._bfs(start, goals, grid, set(), shield, width, height)

    def _bfs(self,
        start: tuple[int, int],
        goals: set[tuple[int, int]],
        grid: list[list[int]],
        traps: set[tuple[int, int]],
        shield: bool,
        width: int,
        height: int,
        ) -> list[str] | None:

        queue: deque[tuple[tuple[int, int], list[str]]] = deque()
        visited: set[tuple[int, int]] = {start}

        queue.append((start, []))

        while queue:

            pos, path = queue.popleft()

            if pos in goals:
                return path

            for action in ('up', 'down', 'left', 'right'):

                nx, ny = self._step(pos, action)
                npos: tuple[int, int] = (nx, ny)

                if npos in visited:
                    continue

                if not self._walkable(nx, ny, grid, traps, shield, width, height):
                    continue

                visited.add(npos)
                queue.append((npos, path + [action]))

        return None

    def _nearest_reachable_with_fallback(self,
        start: tuple[int, int],
        candidates: set[tuple[int, int]],
        grid: list[list[int]],
        traps: set[tuple[int, int]],
        shield: bool,
        width: int,
        height: int,
        ) -> tuple[int, int] | None:

        result = self._nearest_reachable(start, candidates, grid, traps, shield, width, height)
        
        if result is not None:
            return result
        
        return self._nearest_reachable(start, candidates, grid, set(), shield, width, height)

    def _walkable(self,
        x: int,
        y: int,
        grid: list[list[int]],
        traps: set[tuple[int, int]],
        shield: bool,
        width: int,
        height: int,
        ) -> bool:

        if not (0 <= x < width and 0 <= y < height):
            return False

        if grid[y][x] == 0:
            return False

        if not shield and (x, y) in traps:
            return False

        return True

    @staticmethod
    def _step(pos: tuple[int, int], action: str) -> tuple[int, int]:

        x: int = pos[0]
        y: int = pos[1]

        if action == 'up': return (x, y - 1)
        if action == 'down': return (x, y + 1)
        if action == 'left': return (x - 1, y)
        if action == 'right': return (x + 1, y)

        return pos

    def _nearest_reachable(self,
        start: tuple[int, int],
        candidates: set[tuple[int, int]],
        grid: list[list[int]],
        traps: set[tuple[int, int]],
        shield: bool,
        width: int,
        height: int,
        ) -> tuple[int, int] | None:

        queue: deque[tuple[int, int]] = deque()
        visited: set[tuple[int, int]] = {start}

        queue.append(start)

        while queue:

            pos = queue.popleft()

            if pos in candidates:
                return pos

            for action in ('up', 'down', 'left', 'right'):

                nx, ny = self._step(pos, action)
                npos: tuple[int, int] = (nx, ny)

                if npos in visited:
                    continue

                if not self._walkable(nx, ny, grid, traps, shield, width, height):
                    continue

                visited.add(npos)
                queue.append(npos)

        return None
