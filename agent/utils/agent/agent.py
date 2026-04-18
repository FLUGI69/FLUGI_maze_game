import sys

from SupervisedLearning import SupervisedLearning
from ReinforcementLearning import ReinforcementLearning
from TrainedModel import TrainedModelPlayer
from MazeAgent import MazeAgent

if "--dqn" in sys.argv:

    class Agent(ReinforcementLearning):

        def run(self, **kwargs) -> None:

            return super().run(**kwargs)

elif "--cnn" in sys.argv:

    class Agent(SupervisedLearning):

        def run(self, **kwargs) -> None:

            return super().run(**kwargs)


elif "--ai" in sys.argv:

    class Agent(TrainedModelPlayer):

        def run(self, **kwargs) -> None:

            return super().run(**kwargs)
        
else:
    
    class Agent(MazeAgent):

        def run(self, **kwargs) -> None:

            return super().run(**kwargs)

