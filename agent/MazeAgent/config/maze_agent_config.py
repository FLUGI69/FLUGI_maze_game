import typing as t
import logging

from utils.dataclass import DataclassBaseModel
from utils.dc.agent_stats import AgentStats
from utils.process_manager import ProcessManager

class MazeAgentConfig(DataclassBaseModel):

    import_name: str = ""

    logger: logging.Logger = None

    debug: bool = True

    config: dict | DataclassBaseModel | type = None

    exe_name: str = "maze_game.exe"
    max_mazes: int = 50000
    max_steps: int = 700
    headless: bool = True

    agent_stats: AgentStats = None
    
    process_manager: ProcessManager = None

    # supervised learning (CNN)
    cnn_channels: int = 6
    cnn_max_samples: int = 500000
    cnn_data_file: str = "models/cnn_data.pkl"
    cnn_model_file: str = "models/cnn_maze_policy.pt"
    cnn_train_every: int = 500
    cnn_min_samples: int = 100
    cnn_batch_size: int = 64
    cnn_cores_per_sm: dict[tuple[int, int], int] = None

    # reinforcement learning (DQN)
    dqn_actions: list[str] = None
    dqn_file: str = "models/dqn_agent.pt"
    
    # trained model
    pretrained_model: bool = False

    def set_logger(self) -> logging.Logger:

        self.logger = logging.getLogger(self.logger.name if self.logger is not None else "MazeAgent")
    
    def __post_init__(self):

        self.logger = self.logger if self.logger is not None else logging.getLogger("MazeAgent")



