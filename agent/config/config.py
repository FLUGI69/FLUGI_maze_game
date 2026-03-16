from pathlib import Path

class Config(object):

    root_dir = Path(__file__).resolve().parent.parent.parent

    class maze:
        width    = 41
        height   = 25
        channels = 6

    class agent:

        max_mazes    = 1000
        max_steps    = 800
        exe_name     = "maze_game.exe"

    class pathfinder:
        trap_penalty = 20

    class difficulty:
        trap_damage = 2

    class player:
        max_hp = 3

    class training:
        episodes       = 1000
        gamma          = 0.99
        learning_rate  = 0.001
        epsilon_start  = 1.0
        epsilon_end    = 0.05
        epsilon_decay  = 0.995
        batch_size     = 128
        memory_size    = 50000
        model_dir      = "models"
        target_sync    = 10
        max_steps      = 2000
        optimize_interval = 4
        good_skip_reward  = 2.0
        bad_skip_reward   = -30.0

    class chart:
        update_interval = 10
        rolling_window  = 50
        save_path       = "training_chart.png"

    class log:
        level  = "INFO"
        format = "[%(levelname)s] %(name)s - %(message)s"
