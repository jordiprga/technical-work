"""Predictor metrics with explicitly stated inferential targets.

The distribution-free intervals cover the *realized average conditional
success probability* of a predictable predictor, not its accuracy on an
unspecified future stationary population. No independence assumption is made.
Block-bootstrap intervals are exploratory and require stationarity and mixing.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.stats import beta


MARTINGALE_TARGET = (
    "realized test-trajectory average of E[success_t | information before X_t]; "
    "predictor and model selection must be fixed before the final test"
)
BOOTSTRAP_ASSUMPTIONS = (
    "Exploratory circular-block percentile interval; requires a stationary, "
    "sufficiently mixing score process, suitable block length and enough blocks. "
    "Not justified for drift, arbitrary dependence, or very long memory."
)


def _validate_alpha(alpha: float) -> None:
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")


def _validate_predictions(y: np.ndarray, probs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    labels = np.asarray(y)
    q = np.asarray(probs, dtype=np.float64)
    if labels.ndim != 1 or len(labels) == 0:
        raise ValueError("y must be a nonempty one-dimensional sequence")
    if not np.issubdtype(labels.dtype, np.integer):
        if not np.all(np.isfinite(labels)) or not np.all(labels == labels.astype(np.int64)):
            raise ValueError("labels must be integers")
    labels = labels.astype(np.int64)
    if q.ndim != 2 or q.shape[0] != len(labels) or q.shape[1] < 2:
        raise ValueError("probs must have shape (len(y), alphabet_size >= 2)")
    if np.any(~np.isfinite(q)) or np.any(q < 0) or np.any(q > 1 + 1e-8):
        raise ValueError("probabilities must be finite and in [0, 1]")
    sums = q.sum(axis=1)
    if not np.allclose(sums, 1, rtol=1e-6, atol=1e-8):
        raise ValueError("every probability row must sum to one")
    if np.any(labels < 0) or np.any(labels >= q.shape[1]):
        raise ValueError("labels outside declared alphabet")
    # Only remove numerical row-sum drift, not invalid model probabilities.
    return labels, q / sums[:, None]


def martingale_mean_interval(
    observations: np.ndarray,
    alpha: float = 0.05,
    lower: float = 0.0,
    upper: float = 1.0,
) -> tuple[float, float]:
    r"""Two-sided conditional Hoeffding interval for n^-1 sum E[Z_t|F_{t-1}].

    Each Z_t must be adapted and lie in [lower, upper] with deterministic
    endpoints. Conditional Hoeffding's lemma gives radius
    (upper-lower)*sqrt(log(2/alpha)/(2*n)). This remains valid when the unknown
    conditional mean changes over time. It is not a confidence sequence and
    must not be repeatedly inspected under optional stopping.
    """
    _validate_alpha(alpha)
    z = np.asarray(observations, dtype=np.float64)
    if z.ndim != 1 or len(z) == 0 or np.any(~np.isfinite(z)):
        raise ValueError("observations must be a nonempty finite vector")
    if not np.isfinite(lower) or not np.isfinite(upper) or lower >= upper:
        raise ValueError("finite lower < upper required")
    if np.any(z < lower) or np.any(z > upper):
        raise ValueError("observation outside bounded range")
    radius = (upper - lower) * math.sqrt(math.log(2 / alpha) / (2 * len(z)))
    center = float(z.mean())
    return max(lower, center - radius), min(upper, center + radius)


def circular_block_interval(
    observations: np.ndarray,
    alpha: float = 0.05,
    block_length: int = 32,
    seed: int = 0,
    bootstrap: int = 400,
) -> tuple[float, float]:
    """Exploratory percentile CI; see BOOTSTRAP_ASSUMPTIONS.

    Identical indices must be used for paired scores; callers should pass the
    score difference, not subtract two independently bootstrapped intervals.
    """
    _validate_alpha(alpha)
    z = np.asarray(observations, dtype=np.float64)
    if z.ndim != 1 or len(z) == 0 or not np.all(np.isfinite(z)):
        raise ValueError("observations must be a nonempty finite vector")
    if not isinstance(block_length, (int, np.integer)) or not 1 <= block_length <= len(z):
        raise ValueError("block_length must be an integer between 1 and n")
    if not isinstance(bootstrap, (int, np.integer)) or bootstrap < 2:
        raise ValueError("bootstrap must be an integer >= 2")
    rng = np.random.default_rng(seed)
    n = len(z)
    n_blocks = math.ceil(n / block_length)
    offsets = np.arange(block_length)
    means = np.empty(bootstrap)
    # One replicate at a time keeps memory O(n), independent of bootstrap count.
    for b in range(bootstrap):
        starts = rng.integers(0, n, size=n_blocks)
        indices = ((starts[:, None] + offsets) % n).ravel()[:n]
        means[b] = z[indices].mean()
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def iid_clopper_pearson(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact binomial interval ONLY when success indicators are IID Bernoulli.

    IID source samples alone do not generally make overlapping-context
    predictor successes IID. This function is never selected automatically.
    """
    _validate_alpha(alpha)
    if not isinstance(successes, (int, np.integer)) or not isinstance(n, (int, np.integer)):
        raise ValueError("successes and n must be integers")
    if n < 1 or not 0 <= successes <= n:
        raise ValueError("require n >= 1 and 0 <= successes <= n")
    lo = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, n - successes + 1))
    hi = 1.0 if successes == n else float(beta.ppf(1 - alpha / 2, successes + 1, n - successes))
    return lo, hi


