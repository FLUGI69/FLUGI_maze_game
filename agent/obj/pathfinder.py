import heapq
import logging

from config import Config


class Pathfinder:

    _directions = [(0, -1, "up"), (0, 1, "down"), (-1, 0, "left"), (1, 0, "right")]

    def __init__(self):
        
        self.log = logging.getLogger(self.__class__.__name__)

    def find_direction(self, walls, start, goals, traps, width, height):
        """Find first step direction toward nearest goal (A* with trap penalty).
        walls: 1D numpy array where 1.0 = wall, 0.0 = path."""

        if len(goals) == 0:
            
            self.log.debug("no goals provided")
            return None

        trap_set = frozenset(traps)
        goal_set = frozenset(goals)

        heap = [(0, start[0], start[1], None)]
        visited = set()

        while heap:
            
            cost, x, y, first_dir = heapq.heappop(heap)

            if (x, y) in visited:
                continue
            
            visited.add((x, y))

            if (x, y) in goal_set:
                
                self.log.debug("path found: %s → (%d, %d) cost=%.1f" % (first_dir, x, y, cost))
                
                return first_dir

            for dx, dy, direction in self._directions:
                
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    
                    if walls[ny * width + nx] < 0.5:
                        
                        penalty = Config.pathfinder.trap_penalty if (nx, ny) in trap_set else 0
                        new_dir = first_dir if first_dir else direction
                        
                        heapq.heappush(heap, (cost + 1 + penalty, nx, ny, new_dir))

        self.log.debug("no path found from %s to any of %d goals" % (start, len(goals)))
        
        return None

    def find_path(self, 
        walls, 
        start,
        goals, 
        traps, 
        width, 
        height
        ):
        """Find full path (list of (x,y)) from start to nearest goal.
        Returns None if no path exists."""

        if len(goals) == 0:
            return None

        trap_set = frozenset(traps)
        goal_set = frozenset(goals)

        heap = [(0, start[0], start[1])]
        came_from = {}
        best_cost = {(start[0], start[1]): 0}

        while heap:
            
            cost, x, y = heapq.heappop(heap)

            if cost > best_cost.get((x, y), float("inf")):
                continue

            if (x, y) in goal_set:
                
                path = []
                pos = (x, y)
                
                while pos != (start[0], start[1]):
                    
                    path.append(pos)
                    pos = came_from[pos]
                    
                path.reverse()
                
                return path

            for dx, dy, _ in self._directions:
                
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < width and 0 <= ny < height:
                    
                    if walls[ny * width + nx] < 0.5:
                        
                        penalty = Config.pathfinder.trap_penalty if (nx, ny) in trap_set else 0
                        new_cost = cost + 1 + penalty
                        
                        if new_cost < best_cost.get((nx, ny), float("inf")):
                            
                            best_cost[(nx, ny)] = new_cost
                            came_from[(nx, ny)] = (x, y)
                            
                            heapq.heappush(heap, (new_cost, nx, ny))

        return None

    def check_survivability(self,
        walls, 
        start, 
        coins, 
        shields, 
        traps,
        exit_pos, 
        hp, 
        has_shield, 
        width, 
        height
        ):
        """Simulate the pathfinder strategy to check if the maze is completable.
        Returns True if a greedy pathfinder-like agent would survive."""

        pos = start
        remaining_coins = set(coins)
        remaining_shields = set(shields)
        active_traps = set(traps)
        current_hp = hp
        current_shield = has_shield
        trap_damage = Config.difficulty.trap_damage

        for _ in range(len(coins) + len(shields) + 2):
            
            if not remaining_coins:
                break

            # Low HP without shield → try to grab a shield first
            
            if current_hp <= trap_damage and not current_shield and remaining_shields:
                
                path = self.find_path(
                    walls,
                    pos, 
                    list(remaining_shields),
                    list(active_traps),
                    width, 
                    height
                )
                
                if path:
                    
                    pos, current_hp, current_shield = self._walk(
                        path, 
                        current_hp, 
                        current_shield,
                        active_traps, 
                        remaining_shields, 
                        remaining_coins, 
                        trap_damage
                    )
                    
                    if current_hp <= 0:
                        return False
                    
                    continue

            # Go to nearest coin
            path = self.find_path(
                walls, 
                pos, 
                list(remaining_coins),
                list(active_traps), 
                width, 
                height
            )
            
            if path is None:
                return False

            pos, current_hp, current_shield = self._walk(
                path, 
                current_hp, 
                current_shield,
                active_traps, 
                remaining_shields, 
                remaining_coins, 
                trap_damage
            )
            
            if current_hp <= 0:
                return False

        if remaining_coins:
            return False

        # Head to exit
        path = self.find_path(
            walls,
            pos, [exit_pos],
            list(active_traps),
            width,
            height
        )
        
        if path is None:
            
            return False

        pos, current_hp, current_shield = self._walk(
            path, 
            current_hp, 
            current_shield,
            active_traps,
            remaining_shields,
            remaining_coins,
            trap_damage
        )

        return current_hp > 0

    @staticmethod
    def _walk(path, 
        hp, 
        shield, 
        active_traps, 
        remaining_shields,
        remaining_coins, 
        trap_damage
        ):
        """Walk along a path, processing traps/shields/coins. Returns (pos, hp, shield)."""

        for step in path:
            
            if step in active_traps:
                
                if shield:
                    
                    shield = False
                    
                else:
                    
                    hp -= trap_damage
                    
                active_traps.discard(step)
                
                if hp <= 0:
                    
                    return step, hp, shield

            if step in remaining_shields:
                
                remaining_shields.discard(step)
                shield = True

            if step in remaining_coins:
                
                remaining_coins.discard(step)

        return path[-1], hp, shield
