from pathlib import Path

class Config(object):

    class log:
        
        level = "DEBUG"
        
    class time:

        timezone = "UTC"
        timeformat = "%Y-%m-%d %H:%M:%S"

    class maze:
        
        width = 41
        height = 25
        channels = 6

    class agent:

        max_mazes = 50000
        max_steps = 700
        exe_name = "maze_game.exe"
        headless = True

    class dashboard:

        host = "127.0.0.1"
        port = 8050
        update_ms = 1000
        enabled = True
        max_render_points = 100

    class supervised_learning:

        channels = 6
        max_samples = 550000
        data_file = "models/cnn_data.pkl"
        model_file = "models/cnn_maze_policy.pt"
        train_every = 10000
        min_samples = 1000
        batch_size = 64
        cores_per_sm = {
            (2, 0): 32,  (2, 1): 48,
            (3, 0): 192, (3, 2): 192, (3, 5): 192, (3, 7): 192,
            (5, 0): 128, (5, 2): 128, (5, 3): 128,
            (6, 0): 64,  (6, 1): 128, (6, 2): 128,
            (7, 0): 64,  (7, 2): 64,  (7, 5): 64,
            (8, 0): 64,  (8, 6): 128, (8, 7): 128, (8, 9): 128,
            (9, 0): 128,
            (12, 0): 128, (12, 1): 128,  # Blackwell (RTX 50xx)
        }

    class reinforcement_learning:

        actions = ["up", "down", "left", "right"]
        file = "models/dqn_agent.pt"

    class trained_model:

        pretrained_model = True