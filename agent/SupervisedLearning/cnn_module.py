import torch
import torch.nn as nn

class PolicyCNN(nn.Module):

    def __init__(self, channels: int = 6):
        
        super().__init__()

        self.net = nn.Sequential(
            nn.Conv2d(channels, 64, 3, padding = 1),
            nn.ReLU(inplace = True),

            nn.Conv2d(64, 64, 3, padding = 1),
            nn.ReLU(inplace = True),

            nn.AdaptiveAvgPool2d((16, 16)),
            nn.Flatten(),
            nn.Linear(64 * 16 * 16, 256),
            nn.ReLU(inplace = True),

            nn.Linear(256, 4)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)