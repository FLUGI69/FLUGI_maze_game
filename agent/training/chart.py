import logging

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from config import Config


class TrainingChart:

    def __init__(self):
        
        self.log = logging.getLogger(self.__class__.__name__)
        
        self._rewards = []
        self._epsilons = []
        self._wins = []
        self._skips = []
        self._losses = []
        
        self._rolling = Config.chart.rolling_window
        self._closed = False

        plt.ion()
        
        self._fig, self._axes = plt.subplots(2, 2, figsize = (14, 8))
        self._fig.suptitle("FLUGI Maze - DQN Training", fontsize = 14, fontweight = "bold")
        self._fig.canvas.mpl_connect("close_event", self._on_close)

        ax_r, ax_e, ax_w, ax_l = self._axes[0, 0], self._axes[0, 1], self._axes[1, 0], self._axes[1, 1]

        self._ln_reward_raw, = ax_r.plot([], [], alpha = 0.3, color = "royalblue", linewidth = 0.8)
        self._ln_reward_avg, = ax_r.plot([], [], color = "royalblue", linewidth = 2)
        ax_r.set_title("Reward per Episode")
        ax_r.set_xlabel("Episode")
        ax_r.set_ylabel("Reward")
        ax_r.grid(True, alpha = 0.3)

        self._ln_epsilon, = ax_e.plot([], [], color = "darkorange", linewidth = 1.5)
        ax_e.set_title("Epsilon Decay")
        ax_e.set_xlabel("Episode")
        ax_e.set_ylabel("Epsilon")
        ax_e.grid(True, alpha = 0.3)

        self._ln_winrate, = ax_w.plot([], [], color = "seagreen", linewidth = 2, label = "Win Rate")
        self._ln_skiprate, = ax_w.plot([], [], color = "darkorchid", linewidth = 2, linestyle = "--", label = "Skip Rate")
        ax_w.set_title("Win & Skip Rate (rolling %d)" % (self._rolling))
        ax_w.set_xlabel("Episode")
        ax_w.set_ylabel("Rate")
        ax_w.set_ylim(-0.05, 1.05)
        ax_w.legend(loc = "upper left", fontsize = 8)
        ax_w.grid(True, alpha = 0.3)

        self._ln_loss_raw, = ax_l.plot([], [], alpha = 0.3, color = "crimson", linewidth = 0.8)
        self._ln_loss_avg, = ax_l.plot([], [], color = "crimson", linewidth = 2)
        ax_l.set_title("Training Loss")
        ax_l.set_xlabel("Episode")
        ax_l.set_ylabel("Loss")
        ax_l.grid(True, alpha = 0.3)

        self._fig.tight_layout(rect = [0, 0, 1, 0.95])
        self._fig.canvas.draw()
        self._fig.canvas.flush_events()
        plt.show(block = False)

        self.log.info("training chart initialized")

    def _on_close(self, event):
        
        self._closed = True
        self.log.info("chart window closed - stopping training")

    @property
    def stopped(self) -> bool:
        
        return self._closed

    def pump(self):
        
        if self._closed == False:
            self._fig.canvas.flush_events()

    def update(self, episode: int, reward: float, epsilon: float, won: bool, loss: float = None, skipped: bool = False):
        
        self._rewards.append(reward)
        self._epsilons.append(epsilon)
        self._wins.append(1.0 if won == True else 0.0)
        self._skips.append(1.0 if skipped == True else 0.0)
        
        if loss is not None:
            
            self._losses.append(loss)

        if self._closed == True:
            return

        self._draw()

    def _draw(self):
        
        n = len(self._rewards)
        eps = np.arange(1, n + 1)

        self._ln_reward_raw.set_data(eps, self._rewards)

        if n >= self._rolling:
            
            avg = np.convolve(self._rewards, np.ones(self._rolling) / self._rolling, mode = "valid")
            self._ln_reward_avg.set_data(np.arange(self._rolling, n + 1), avg)

        ax_r = self._axes[0, 0]
        ax_r.set_xlim(1, max(n, 2))
        
        if n > 0:
            
            pad = max(abs(min(self._rewards)), abs(max(self._rewards))) * 0.05 + 1
            ax_r.set_ylim(min(self._rewards) - pad, max(self._rewards) + pad)

        self._ln_epsilon.set_data(eps, self._epsilons)
        ax_e = self._axes[0, 1]
        ax_e.set_xlim(1, max(n, 2))
        ax_e.set_ylim(0, 1.05)

        if n >= self._rolling:
            rate = np.convolve(self._wins, np.ones(self._rolling) / self._rolling, mode = "valid")
            self._ln_winrate.set_data(np.arange(self._rolling, n + 1), rate)
            skip_rate = np.convolve(self._skips, np.ones(self._rolling) / self._rolling, mode = "valid")
            self._ln_skiprate.set_data(np.arange(self._rolling, n + 1), skip_rate)
            self._axes[1, 0].set_xlim(self._rolling, max(n, self._rolling + 1))

        nl = len(self._losses)

        if nl > 0:
            
            loss_eps = np.arange(1, nl + 1)
            self._ln_loss_raw.set_data(loss_eps, self._losses)

            if nl >= self._rolling:
                
                avg = np.convolve(self._losses, np.ones(self._rolling) / self._rolling, mode = "valid")
                self._ln_loss_avg.set_data(np.arange(self._rolling, nl + 1), avg)

            ax_l = self._axes[1, 1]
            ax_l.set_xlim(1, max(nl, 2))
            ax_l.set_ylim(0, max(self._losses) * 1.1 + 0.001)

        self._fig.canvas.draw_idle()
        self._fig.canvas.flush_events()

    def save(self):
        
        path = Config.root_dir / Config.chart.save_path

        try:

            if self._closed == True:
                
                self._save_offline(path)
                
            else:
                self._fig.savefig(str(path), dpi = 150, bbox_inches = "tight")

            self.log.info("chart saved to %s" % (path))

        except Exception as e:
            
            self.log.warning("chart save failed: %s" % (e))

    def _save_offline(self, path):

        fig, axes = plt.subplots(2, 2, figsize = (14, 8))
        fig.suptitle("FLUGI Maze - DQN Training", fontsize = 14, fontweight = "bold")

        n = len(self._rewards)
        eps = np.arange(1, n + 1)

        ax = axes[0, 0]
        ax.plot(eps, self._rewards, alpha = 0.3, color = "royalblue", linewidth = 0.8)

        if n >= self._rolling:
            
            avg = np.convolve(self._rewards, np.ones(self._rolling) / self._rolling, mode = "valid")
            ax.plot(np.arange(self._rolling, n + 1), avg, color = "royalblue", linewidth = 2)

        ax.set_title("Reward per Episode")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Reward")
        ax.grid(True, alpha = 0.3)

        ax = axes[0, 1]
        ax.plot(eps, self._epsilons, color = "darkorange", linewidth = 1.5)
        ax.set_title("Epsilon Decay")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Epsilon")
        ax.grid(True, alpha = 0.3)

        ax = axes[1, 0]

        if n >= self._rolling:
            
            rate = np.convolve(self._wins, np.ones(self._rolling) / self._rolling, mode = "valid")
            ax.plot(np.arange(self._rolling, n + 1), rate, color = "seagreen", linewidth = 2, label = "Win Rate")
            skip_rate = np.convolve(self._skips, np.ones(self._rolling) / self._rolling, mode = "valid")
            ax.plot(np.arange(self._rolling, n + 1), skip_rate, color = "darkorchid", linewidth = 2, linestyle = "--", label = "Skip Rate")
            ax.legend(loc = "upper left", fontsize = 8)

        ax.set_title("Win & Skip Rate (rolling %d)" % (self._rolling))
        ax.set_xlabel("Episode")
        ax.set_ylabel("Rate")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha = 0.3)

        ax = axes[1, 1]

        if len(self._losses) > 0:
            
            nl = len(self._losses)
            loss_eps = np.arange(1, nl + 1)
            ax.plot(loss_eps, self._losses, alpha = 0.3, color = "crimson", linewidth = 0.8)

            if nl >= self._rolling:
                avg = np.convolve(self._losses, np.ones(self._rolling) / self._rolling, mode = "valid")
                ax.plot(np.arange(self._rolling, nl + 1), avg, color = "crimson", linewidth = 2)

        ax.set_title("Training Loss")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Loss")
        ax.grid(True, alpha = 0.3)

        fig.tight_layout(rect = [0, 0, 1, 0.95])
        fig.savefig(str(path), dpi = 150, bbox_inches = "tight")
        plt.close(fig)

    def close(self):
        
        try:
            
            plt.ioff()
            plt.close(self._fig)
            
        except Exception:
            pass
        
        self.log.debug("chart closed")
