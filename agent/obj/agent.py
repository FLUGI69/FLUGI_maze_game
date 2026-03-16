import sys
import logging

from config import Config
from obj import GameProcess, Strategist

class Agent:

    def __init__(self):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self._exe = Config.root_dir / Config.agent.exe_name
        
        self._game = None
        
        self._strategy = None
        
        self._wins = 0
        self._losses = 0
        
        self._steps = 0

    def run(self):
        
        if self._exe.exists() == False:
            
            self.log.error("executable not found: %s" % (self._exe))
            sys.exit(1)

        self._game = GameProcess(self._exe)
        self._strategy = Strategist()
        
        self.log.info("agent started - exe: %s" % (self._exe))

        try:
            
            self._loop()
            
        except (BrokenPipeError, KeyboardInterrupt):
            
            self.log.warning("interrupted")
            
        except Exception:
            
            self.log.exception("unexpected error")
            
        finally:
            
            self._game.close()
            
            total = self._wins + self._losses
            rate = self._wins / max(total, 1) * 100
            
            self.log.info("agent finished - %d/%d wins (%.1f%% win rate)" % (self._wins, total, rate))

    def _loop(self):
        
        while True:
            
            gs = self._game.read_state()
            
            if gs is None:
                
                self.log.warning("game process ended unexpectedly")
                break

            if gs.state == "playing":
                
                action = self._strategy.choose_action(gs)
                self._game.send(action)
                self._steps += 1
                
                self.log.debug("step %d - action: %s - pos: %s - hp: %d" % (
                    self._steps, action, gs.player_pos, gs.hp
                    )
                )

                if self._steps > Config.agent.max_steps:
                    
                    self._losses += 1
                    self._steps = 0
                    total = self._wins + self._losses
                    rate = self._wins / total * 100
                    
                    self.log.warning("stuck after %d steps on maze %d - requesting new maze (win rate: %.1f%%)" % (
                        Config.agent.max_steps,
                        total, 
                        rate
                        )
                    )
                    
                    self._game.send("new")

            elif gs.state == "won":
                
                self._wins += 1
                self._steps = 0
                total = self._wins + self._losses
                rate = self._wins / total * 100
                
                self.log.info("WON maze %d in %d moves (win rate: %.1f%% - %d/%d)" % (
                    total, 
                    gs.moves, 
                    rate, 
                    self._wins, 
                    total
                    )
                )

                self._game.send("new")

            elif gs.state == "dead":
                
                self._losses += 1
                self._steps = 0
                total = self._wins + self._losses
                rate = self._wins / total * 100
                
                self.log.warning("DIED on maze %d after %d moves - requesting new maze (win rate: %.1f%% - %d/%d)" % (
                    total, 
                    gs.moves, 
                    rate, 
                    self._wins,
                    total
                    )
                )
                
                self._game.send("new")
            
            total = self._wins + self._losses
            
            if total >= Config.agent.max_mazes:
                
                rate = self._wins / total * 100
                
                self.log.info("reached %d mazes limit - %d wins, %d losses (%.1f%% win rate)" % (
                    Config.agent.max_mazes, 
                    self._wins,
                    self._losses, 
                    rate
                    )
                )
                
                self._game.send("quit")
                break
