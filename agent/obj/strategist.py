import logging

from .pathfinder import Pathfinder
from .game_state import GameState

class Strategist:

    def __init__(self):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self._pathfinder = Pathfinder()
        
        self.log.info("strategist initialized")

    def choose_action(self, gs: GameState) -> str:
        
        pf = self._pathfinder.find_direction
        pos = gs.player_pos
        w = gs.walls_array

        if gs.exit_open:
            
            d = pf(w, pos, [gs.exit_pos], gs.traps, gs.width, gs.height)
            
            if d is not None:
                
                self.log.debug("heading to exit - %s" % (d))
                
                return d

        if gs.hp == 1 and gs.has_shield == False and gs.shields:
            
            d = pf(w, pos, gs.shields, gs.traps, gs.width, gs.height)
            
            if d is not None:
                
                self.log.debug("low hp, seeking shield - %s" % (d))
                
                return d

        if gs.coins:
            
            d = pf(w, pos, gs.coins, gs.traps, gs.width, gs.height)
            
            if d is not None:
                
                self.log.debug("collecting coin - %s" % (d))
                
                return d

        self.log.debug("no target found - defaulting to up")
        
        return "up"
