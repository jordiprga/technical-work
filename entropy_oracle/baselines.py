"""Frozen statistical and sklearn next-symbol predictors.

All probabilities refer to discrete symbols. Contexts contain only past samples,
oldest first. No predictor updates its parameters in ``predict_proba``.
"""
from __future__ import annotations

from collections import defaultdict
import warnings

import numpy as np
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
    deterministic Adam, and no internal random validation split. The estimator
    hyperparameters are fixed before test evaluation.
    """
    def __init__(self, alphabet_size=2, window=32, seed=0, kind="gb", **kwargs):
        super().__init__(alphabet_size, window, seed, **kwargs)
        self.kind = kind
        if kind == "gb":
            self.estimator_ = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15,
                learning_rate=0.1, l2_regularization=1.0, early_stopping=False, random_state=seed)
        elif kind == "rf":
            self.estimator_ = RandomForestClassifier(n_estimators=100, max_depth=14,
                min_samples_leaf=3, n_jobs=1, random_state=seed)
        elif kind == "mlp":
            self.estimator_ = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=65,
                learning_rate_init=0.003, batch_size=256, early_stopping=False,
                random_state=seed, alpha=0.01, tol=1e-5, n_iter_no_change=15)
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
        super().fit(X, y)
        self.constant_ = len(np.unique(y)) == 1
        if not self.constant_:
            with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as recorded:
                warnings.simplefilter("always", ConvergenceWarning)
                self.estimator_.fit(self._features(X), y)
                self.fit_warnings_ = [str(w.message) for w in recorded]
            if hasattr(self.estimator_, "loss_curve_"):
                self.history = [{"epoch": i + 1, "train_loss": float(loss / np.log(2.0)), "train_loss_units": "bits", "includes_l2_penalty": True}
                                for i, loss in enumerate(self.estimator_.loss_curve_)]
        return self

    def predict_proba(self, X):
        X = _validate_xy(X, alphabet_size=self.alphabet_size)
        if self.constant_:
            return np.tile(self.probs_, (len(X), 1))
        if not len(X):
            return np.empty((0, self.alphabet_size))
        with threadpool_limits(limits=1):
            local = self.estimator_.predict_proba(self._features(X))
        full = np.full((len(X), self.alphabet_size), 1e-12, dtype=float)
        full[:, self.estimator_.classes_.astype(int)] = local
        full /= full.sum(axis=1, keepdims=True)
        return full


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
