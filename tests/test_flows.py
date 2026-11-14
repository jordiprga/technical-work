import numpy as np
import pytest

torch = pytest.importorskip('torch')
from entropy_oracle.flows import (rational_quadratic_spline,
                                  ConditionalSplineNetwork, build_flow)


def test_spline_inverse_jacobian_and_tails():
    torch.manual_seed(1010)
    batch, k = 4, 8
    xx = torch.linspace(-6, 6, 73, dtype=torch.float64).repeat(batch, 1)
    ww = torch.randn(batch, k, dtype=torch.float64) * 0.5
    hh = torch.randn(batch, k, dtype=torch.float64) * 0.5
    dd = torch.randn(batch, k - 1, dtype=torch.float64) * 0.5
    yy, logj = rational_quadratic_spline(xx, ww, hh, dd)
    xr, logji = rational_quadratic_spline(yy, ww, hh, dd, inverse=True)
    torch.testing.assert_close(xr, xx, atol=1e-8, rtol=1e-8)
    torch.testing.assert_close(logj + logji, torch.zeros_like(xx), atol=1e-8, rtol=1e-8)
    assert torch.all(yy[:, 1:] > yy[:, :-1])
    torch.testing.assert_close(yy[:, 0], xx[:, 0])
    torch.testing.assert_close(yy[:, -1], xx[:, -1])


@pytest.mark.parametrize('alphabet', [2, 8, 32])
def test_bin_mass_normalization_gradient(alphabet):
    model = ConditionalSplineNetwork(alphabet, window=7)
    contexts = torch.randint(0, alphabet, (16, 7))
    prob = model(contexts)
    assert prob.shape == (16, alphabet)
    torch.testing.assert_close(prob.sum(-1), torch.ones(16, dtype=prob.dtype))
    assert torch.all(prob > 0)
    loss = -torch.log(prob[:, 0]).mean()
    loss.backward()
    for parameter in model.parameters():
        assert parameter.grad is not None
        assert torch.isfinite(parameter.grad).all()


def test_flow_fit_and_exact_mass_behavior():
    rng = np.random.default_rng(1004)
    X = rng.integers(0, 2, (600, 8))
    y = X[:, -1]
    flow = build_flow(2, window=8, seed=1005, epochs=5, batch_size=100)
    flow.fit(X[:450], y[:450], X[450:525], y[450:525])
    p = flow.predict_proba(X[525:])
    assert p.shape == (75, 2)
    np.testing.assert_allclose(p.sum(1), 1, atol=1e-9)
    assert (p.argmax(1) == y[525:]).mean() > 0.8
    assert len(flow.history) == 5
    assert flow.predict_proba(np.empty((0, 8))).shape == (0, 2)


def test_extreme_conditioner_produces_valid_masses():
    model = ConditionalSplineNetwork(16, window=3)
    with torch.no_grad():
        model.conditioner[-1].bias[:] = 100
    probs = model(torch.tensor([[0, 0, 0], [15, 15, 15]]))
    assert torch.isfinite(probs).all()
    assert torch.all(probs > 0)
    torch.testing.assert_close(probs.sum(-1), torch.ones(2, dtype=probs.dtype))


def test_spline_log_jacobian_matches_autograd():
    torch.manual_seed(1008)
    xx = torch.linspace(-3.8, 3.8, 37, dtype=torch.float64)[None, :].requires_grad_()
    ww = torch.randn(1, 8, dtype=torch.float64) * 0.5
    hh = torch.randn(1, 8, dtype=torch.float64) * 0.5
    dd = torch.randn(1, 7, dtype=torch.float64) * 0.5
    yy, logj = rational_quadratic_spline(xx, ww, hh, dd)
    (actual_jacobian,) = torch.autograd.grad(yy.sum(), xx)
    torch.testing.assert_close(actual_jacobian, logj.exp(), atol=1e-9, rtol=1e-9)
