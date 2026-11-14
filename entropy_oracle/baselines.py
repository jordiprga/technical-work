"""Frozen statistical and sklearn next-symbol predictors.

All probabilities refer to discrete symbols. Contexts contain only past samples,
oldest first. No predictor updates its parameters in ``predict_proba``.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import warnings

import numpy as np
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPClassifier
from threadpoolctl import threadpool_limits

BASELINE_NAMES = ["marginal", *[f"markov{i}" for i in range(1, 6)], "ppm", "lz78", "gb", "rf", "mlp"]


def _validate_xy(X, y=None, alphabet_size=2):
    X = np.asarray(X, dtype=np.int64)
    if X.ndim != 2:
        raise ValueError("X must be a two-dimensional matrix of past-symbol windows")
    if X.size and (X.min() < 0 or X.max() >= alphabet_size):
        raise ValueError("Context symbols are outside the alphabet")
    if y is None:
        return X
    y = np.asarray(y, dtype=np.int64)
    if y.ndim != 1 or len(X) != len(y) or not len(y):
        raise ValueError("y must be nonempty and match X")
    if y.min() < 0 or y.max() >= alphabet_size:
        raise ValueError("Target symbols are outside the alphabet")
    return X, y


class MarginalPredictor:
    """Jeffreys-smoothed empirical marginal distribution (alpha = 1/2)."""
    def __init__(self, alphabet_size=2, window=32, seed=0, alpha=0.5, **kwargs):
        self.alphabet_size = int(alphabet_size)
        self.window = int(window)
        self.seed = int(seed)
        self.alpha = float(alpha)
        if self.alphabet_size < 2 or self.alpha <= 0:
            raise ValueError("Need alphabet_size >= 2 and alpha > 0")
        self.history = []

    def fit(self, X, y, X_val=None, y_val=None):
        _, y = _validate_xy(X, y, self.alphabet_size)
        counts = np.bincount(y, minlength=self.alphabet_size).astype(float)
        self.probs_ = (counts + self.alpha) / (len(y) + self.alpha * self.alphabet_size)
        return self

    def predict_proba(self, X):
        X = _validate_xy(X, alphabet_size=self.alphabet_size)
        return np.tile(self.probs_, (len(X), 1))


class MarkovPredictor(MarginalPredictor):
    """Fixed-order empirical Markov model with a smoothed marginal prior.

    Each observed context has one unit of prior mass distributed according to
    the training marginal. Unseen contexts use that marginal directly.
    """
    def __init__(self, alphabet_size=2, window=32, seed=0, order=1, prior_strength=1.0, **kwargs):
        super().__init__(alphabet_size, window, seed, **kwargs)
        self.order = int(order)
        self.prior_strength = float(prior_strength)
        if self.order < 1 or self.order > window:
            raise ValueError("Markov order must lie between one and window length")

    def fit(self, X, y, X_val=None, y_val=None):
        X, y = _validate_xy(X, y, self.alphabet_size)
        super().fit(X, y)
        counts = defaultdict(lambda: np.zeros(self.alphabet_size, dtype=float))
        for row, target in zip(X[:, -self.order:], y):
            counts[tuple(row)][target] += 1
        self.context_probs_ = {
            key: (count + self.prior_strength * self.probs_) / (count.sum() + self.prior_strength)
            for key, count in counts.items()
        }
        return self

    def predict_proba(self, X):
        X = _validate_xy(X, alphabet_size=self.alphabet_size)
        return np.asarray([self.context_probs_.get(tuple(row), self.probs_) for row in X[:, -self.order:]]).reshape(-1, self.alphabet_size)


class PPMPredictor(MarginalPredictor):
    """Interpolated PPM/Witten-Bell context model, without exclusion.

    At each suffix h, p(.|h) = (counts_h + T_h p(.|suffix(h))) /
    (N_h + T_h), where T_h is the number of distinct symbols observed after h.
    This is a normalized compression probability model, not a normative 90B
    MultiMMC implementation and not the exact PPM-C exclusion convention.
    """
    def __init__(self, alphabet_size=2, window=32, seed=0, max_depth=12, **kwargs):
        super().__init__(alphabet_size, window, seed, **kwargs)
        self.max_depth = min(int(max_depth), int(window))

    def fit(self, X, y, X_val=None, y_val=None):
        X, y = _validate_xy(X, y, self.alphabet_size)
        super().fit(X, y)
        self.context_probs_ = [{}]
        for depth in range(1, min(self.max_depth, X.shape[1]) + 1):
            counts = defaultdict(lambda: np.zeros(self.alphabet_size, dtype=float))
            for row, target in zip(X[:, -depth:], y):
                counts[tuple(row)][target] += 1
            level = {}
            previous = self.context_probs_[-1]
            for key, count in counts.items():
                lower = previous.get(key[1:], self.probs_)
                distinct = np.count_nonzero(count)
                level[key] = (count + distinct * lower) / (count.sum() + distinct)
            self.context_probs_.append(level)
        return self

    def predict_proba(self, X):
        X = _validate_xy(X, alphabet_size=self.alphabet_size)
        out = np.tile(self.probs_, (len(X), 1))
        for index, row in enumerate(X):
            for depth in range(min(len(self.context_probs_) - 1, X.shape[1]), 0, -1):
                probability = self.context_probs_[depth].get(tuple(row[-depth:]))
                if probability is not None:
                    out[index] = probability
                    break
        return out


class LZ78Predictor(MarginalPredictor):
    """Frozen LZ78 phrase-trie predictor with marginal smoothing.

    Training targets are parsed into LZ78 phrases; every visited trie node
    records the next symbol before the phrase terminates. At prediction time,
    use the longest past suffix present in this phrase trie. This is a
    compression-inspired predictor, not a compressed-file entropy estimate or
    an implementation of the SP 800-90B LZ78Y estimator. Fitting assumes y is
    in chronological order; initial context samples are not added to training.
    """
    def fit(self, X, y, X_val=None, y_val=None):
        X, y = _validate_xy(X, y, self.alphabet_size)
        super().fit(X, y)
        self.children_ = [{}]
        self.counts_ = [np.zeros(self.alphabet_size, dtype=float)]
        node = 0
        for target in y:
            target = int(target)
            self.counts_[node][target] += 1
            child = self.children_[node].get(target)
            if child is None:
                self.children_[node][target] = len(self.children_)
                self.children_.append({})
                self.counts_.append(np.zeros(self.alphabet_size, dtype=float))
                node = 0
            else:
                node = child
        self.node_probs_ = [(c + self.probs_) / (c.sum() + 1) for c in self.counts_]
        return self

    def predict_proba(self, X):
        X = _validate_xy(X, alphabet_size=self.alphabet_size)
        out = np.tile(self.probs_, (len(X), 1))
        for i, row in enumerate(X):
            for start in range(len(row)):
                node = 0
                for value in row[start:]:
                    node = self.children_[node].get(int(value))
                    if node is None:
                        break
                if node is not None and self.counts_[node].sum() > 0:
                    out[i] = self.node_probs_[node]
                    break
        return out


class SklearnPredictor(MarginalPredictor):
    """CPU-bounded sklearn classifiers with explicit full-alphabet output.

    MLP uses one-hot categorical lags (signed scalar lags for binary data),
    deterministic Adam, and no internal random validation split. When a caller
    supplies a chronological validation segment, its log-loss selects the MLP
    checkpoint and controls early stopping. Only training examples enter Adam.
    Without validation, the MLP trains for a fixed ``max_epochs`` budget. The
    estimator hyperparameters are fixed before test evaluation.
    """
    def __init__(self, alphabet_size=2, window=32, seed=0, kind="gb",
                 max_epochs=65, patience=6, min_delta=1e-4, **kwargs):
        super().__init__(alphabet_size, window, seed, **kwargs)
        self.kind = kind
        if int(max_epochs) != max_epochs or int(max_epochs) < 1:
            raise ValueError("max_epochs must be a positive integer")
        if int(patience) != patience or int(patience) < 1:
            raise ValueError("patience must be a positive integer")
        if not np.isfinite(min_delta) or min_delta < 0:
            raise ValueError("min_delta must be finite and nonnegative")
        self.max_epochs = int(max_epochs)
        self.patience = int(patience)
        self.min_delta = float(min_delta)
        if kind == "gb":
            self.estimator_ = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15,
                learning_rate=0.1, l2_regularization=1.0, early_stopping=False, random_state=seed)
        elif kind == "rf":
            self.estimator_ = RandomForestClassifier(n_estimators=100, max_depth=14,
                min_samples_leaf=3, n_jobs=1, random_state=seed)
        elif kind == "mlp":
            self.estimator_ = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1,
                learning_rate_init=0.003, batch_size=256, early_stopping=False,
                random_state=seed, alpha=0.01, tol=0,
                n_iter_no_change=self.max_epochs + 1)
        else:
            raise ValueError(f"Unknown sklearn predictor {kind!r}")

    def _features(self, X):
        if self.kind == "mlp":
            if self.alphabet_size == 2:
                return (2.0 * X - 1).astype(np.float32)
            return np.eye(self.alphabet_size, dtype=np.float32)[X].reshape(len(X), -1)
        return X.astype(np.float32)

    def fit(self, X, y, X_val=None, y_val=None):
        X, y = _validate_xy(X, y, self.alphabet_size)
        if (X_val is None) != (y_val is None):
            raise ValueError("X_val and y_val must be supplied together")
        if X_val is not None:
            X_val, y_val = _validate_xy(X_val, y_val, self.alphabet_size)
            if X_val.shape[1] != X.shape[1]:
                raise ValueError("Training and validation windows must have equal width")
        super().fit(X, y)
        self.history = []
        self.fit_warnings_ = []
        self.best_epoch_ = None
        self.best_val_loss_ = None
        self.epochs_trained_ = 0
        self.early_stopped_ = False
        self.constant_ = len(np.unique(y)) == 1
        self.validation_used_ = self.kind == "mlp" and X_val is not None and not self.constant_
        if not self.constant_:
            # Repeated fit calls must start from the same seed, not continue an
            # earlier partial_fit trajectory or retain its optimizer state.
            self.estimator_ = clone(self.estimator_)
            with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as recorded:
                warnings.simplefilter("always", ConvergenceWarning)
                if self.kind == "mlp":
                    self._fit_mlp(X, y, X_val, y_val)
                else:
                    self.estimator_.fit(self._features(X), y)
                self.fit_warnings_ = [str(w.message) for w in recorded]
        return self

    @staticmethod
    def _log_loss_bits(labels, probabilities):
        return float(-np.log2(np.maximum(
            probabilities[np.arange(len(labels)), labels], 1e-15
        )).mean())

    def _fit_mlp(self, X, y, X_val, y_val):
        """Run one training-only Adam epoch at a time, then score frozen weights."""
        features = self._features(X)
        val_features = self._features(X_val) if X_val is not None else None
        self.estimator_.set_params(batch_size=min(256, len(y)))
        classes = np.arange(self.alphabet_size)
        best_estimator = None
        best_loss = float("inf")
        patience_reference = float("inf")
        stale_epochs = 0
        for epoch in range(1, self.max_epochs + 1):
            # Declaring every class also covers alphabet symbols absent in train
            # but present in validation. Their validation labels never train it.
            self.estimator_.partial_fit(features, y, classes=classes)
            train_probs = self._aligned_probabilities(features)
            row = {
                "epoch": epoch,
                "train_loss": self._log_loss_bits(y, train_probs),
                "train_loss_units": "bits",
                "includes_l2_penalty": False,
                "train_accuracy": float(np.mean(train_probs.argmax(axis=1) == y)),
                "optimizer_objective_bits": float(self.estimator_.loss_ / np.log(2.0)),
                "optimizer_objective_includes_l2": True,
            }
            if val_features is not None:
                val_probs = self._aligned_probabilities(val_features)
                val_loss = self._log_loss_bits(y_val, val_probs)
                row.update(val_loss=val_loss, val_loss_units="bits",
                           val_accuracy=float(np.mean(val_probs.argmax(axis=1) == y_val)))
                # Always save the actual minimum. min_delta affects patience,
                # not which checkpoint is ultimately restored.
                if val_loss < best_loss:
                    best_loss = val_loss
                    best_estimator = deepcopy(self.estimator_)
                    self.best_epoch_ = epoch
                    self.best_val_loss_ = val_loss
                if val_loss < patience_reference - self.min_delta:
                    patience_reference = val_loss
                    stale_epochs = 0
                else:
                    stale_epochs += 1
            self.history.append(row)
            self.epochs_trained_ = epoch
            if val_features is not None and stale_epochs >= self.patience:
                self.early_stopped_ = epoch < self.max_epochs
                break
        if best_estimator is not None:
            self.estimator_ = best_estimator
        else:
            self.best_epoch_ = self.epochs_trained_

    def _aligned_probabilities(self, features):
        local = self.estimator_.predict_proba(features)
        full = np.full((len(features), self.alphabet_size), 1e-12, dtype=float)
        full[:, self.estimator_.classes_.astype(int)] = local
        full /= full.sum(axis=1, keepdims=True)
        return full

    def predict_proba(self, X):
        X = _validate_xy(X, alphabet_size=self.alphabet_size)
        if self.constant_:
            return np.tile(self.probs_, (len(X), 1))
        if not len(X):
            return np.empty((0, self.alphabet_size))
        with threadpool_limits(limits=1):
            return self._aligned_probabilities(self._features(X))


def build_baseline(name, alphabet_size, window=32, seed=0, **kwargs):
    common = dict(alphabet_size=alphabet_size, window=window, seed=seed, **kwargs)
    if name == "marginal":
        return MarginalPredictor(**common)
    if name.startswith("markov") and name[6:].isdigit():
        return MarkovPredictor(order=int(name[6:]), **common)
    if name == "ppm":
        return PPMPredictor(**common)
    if name == "lz78":
        return LZ78Predictor(**common)
    if name in {"gb", "rf", "mlp"}:
        return SklearnPredictor(kind=name, **common)
    raise ValueError(f"Unknown baseline {name!r}; expected one of {BASELINE_NAMES}")
