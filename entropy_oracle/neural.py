"""Small causal neural predictors for integer-valued temporal windows.

Only the supplied history is observed.  The sequence readout concatenates encoded
positions rather than discarding all but the last state; this makes finite-window
lag dependencies accessible on modest CPU training budgets.  All training and
epoch selection use train/validation data; predict_proba never updates parameters.
"""
from __future__ import annotations

import copy
import math
import random
from typing import Optional

import numpy as np
import torch
from torch import nn


NEURAL_NAMES = ["gru", "transformer"]


class GRUNet(nn.Module):
    def __init__(self, alphabet_size: int, window: int, hidden: int = 24):
        super().__init__()
        self.embedding = nn.Embedding(alphabet_size, 8)
        self.gru = nn.GRU(8, hidden, batch_first=True)
        self.readout = nn.Sequential(
            nn.Flatten(), nn.Linear(window * hidden, 64), nn.GELU(),
            nn.Linear(64, alphabet_size),
        )

    def encode(self, x):
        return self.gru(self.embedding(x))[0]

    def forward(self, x):
        return self.readout(self.encode(x))


class CausalTransformerNet(nn.Module):
    def __init__(self, alphabet_size: int, window: int, hidden: int = 16):
        super().__init__()
        self.embedding = nn.Embedding(alphabet_size, hidden)
        self.positions = nn.Parameter(torch.randn(1, window, hidden) * 0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=hidden, nhead=2, dim_feedforward=hidden * 2,
            dropout=0.0, activation="gelu", batch_first=True, norm_first=False,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=1,
                                             enable_nested_tensor=False)
        self.register_buffer("causal_mask", torch.triu(
            torch.ones(window, window, dtype=torch.bool), diagonal=1))
        self.readout = nn.Sequential(
            nn.Flatten(), nn.Linear(window * hidden, 64), nn.GELU(),
            nn.Linear(64, alphabet_size),
        )

    def encode(self, x):
        length = x.shape[1]
        z = self.embedding(x) + self.positions[:, :length]
        return self.encoder(z, mask=self.causal_mask[:length, :length])

    def forward(self, x):
        return self.readout(self.encode(x))


