import logging

from config import Config
from obj.game_process import GameProcess
from obj.game_state import GameState
from obj.pathfinder import Pathfinder


class MazeEnvironment:

    _actions = ["up", "down", "left", "right", "skip"]

    def __init__(self):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self._exe_path = Config.root_dir / Config.agent.exe_name
        
        self._game: GameProcess | None = None
        self._pathfinder = Pathfinder()
        
        self._prev_state: GameState | None = None
        self._pending_state: GameState | None = None
        
        self._last_state: str = "playing"
        
        self._episode_steps = 0
        self._visited: set = set()
        
        self.log.info("environment initialized - exe: %s" % (self._exe_path))

    @property
    def action_count(self) -> int:
        
        return len(self._actions)

    @property
    def observation_size(self) -> int:
    
        return Config.maze.channels * Config.maze.width * Config.maze.height + 4

    def reset(self) -> GameState:
        
        # If a skip already fetched the next maze, use it
        if self._pending_state is not None:
            
            gs = self._pending_state
            self._pending_state = None
            self._episode_steps = 0
            self._visited = set()
            self._prev_state = gs
            
            self.log.debug("using pending state from skip")
            
            return gs

        if self._game is not None and self._game.is_alive() == False:
            
            self._game.close()
            self._game = None
            
            self.log.debug("dead game process cleaned up")

        if self._game is None:
            
            self._game = GameProcess(self._exe_path)
            
            self._episode_steps = 0
            self._visited = set()

            gs = self._game.read_state()
            self._prev_state = gs
            
            self.log.debug("new game process started - state: %s" % (gs.state))
            
            return gs

        if self._last_state in ("won", "skipped"):
            
            self._game.send("new")
            
        elif self._last_state == "dead":
            
            self._game.send("restart")

        self._episode_steps = 0
        self._visited = set()

        gs = self._game.read_state()
        
        if gs is None:
            
            self.log.warning("game process died during reset - restarting")
            
            self._game.close()
            self._game = GameProcess(self._exe_path)
            
            gs = self._game.read_state()

        self._prev_state = gs
        
        self.log.debug("environment reset - state: %s" % (gs.state))
        
        return gs

    def step(self, action_index: int) -> tuple:

        # --- SKIP action: only allowed on the very first step ---
        if action_index == 4:
            
            if self._episode_steps > 0:
                # Penalize skip after first step - treat as wasted move
                self._episode_steps += 1
                
                return self._prev_state, -2.0, False, {
                    "state": "playing", 
                    "moves": self._prev_state.moves, 
                    "steps": self._episode_steps
                }
           
            return self._handle_skip()

        action = self._actions[action_index]
        self._game.send(action)
        
        self._episode_steps += 1

        gs = self._game.read_state()
        
        if gs is None:
            
            self.log.warning("game process ended unexpectedly at step %d" % (self._episode_steps))
            self._last_state = "process_ended"
            
            return None, 0.0, True, {"reason": "process_ended"}

        reward = self._compute_reward(self._prev_state, gs)
        
        done = gs.state in ("won", "dead")

        if self._episode_steps >= Config.training.max_steps and done == False:
            
            done = True
            reward -= 20.0
            
            self.log.info("episode timed out after %d steps" % (self._episode_steps))

        info = {
            "state": gs.state if self._episode_steps < Config.training.max_steps or gs.state != "playing" else "timeout",
            "moves": gs.moves,
            "steps": self._episode_steps,
        }

        if gs.state == "won":
            
            self.log.info("episode won in %d moves (reward: %.2f)" % (gs.moves, reward))

        elif gs.state == "dead":
            
            self.log.info("episode died after %d moves (reward: %.2f)" % (gs.moves, reward))

        if done == True:
            
            self._last_state = gs.state if gs.state in ("won", "dead") else "dead"

        self._prev_state = gs
        
        return gs, reward, done, info

    def _handle_skip(self) -> tuple:
        """Handle the skip action: check survivability, reward accordingly, get new maze."""

        gs = self._prev_state

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

        if survivable:
            
            reward = Config.training.bad_skip_reward    # -20: shouldn't have skipped
            
            self.log.info("BAD SKIP at step %d - maze was survivable (reward: %.1f)" % (
                self._episode_steps, 
                reward
                )
            )
            
        else:
            
            reward = Config.training.good_skip_reward   # +5: smart decision
            
            self.log.info("GOOD SKIP at step %d - maze was impossible (reward: %.1f)" % (
                self._episode_steps, 
                reward
                )
            )

        # Request a new maze from the game process
        self._game.send("new")
        new_gs = self._game.read_state()

        if new_gs is None:
            
            self.log.warning("game process died during skip")
            self._last_state = "process_ended"
            
            return None, reward, True, {"reason": "process_ended"}

        self._pending_state = new_gs
        self._last_state = "skipped"

        info = {
            "state": "skipped",
            "survivable": survivable,
            "moves": gs.moves,
            "steps": self._episode_steps,
        }

        # Return the old state as next_state (done=True, so next_q is zeroed)
        return gs, reward, True, info

    def close(self):
        
        if self._game is not None:
            
            self._game.send("quit")
            self._game.close()
            self._game = None
            
            self.log.info("environment closed")

    def _nearest_coin_dist(self, gs: GameState) -> float:

        if len(gs.coins) == 0:
            return 0.0

        px, py = gs.player_pos
        best = float("inf")

        for cx, cy in gs.coins:
            
            d = abs(px - cx) + abs(py - cy)

            if d < best:
                best = d

        return best

    def _exit_dist(self, gs: GameState) -> float:

        px, py = gs.player_pos
        ex, ey = gs.exit_pos

        return abs(px - ex) + abs(py - ey)

    def _compute_reward(self, prev: GameState, curr: GameState) -> float:
        
        reward = -0.05   # higher step penalty → agent values efficiency

        if curr.state == "won":
            
            # win bonus + efficiency bonus for fast completion
            efficiency = max(0.0, 1.0 - self._episode_steps / Config.training.max_steps)
            reward += 100.0 + efficiency * 50.0

        elif curr.state == "dead":
            
            reward -= 50.0

        else:

            # -- movement quality --
            if curr.player_pos == prev.player_pos:
                
                reward -= 1.5       # wall bump: much harsher

            elif curr.player_pos in self._visited:
                
                reward -= 0.3       # revisit: harsher

            else:
                
                reward += 0.1       # new cell exploration bonus

            self._visited.add(curr.player_pos)
            
            # -- coin collection --
            if curr.coins_collected > prev.coins_collected:
                
                reward += 20.0      # big reward for each coin
                
                # progressive bonus: later coins worth more
                progress = curr.coins_collected / max(curr.total_coins, 1)
                reward += progress * 5.0
                
                # all coins collected → exit just opened
                if curr.coins_collected == curr.total_coins:
                    reward += 25.0

            else:

                # -- distance shaping --
                if curr.exit_open:
                    
                    # all coins done → head to exit
                    prev_d = self._exit_dist(prev)
                    curr_d = self._exit_dist(curr)
                    reward += (prev_d - curr_d) * 0.5
                    
                else:
                    
                    # still collecting → head toward nearest coin
                    prev_dist = self._nearest_coin_dist(prev)
                    curr_dist = self._nearest_coin_dist(curr)
                    delta = prev_dist - curr_dist
                    reward += delta * 0.5

            # -- shield pickup --
            if curr.has_shield and not prev.has_shield:
                reward += 3.0

            if curr.has_shield and prev.has_shield == False:
                
                reward += 2.0

            if curr.has_shield == False and prev.has_shield and curr.hp == prev.hp:
                
                reward -= 1.0

            if curr.hp < prev.hp:
                
                reward -= 10.0

            if curr.exit_open and prev.exit_open == False:
                
                reward += 3.0

            if curr.exit_open == True:

                prev_exit = self._exit_dist(prev)
                curr_exit = self._exit_dist(curr)
                delta = prev_exit - curr_exit
                
                reward += delta * 0.2

        return reward
