import numpy as np
import pytest
from entropy_oracle.baselines import BASELINE_NAMES, build_baseline


def training(alphabet=3, n=240, width=8):
    rng = np.random.default_rng(42)
    seq = rng.integers(alphabet, size=n + width)
    windows = np.lib.stride_tricks.sliding_window_view(seq, width + 1)
    return windows[:, :-1].copy(), windows[:, -1].copy()


@pytest.mark.parametrize("name", BASELINE_NAMES)
def test_probabilities_and_frozen_predictions(name):
    X, y = training()
    model = build_baseline(name, 3, window=8, seed=10).fit(X, y)
    probes = X[:15].copy()
    first = model.predict_proba(probes)
    assert first.shape == (15, 3)
    assert np.all(first > 0)
    np.testing.assert_allclose(first.sum(axis=1), 1, atol=1e-7)
    model.predict_proba(X[100:])
    X[:] = 2
    y[:] = 2
    np.testing.assert_allclose(model.predict_proba(probes), first)


@pytest.mark.parametrize("name", BASELINE_NAMES)
def test_unseen_symbols_and_constant_training(name):
    X = np.zeros((60, 8), dtype=int)
    y = np.zeros(60, dtype=int)
    model = build_baseline(name, 4, window=8).fit(X, y)
    probabilities = model.predict_proba(np.full((3, 8), 3, dtype=int))
    assert probabilities.shape == (3, 4)
    assert np.all(probabilities > 0)
    np.testing.assert_allclose(probabilities.sum(axis=1), 1)


def test_markov_learns_dependency_with_uniform_marginal():
    rng = np.random.default_rng(200)
    seq = np.empty(4000, dtype=int)
    seq[0] = 0
    for i in range(1, len(seq)):
        seq[i] = seq[i - 1] ^ (rng.random() < 0.1)
    windows = np.lib.stride_tricks.sliding_window_view(seq, 9)
    X, y = windows[:, :-1], windows[:, -1]
    model = build_baseline("markov1", 2, window=8).fit(X[:2500], y[:2500])
    assert np.mean(model.predict_proba(X[3000:]).argmax(1) == y[3000:]) > 0.85


def test_ppm_backoff_matches_marginal_for_unseen_context():
    X = np.zeros((40, 8), dtype=int)
    y = np.tile([0, 0, 1, 1], 10)
    model = build_baseline("ppm", 3, window=8).fit(X, y)
    np.testing.assert_allclose(model.predict_proba(np.full((1, 8), 2))[0], model.probs_)
