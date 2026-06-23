import torch
import torch.nn as nn
import torch.nn.functional as F


class FeatureEncoder(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int = 64, dropout: float = 0.15):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),

            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),

            nn.Linear(128, latent_dim),
        )

    def forward(self, x):
        z = self.net(x)
        z = F.normalize(z, p=2, dim=1)
        return z


class EncoderClassifier(nn.Module):
    def __init__(
        self,
        input_dim: int,
        latent_dim: int = 64,
        num_classes: int = 22,
        dropout: float = 0.15,
    ):
        super().__init__()
        self.encoder = FeatureEncoder(input_dim, latent_dim, dropout)
        self.classifier = nn.Linear(latent_dim, num_classes)

    def forward(self, x, return_embedding: bool = True):
        z = self.encoder(x)
        logits = self.classifier(z)

        if return_embedding:
            return z, logits

        return logits