def score_predictions(
    y: np.ndarray,
    probs: np.ndarray,
    alpha: float = 0.05,
    block_length: int = 32,
    seed: int = 0,
    bootstrap: int = 400,
) -> dict[str, Any]:
    """Score frozen out-of-sample probability predictions.

    Top-1 ties are broken by the smallest symbol index (numpy argmax).
    Log loss uses a declared 1e-15 floor solely for finite numerical reporting.
    mean(max(q)) is a model confidence, *not* its measured guessing success.
    """
    labels, q = _validate_predictions(y, probs)
    _validate_alpha(alpha)
    predictions = q.argmax(axis=1)
    successes = (predictions == labels).astype(np.float64)
    accuracy = float(successes.mean())
    lo, hi = martingale_mean_interval(successes, alpha)
    true_q = q[np.arange(len(labels)), labels]
    epsilon = 1e-15
    onehot = np.eye(q.shape[1])[labels]
    result: dict[str, Any] = {
        "n_test": len(labels),
        "accuracy": accuracy,
        "log_loss_bits": float(-np.log2(np.maximum(true_q, epsilon)).mean()),
        "log_loss_clip_epsilon": epsilon,
        "log_loss_clipped_count": int(np.count_nonzero(true_q < epsilon)),
        "brier": float(np.square(q - onehot).sum(axis=1).mean()),
        "guess_probability_model": float(q.max(axis=1).mean()),
        "empirical_predictor_surprisal_bits": -math.log2(accuracy) if accuracy else None,
        "success_ci_low": lo,
        "success_ci_high": hi,
        "confidence_level": 1 - alpha,
        "success_ci_method": "two-sided conditional Hoeffding (fixed horizon)",
        "success_ci_target": MARTINGALE_TARGET,
        "bootstrap_ci_low": None,
        "bootstrap_ci_high": None,
        "bootstrap_assumptions": BOOTSTRAP_ASSUMPTIONS,
    }
    if bootstrap:
        length = min(int(block_length), len(labels))
        blo, bhi = circular_block_interval(successes, alpha, length, seed, bootstrap)
        result.update(bootstrap_ci_low=blo, bootstrap_ci_high=bhi, bootstrap_block_length=length)
    return result


def paired_comparison(
    y: np.ndarray,
    probs_a: np.ndarray,
    probs_b: np.ndarray,
    alpha: float = 0.05,
    block_length: int = 32,
    seed: int = 0,
    bootstrap: int = 400,
) -> dict[str, Any]:
    """Paired accuracy difference A - B on identical test positions.

    D_t is in [-1, 1]; the two-sided martingale radius is
    sqrt(2*log(2/alpha)/n). Models/comparison must be selected before test.
    For m exploratory test-selected comparisons, supply alpha/m (Bonferroni)
    or make no family-wise significance claim.
    """
    labels, qa = _validate_predictions(y, probs_a)
    _, qb = _validate_predictions(y, probs_b)
    if qa.shape != qb.shape:
        raise ValueError("paired probability arrays must share the same shape")
    da = (qa.argmax(axis=1) == labels).astype(np.float64)
    db = (qb.argmax(axis=1) == labels).astype(np.float64)
    difference = da - db
    lo, hi = martingale_mean_interval(difference, alpha, lower=-1.0, upper=1.0)
    result: dict[str, Any] = {
        "n_test": len(labels),
        "delta_accuracy": float(difference.mean()),
        "ci_low": lo,
        "ci_high": hi,
        "confidence_level": 1 - alpha,
        "ci_method": "two-sided paired conditional Hoeffding (fixed horizon)",
        "ci_target": "realized average conditional success(A) minus success(B)",
        "bootstrap_ci_low": None,
        "bootstrap_ci_high": None,
        "bootstrap_assumptions": BOOTSTRAP_ASSUMPTIONS,
        "fraction_disagreeing_predictions": float(np.mean(qa.argmax(axis=1) != qb.argmax(axis=1))),
    }
    if bootstrap:
        length = min(int(block_length), len(labels))
        blo, bhi = circular_block_interval(difference, alpha, length, seed, bootstrap)
        result.update(bootstrap_ci_low=blo, bootstrap_ci_high=bhi, bootstrap_block_length=length)
    return result