class NeuralPredictor:
    """PyTorch sklearn-style predictor with deterministic seeded minibatches.

    A validation-selected best checkpoint is restored after training.  Validation
    statistics therefore are selection statistics, not independent evidence.
    ``history`` losses are in bits/symbol and accuracy is top-one correctness.
    GPU is used automatically when available, unless device='cpu' is supplied.
    """

    def __init__(self, name: str, alphabet_size: int, window: int = 32,
                 seed: int = 0, epochs: int = 15, batch_size: int = 256,
                 learning_rate: float = 0.002, device: Optional[str] = None,
                 patience: int = 6, **kwargs):
        if name not in NEURAL_NAMES:
            raise ValueError(f"Unknown neural predictor: {name}")
        if alphabet_size < 2 or window < 1 or epochs < 1:
            raise ValueError("alphabet_size>=2, window>=1 and epochs>=1 required")
        self.name = name
        self.alphabet_size = alphabet_size
        self.window = window
        self.seed = int(seed)
        self.epochs = int(epochs)
        self.batch_size = int(batch_size)
        self.learning_rate = learning_rate
        self.patience = int(patience)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.history = []
        self.best_epoch = None
        self.model = None

    def _check_x(self, X):
        x = np.asarray(X)
        if x.ndim != 2 or x.shape[1] != self.window:
            raise ValueError(f"Expected shape (n,{self.window}), got {x.shape}")
        if np.any(x < 0) or np.any(x >= self.alphabet_size):
            raise ValueError("History symbols outside declared alphabet")
        if not np.issubdtype(x.dtype, np.integer):
            raise ValueError("History must contain integer symbols")
        return np.ascontiguousarray(x, dtype=np.int64)

    @torch.no_grad()
    def _evaluate(self, x, y):
        self.model.eval()
        total_loss, total_correct = 0.0, 0
        for start in range(0, len(x), self.batch_size):
            xb = x[start:start + self.batch_size].to(self.device)
            yb = y[start:start + self.batch_size].to(self.device)
            logits = self.model(xb)
            total_loss += nn.functional.cross_entropy(logits, yb, reduction="sum").item()
            total_correct += (logits.argmax(1) == yb).sum().item()
        return total_loss / len(y) / math.log(2), total_correct / len(y)

    def fit(self, X, y, X_val=None, y_val=None):
        torch.set_num_threads(1)
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        random.seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        # CPU execution is deterministic.  This requests deterministic kernels
        # for CUDA too, while warning if a backend cannot provide one.
        torch.use_deterministic_algorithms(True, warn_only=True)
        x = torch.from_numpy(self._check_x(X).copy())
        target = np.asarray(y, dtype=np.int64)
        if len(target) != len(x) or len(x) == 0:
            raise ValueError("Training X/y must be nonempty with equal lengths")
        if np.any(target < 0) or np.any(target >= self.alphabet_size):
            raise ValueError("Training labels outside declared alphabet")
        labels = torch.from_numpy(target.copy())
        if (X_val is None) != (y_val is None):
            raise ValueError("Supply both X_val and y_val")
        val_x = torch.from_numpy(self._check_x(X_val).copy()) if X_val is not None else None
        val_y = torch.from_numpy(np.asarray(y_val, dtype=np.int64).copy()) if y_val is not None else None
        if val_x is not None and (len(val_x) != len(val_y) or len(val_x) == 0):
            raise ValueError("Validation X/y must be nonempty with equal lengths")
        network = GRUNet if self.name == "gru" else CausalTransformerNet
        self.model = network(self.alphabet_size, self.window).to(self.device)
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.learning_rate,
                                      weight_decay=1e-4)
        generator = torch.Generator().manual_seed(self.seed)
        self.history = []
        best_loss, stale, best_state = math.inf, 0, None
        for epoch in range(1, self.epochs + 1):
            self.model.train()
            permutation = torch.randperm(len(x), generator=generator)
            loss_sum, correct = 0.0, 0
            for start in range(0, len(x), self.batch_size):
                ids = permutation[start:start + self.batch_size]
                xb, yb = x[ids].to(self.device), labels[ids].to(self.device)
                optimizer.zero_grad(set_to_none=True)
                logits = self.model(xb)
                loss = nn.functional.cross_entropy(logits, yb)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                loss_sum += loss.item() * len(ids)
                correct += (logits.argmax(1) == yb).sum().item()
            row = {"epoch": epoch, "train_loss": loss_sum / len(x) / math.log(2),
                   "train_accuracy": correct / len(x)}
            if val_x is not None:
                row["val_loss"], row["val_accuracy"] = self._evaluate(val_x, val_y)
                criterion = row["val_loss"]
            else:
                criterion = row["train_loss"]
            self.history.append(row)
            if criterion < best_loss - 1e-5:
                best_loss, stale = criterion, 0
                best_state = copy.deepcopy(self.model.state_dict())
                self.best_epoch = epoch
            else:
                stale += 1
            if val_x is not None and self.patience > 0 and stale >= self.patience:
                break
        self.model.load_state_dict(best_state)
        self.model.eval()
        return self

    @torch.no_grad()
    def predict_proba(self, X):
        if self.model is None:
            raise RuntimeError("Call fit before predict_proba")
        x = torch.from_numpy(self._check_x(X).copy())
        if len(x) == 0:
            return np.empty((0, self.alphabet_size), dtype=np.float64)
        self.model.eval()
        predictions = []
        for start in range(0, len(x), self.batch_size):
            logits = self.model(x[start:start + self.batch_size].to(self.device))
            predictions.append(torch.softmax(logits, dim=1).cpu().numpy())
        p = np.concatenate(predictions).astype(np.float64)
        return p / p.sum(axis=1, keepdims=True)


def build_neural(name, alphabet_size, window=32, seed=0, epochs=15, **kwargs):
    return NeuralPredictor(name=name, alphabet_size=alphabet_size, window=window,
                           seed=seed, epochs=epochs, **kwargs)
