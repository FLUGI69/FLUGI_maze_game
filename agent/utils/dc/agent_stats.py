from threading import Lock

from utils.dataclass import DataclassBaseModel

class EpisodeResult(DataclassBaseModel):

    maze_id: int = 0
    won: bool = False
    died: bool = False
    steps: int = 0
    coins_collected: int = 0
    coins_possible: int = 10
    hp_lost: int = 0
    shields_picked: int = 0
    epsilon: float = 0.0
    episode_reward: float = 0.0

class AgentStats:

    def __init__(self, 
        shared_list = None, 
        manager = None, 
        max_render_points: int = 400
        ):

        self._manager = manager 
        
        self.episodes = shared_list if shared_list is not None else []
        
        self._lock = Lock()
        
        self._max_render_points = max_render_points

    def add(self, ep: EpisodeResult) -> None:

        with self._lock:
            self.episodes.append(ep)

    def snapshot(self) -> dict:

        with self._lock:
            eps = list(self.episodes)

        n = len(eps)

        if n == 0:
            return {}

        ids = list(range(1, n + 1))

        win_rate = [sum(e.won  for e in eps[:i+1]) / (i+1) * 100 for i in range(n)]
        death_cum = [sum(e.died for e in eps[:i+1]) for i in range(n)]
        steps_pct = [e.steps / 700 * 100 for e in eps]
        coins_pct = [e.coins_collected / max(e.coins_possible, 1) * 100 for e in eps]
        hp_pct = [e.hp_lost / 3 * 100 for e in eps]
        shields_pct = [e.shields_picked / 2 * 100 for e in eps]
        epsilon = [e.epsilon for e in eps]
        reward = [e.episode_reward for e in eps]

        result = dict(
            ids = ids,
            win_rate = win_rate, win_rate_avg = self._rolling(win_rate),
            death_cum = death_cum, death_cum_avg = self._rolling(death_cum),
            steps_pct = steps_pct, steps_pct_avg = self._rolling(steps_pct),
            coins_pct = coins_pct, coins_pct_avg = self._rolling(coins_pct),
            hp_pct = hp_pct, hp_pct_avg = self._rolling(hp_pct),
            shields_pct = shields_pct, shields_pct_avg = self._rolling(shields_pct),
            epsilon = epsilon, epsilon_avg = self._rolling(epsilon),
            reward_cum = reward, reward_cum_avg = self._rolling(reward),
        )

        if n > self._max_render_points:
            result = self._downsample(result, self._max_render_points)

        result["total"] = n

        return result

    @staticmethod
    def _downsample(data: dict, max_points: int) -> dict:
        """Keep evenly-spaced indices so every series stays in sync."""
        
        n = len(data["ids"])
        indices = [round(i * (n - 1) / (max_points - 1)) for i in range(max_points)]
        
        return {k: [v[i] for i in indices] for k, v in data.items()}

    @staticmethod
    def _rolling(data: list, w: int = 20) -> list:

        out = []

        for i in range(len(data)):
            
            window = data[max(0, i - w + 1): i + 1]
            out.append(sum(window) / len(window))

        return out
