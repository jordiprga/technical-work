import numpy as np
import pytest

torch = pytest.importorskip("torch")
from entropy_oracle.neural import CausalTransformerNet, build_neural


@pytest.mark.parametrize("name", ["gru", "transformer"])
def test_neural_probability_and_learning(name):
    rng = np.random.default_rng(7)
    X = rng.integers(0, 2, (384, 8))
    y = X[:, -3]
    model = build_neural(name, 2, window=8, seed=7, epochs=12,
                         batch_size=64, device="cpu")
    model.fit(X[:256], y[:256], X[256:320], y[256:320])
    p = model.predict_proba(X[320:])
    assert p.shape == (64, 2)
    assert np.all(p >= 0)
    np.testing.assert_allclose(p.sum(axis=1), 1, atol=1e-6)
    assert (p.argmax(axis=1) == y[320:]).mean() > 0.75
    assert 1 <= model.best_epoch <= 12
    assert len(model.history) > 0
    np.testing.assert_allclose(p, model.predict_proba(X[320:]))


def test_transformer_encoder_masks_future():
    torch.manual_seed(3)
    model = CausalTransformerNet(2, 8).eval()
    original = torch.tensor([[0, 1, 0, 0, 1, 1, 0, 1]])
    altered = original.clone()
    altered[:, 4:] = 1 - altered[:, 4:]
    with torch.no_grad():
        a, b = model.encode(original), model.encode(altered)
    torch.testing.assert_close(a[:, :4], b[:, :4], atol=1e-6, rtol=1e-6)


def test_neural_reproducible_and_no_mutation():
    rng = np.random.default_rng(11)
    X = rng.integers(0, 3, (96, 4))
    y = X[:, -1].copy()
    before = X.copy()
    a = build_neural("gru", 3, window=4, seed=9, epochs=2, device="cpu").fit(X, y)
    b = build_neural("gru", 3, window=4, seed=9, epochs=2, device="cpu").fit(X, y)
    np.testing.assert_array_equal(X, before)
    np.testing.assert_allclose(a.predict_proba(X), b.predict_proba(X), atol=1e-7)
    assert a.predict_proba(X[:0]).shape == (0, 3)
