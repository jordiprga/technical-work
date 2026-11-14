import math

import numpy as np
import pytest

from entropy_oracle.statistics import (
    circular_block_interval,
    iid_clopper_pearson,
    martingale_mean_interval,
    paired_comparison,
    score_predictions,
)


def test_metrics_distinguish_confidence_success_and_logloss():
    y = np.array([0, 1, 1, 0])
    p = np.array([[.9, .1], [.6, .4], [.2, .8], [.4, .6]])
    result = score_predictions(y, p, bootstrap=0)
    assert result["accuracy"] == .5
    assert result["guess_probability_model"] == pytest.approx(.725)
    assert result["log_loss_bits"] == pytest.approx(-np.log2([.9, .4, .8, .4]).mean())
    assert result["empirical_predictor_surprisal_bits"] == 1
    assert result["log_loss_bits"] != result["empirical_predictor_surprisal_bits"]


def test_martingale_radius_and_paired_range():
    observations = np.tile([0., 1.], 100)
    lo, hi = martingale_mean_interval(observations)
    radius = math.sqrt(math.log(40) / 400)
    assert lo == pytest.approx(.5 - radius)
    assert hi == pytest.approx(.5 + radius)
    paired_lo, paired_hi = martingale_mean_interval(observations * 2 - 1, lower=-1, upper=1)
    assert paired_lo == pytest.approx(-2 * radius)
    assert paired_hi == pytest.approx(2 * radius)


def test_paired_scores_use_same_positions():
    y = np.array([0, 0, 1, 1] * 100)
    a = np.eye(2)[y] * .8 + .1
    b = np.tile([.6, .4], (len(y), 1))
    comparison = paired_comparison(y, a, b, bootstrap=30)
    assert comparison["delta_accuracy"] == .5
    assert comparison["ci_low"] > 0
    same = paired_comparison(y, a, a, bootstrap=30)
    assert same["delta_accuracy"] == 0
    assert same["bootstrap_ci_low"] == same["bootstrap_ci_high"] == 0


def test_bootstrap_reproducible_and_preserves_constant_sequence():
    x = np.random.default_rng(0).normal(size=300)
    assert circular_block_interval(x, seed=42, bootstrap=40) == circular_block_interval(x, seed=42, bootstrap=40)
    assert circular_block_interval(np.ones(100), bootstrap=40) == (1., 1.)


def test_probability_validation():
    with pytest.raises(ValueError):
        score_predictions(np.array([0]), np.array([[.7, .7]]))
    with pytest.raises(ValueError):
        score_predictions(np.array([2]), np.array([[.5, .5]]))
    with pytest.raises(ValueError):
        score_predictions(np.array([0]), np.array([[np.nan, .5]]))
    with pytest.raises(ValueError):
        martingale_mean_interval(np.array([1.2]))


def test_iid_binomial_boundary_cases():
    assert iid_clopper_pearson(0, 10)[0] == 0
    assert iid_clopper_pearson(10, 10)[1] == 1
    lo, hi = iid_clopper_pearson(5, 10)
    assert lo < .5 < hi


def test_adapted_nonstationary_scores_have_correct_martingale_target():
    # Deliberate dependence: success probability changes with the previous
    # outcome, and an additional deterministic drift changes it over time.
    # This deterministic Monte Carlo sanity check is not a proof of coverage.
    rng = np.random.default_rng(91)
    paths, n = 1500, 180
    previous = np.zeros(paths)
    successes = np.zeros(paths)
    conditional_means = np.zeros(paths)
    for t in range(n):
        probability = .1 + .5 * previous + .15 * t / n
        previous = (rng.random(paths) < probability).astype(float)
        successes += previous
        conditional_means += probability
    radius = math.sqrt(math.log(40) / (2 * n))
    misses = np.mean(np.abs(successes / n - conditional_means / n) > radius)
    assert misses < .05


def test_zero_likelihood_is_reported_as_clipped_not_silently_finite():
    result = score_predictions(np.array([1]), np.array([[1., 0.]]), bootstrap=0)
    assert result["log_loss_clipped_count"] == 1
    assert result["empirical_predictor_surprisal_bits"] is None
    assert result["log_loss_bits"] == pytest.approx(-math.log2(1e-15))
