import torch
import torch.nn as nn

class DQNNetwork(nn.Module):
    """
    Deep Q-Network.  Feature extractor mirrors ImpossibleCNN.features so
    that pre-trained SL weights can be transferred directly.

    Input : (batch, channels, H, W) float32
    Output: (batch, n_actions)  Q-values
    """

    def __init__(self, channels: int = 6, n_actions: int = 4):

        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(channels, 32, kernel_size = 3, padding = 1),
            nn.ReLU(inplace = True),
            nn.Conv2d(32, 64, kernel_size = 3, padding = 1),
            nn.ReLU(inplace = True),
            nn.Conv2d(64, 64, kernel_size = 3, padding = 1),
            nn.ReLU(inplace = True),
            nn.AdaptiveAvgPool2d((6, 6)),
        )

        self.q_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 36, 256),
            nn.ReLU(inplace = True),
            nn.Linear(256, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.q_head(self.features(x))
