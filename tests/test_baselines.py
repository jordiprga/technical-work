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


def _loss_bits(y, probabilities):
    return float(-np.log2(np.maximum(probabilities[np.arange(len(y)), y], 1e-15)).mean())


def test_mlp_restores_validation_checkpoint_before_temporal_drift_overfitting():
    # A controlled train/validation regime change makes further training harm
    # temporal validation. No test set is involved in selecting this checkpoint.
    rng = np.random.default_rng(2001)
    X = rng.integers(0, 2, (400, 8))
    y = X[:, -1].copy()
    X_val = rng.integers(0, 2, (300, 8))
    y_val = 1 - X_val[:, -1]
    model = build_baseline("mlp", 2, window=8, seed=2001, max_epochs=30)
    model.fit(X, y, X_val, y_val)
    losses = [row["val_loss"] for row in model.history]
    assert model.early_stopped_
    assert model.epochs_trained_ < model.max_epochs
    assert model.best_epoch_ < model.epochs_trained_
    restored_loss = _loss_bits(y_val, model.predict_proba(X_val))
    assert restored_loss == pytest.approx(min(losses), abs=1e-10)
    assert restored_loss == pytest.approx(model.best_val_loss_, abs=1e-10)
    assert losses[-1] > restored_loss + .1
    assert model.history[-1]["train_loss"] < model.history[0]["train_loss"]
    assert all(row["train_loss_units"] == row["val_loss_units"] == "bits"
               and not row["includes_l2_penalty"] for row in model.history)


def test_mlp_validation_never_enters_optimizer_and_inference_does_not_update(monkeypatch):
    from sklearn.neural_network import MLPClassifier

    rng = np.random.default_rng(2002)
    X = rng.integers(0, 2, (120, 6))
    y = X[:, -1].copy()
    X_val = rng.integers(0, 2, (75, 6))
    y_val = rng.integers(0, 2, 75)
    calls = []
    original = MLPClassifier.partial_fit

    def record_training(estimator, features, targets, classes=None, **kwargs):
        np.testing.assert_array_equal(features, 2 * X - 1)
        np.testing.assert_array_equal(targets, y)
        np.testing.assert_array_equal(classes, [0, 1])
        calls.append(len(targets))
        return original(estimator, features, targets, classes=classes, **kwargs)

    monkeypatch.setattr(MLPClassifier, "partial_fit", record_training)
    model = build_baseline("mlp", 2, window=6, seed=2002, max_epochs=10)
    model.fit(X, y, X_val, y_val)
    assert len(calls) == model.epochs_trained_
    assert model.validation_used_
    # Save a new inference segment and ensure neither inference nor mutation of
    # caller-owned train/validation arrays changes the fitted checkpoint.
    probes = rng.integers(0, 2, (30, 6))
    first = model.predict_proba(probes)
    weights = [weight.copy() for weight in model.estimator_.coefs_]
    model.predict_proba(rng.integers(0, 2, (40, 6)))
    X[:] = 0
    y[:] = 0
    X_val[:] = 1
    y_val[:] = 1
    np.testing.assert_array_equal(model.predict_proba(probes), first)
    for before, after in zip(weights, model.estimator_.coefs_):
        np.testing.assert_array_equal(before, after)
    assert len(calls) == model.epochs_trained_


def test_mlp_full_alphabet_alignment_with_missing_training_symbol():
    rng = np.random.default_rng(2003)
    X = rng.integers(0, 3, (160, 5))
    y = 2 * rng.integers(0, 2, 160)  # Symbol 1 appears only in validation.
    X_val = rng.integers(0, 3, (60, 5))
    y_val = np.tile([0, 1, 2], 20)
    model = build_baseline("mlp", 3, window=5, seed=2003, max_epochs=8)
    model.fit(X, y, X_val, y_val)
    np.testing.assert_array_equal(model.estimator_.classes_, [0, 1, 2])
    probabilities = model.predict_proba(X_val)
    assert probabilities.shape == (60, 3)
    assert np.all(probabilities > 0)
    np.testing.assert_allclose(probabilities.sum(axis=1), 1)
    assert _loss_bits(y_val, probabilities) == pytest.approx(model.best_val_loss_)


def test_mlp_no_validation_uses_fixed_budget_and_refit_restarts_seed():
    rng = np.random.default_rng(2004)
    X = rng.integers(0, 2, (150, 5))
    y = rng.integers(0, 2, 150)
    model = build_baseline("mlp", 2, window=5, seed=2004, max_epochs=9)
    model.fit(X, y)
    assert not model.validation_used_
    assert not model.early_stopped_
    assert model.best_val_loss_ is None
    assert model.best_epoch_ == model.epochs_trained_ == len(model.history) == 9
    assert all("val_loss" not in row for row in model.history)
    predictions = model.predict_proba(X)
    model.fit(X, y)
    np.testing.assert_array_equal(model.predict_proba(X), predictions)


def test_mlp_constant_training_retains_smoothed_marginal_without_validation_fitting():
    X = np.zeros((40, 5), dtype=int)
    y = np.zeros(40, dtype=int)
    X_val = np.ones((20, 5), dtype=int)
    y_val = np.full(20, 2)
    model = build_baseline("mlp", 3, window=5, seed=2005).fit(X, y, X_val, y_val)
    assert model.constant_
    assert model.epochs_trained_ == 0
    assert not model.validation_used_
    np.testing.assert_allclose(model.predict_proba(X_val), np.tile(model.probs_, (20, 1)))
    assert np.all(model.predict_proba(X_val) > 0)


@pytest.mark.parametrize("only", ["features", "labels"])
def test_mlp_requires_complete_validation_pair(only):
    X = np.zeros((10, 5), dtype=int)
    y = np.arange(10) % 2
    kwargs = {"X_val": X} if only == "features" else {"y_val": y}
    with pytest.raises(ValueError, match="supplied together"):
        build_baseline("mlp", 2, window=5, seed=2006).fit(X, y, **kwargs)
