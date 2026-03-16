import sys
import logging

from config import Config
from obj import GameProcess


class RLPlayer:

    _actions = ["up", "down", "left", "right", "skip"]

    def __init__(self):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self._exe = Config.root_dir / Config.agent.exe_name

    def run(self):
        
        from training import Trainer

        if self._exe.exists() == False:
            
            self.log.error("executable not found: %s" % (self._exe))
            
            sys.exit(1)

        trainer = Trainer()
        trainer.load_model("best.pt")
        self.log.info("loaded trained model - starting RL play")

        game = GameProcess(self._exe)
        wins = 0
        losses = 0
        skips = 0

        try:
            
            while True:
                
                gs = game.read_state()
                
                if gs is None:
                    
                    self.log.warning("game process ended")
                    break

                if gs.state == "playing":
                    
                    action_idx = trainer.predict(gs.to_observation())
                    action = self._actions[action_idx]
                    
                    if action == "skip":
                        
                        skips += 1
                        
                        self.log.info("SKIP #%d at move %d" % (
                            skips, 
                            gs.moves
                            )
                        )
                        
                        game.send("new")
                        continue
                    
                    game.send(action)
                    
                    self.log.debug("action: %s (index: %d)" % (action, action_idx))

                elif gs.state == "won":
                    
                    wins += 1
                    played = wins + losses
                    rate = wins / played * 100
                    
                    self.log.info("WIN #%d in %d moves (played: %d/%d, skips: %d, win rate: %.1f%%)" % (
                        wins, 
                        gs.moves,
                        played, 
                        Config.agent.
                        max_mazes, 
                        skips, 
                        rate
                        )
                    )
                    
                    if played >= Config.agent.max_mazes:
                        
                        game.send("quit")
                        break
                    
                    game.send("new")

                elif gs.state == "dead":
                    
                    losses += 1
                    played = wins + losses
                    rate = wins / played * 100
                    
                    self.log.warning("DIED #%d after %d moves (played: %d/%d, skips: %d, win rate: %.1f%%)" % (
                        losses,
                        gs.moves, 
                        played,
                        Config.agent.max_mazes, 
                        skips, 
                        rate
                        )
                    )
                    
                    if played >= Config.agent.max_mazes:
                        
                        game.send("quit")
                        break
                    
                    game.send("new")

        except (BrokenPipeError, KeyboardInterrupt):
            
            self.log.warning("interrupted")
            
        except Exception:
            
            self.log.exception("unexpected error during RL play")
            
        finally:
            
            game.close()
            
            played = wins + losses
            rate = wins / max(played, 1) * 100
            
            self.log.info("RL player finished - %d/%d wins (%.1f%% win rate) - %d skips" % (
                wins, 
                played,
                rate, 
                skips
                )
            )
