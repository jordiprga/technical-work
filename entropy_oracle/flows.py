"""Conditional neural spline flow evaluated as exact discrete bin masses.

Given context c, U~Logistic(0,1) and Y = mu(c)+s(c)*S_c^{-1}(U),
where S_c is a monotone rational-quadratic spline with identity tails.
Category j is the event e_j <= Y < e_{j+1}; e_0=-inf, e_A=inf.
Therefore q(j|c)=sigmoid(S_c((e_{j+1}-mu)/s))
                  -sigmoid(S_c((e_j-mu)/s)).
Only these integrated masses are fitted/evaluated, never point densities.

This is a one-dimensional conditional normalizing flow, not a joint MAF.
For binary data its observable distribution is simply Bernoulli; the
within-bin continuous density is not identifiable from discrete observations.
"""
from __future__ import annotations

import copy
import math
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


def rational_quadratic_spline(inputs, raw_widths, raw_heights, raw_derivatives,
                              inverse=False, bound=4.0, min_bin=1e-3,
                              min_derivative=1e-3):
    """Batched monotonic RQS with identity tails; returns values and log|Jac|.

    inputs is (batch, points); raw widths/heights are (batch, K) and
    raw_derivatives is (batch, K-1). End derivatives are exactly one.
    """
    k = raw_widths.shape[-1]
    widths = min_bin + (2 * bound - k * min_bin) * F.softmax(raw_widths, -1)
    heights = min_bin + (2 * bound - k * min_bin) * F.softmax(raw_heights, -1)
    xknots = F.pad(torch.cumsum(widths, -1), (1, 0), value=0) - bound
    yknots = F.pad(torch.cumsum(heights, -1), (1, 0), value=0) - bound
    ones = torch.ones_like(raw_widths[:, :1])
    deriv = torch.cat([ones, min_derivative + F.softplus(raw_derivatives), ones], -1)
    inside = (inputs >= -bound) & (inputs <= bound)
    # Evaluate out-of-range points at a finite endpoint before selecting tails.
    safe_inputs = inputs.clamp(-bound, bound)
    knots = yknots if inverse else xknots
    idx = torch.searchsorted(knots.contiguous(), safe_inputs.contiguous(), right=True) - 1
    idx = idx.clamp(0, k - 1)
    gather = lambda t: torch.gather(t, 1, idx)
    xk, yk = gather(xknots), gather(yknots)
    wk, hk = gather(widths), gather(heights)
    dk, dk1 = gather(deriv), torch.gather(deriv, 1, idx + 1)
    delta = hk / wk
    if inverse:
        ydelta = safe_inputs - yk
        curvature = dk + dk1 - 2 * delta
        a = ydelta * curvature + hk * (delta - dk)
        b = hk * dk - ydelta * curvature
        c = -delta * ydelta
        discriminant = (b.square() - 4 * a * c).clamp_min(0)
        theta = (2 * c) / (-b - torch.sqrt(discriminant))
        theta = theta.clamp(0, 1)
        outputs = xk + theta * wk
    else:
        theta = ((safe_inputs - xk) / wk).clamp(0, 1)
        numerator = hk * (delta * theta.square() + dk * theta * (1 - theta))
        denominator = delta + (dk1 + dk - 2 * delta) * theta * (1 - theta)
        outputs = yk + numerator / denominator
    denominator = delta + (dk1 + dk - 2 * delta) * theta * (1 - theta)
    derivative_numerator = delta.square() * (
        dk1 * theta.square() + 2 * delta * theta * (1 - theta)
        + dk * (1 - theta).square())
    logdet = torch.log(derivative_numerator) - 2 * torch.log(denominator)
    if inverse:
        logdet = -logdet
    return torch.where(inside, outputs, inputs), torch.where(inside, logdet, torch.zeros_like(logdet))


class ConditionalSplineNetwork(nn.Module):
    def __init__(self, alphabet_size, window, hidden=48, spline_bins=8):
        super().__init__()
        self.alphabet_size = alphabet_size
        self.spline_bins = spline_bins
        self.conditioner = nn.Sequential(
            nn.Linear(window, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, 3 * spline_bins + 1))
        last = self.conditioner[-1]
        nn.init.zeros_(last.weight)
        nn.init.zeros_(last.bias)
        with torch.no_grad():
            last.bias[2 + 2 * spline_bins:] = math.log(math.expm1(1 - 1e-3))
        self.register_buffer('edges', torch.linspace(-3.0, 3.0, alphabet_size + 1)[1:-1])

    def parameters_for(self, contexts):
        contexts = 2 * contexts.float() / (self.alphabet_size - 1) - 1
        raw = self.conditioner(contexts)
        k = self.spline_bins
        location = raw[:, :1]
        scale = torch.exp(raw[:, 1:2].clamp(-3, 3))
        return location, scale, raw[:, 2:2+k], raw[:, 2+k:2+2*k], raw[:, 2+2*k:]

    def cdf(self, points, contexts):
        location, scale, widths, heights, derivatives = self.parameters_for(contexts)
        transformed, _ = rational_quadratic_spline(
            (points - location) / scale, widths, heights, derivatives)
        return torch.sigmoid(transformed.double())

    def forward(self, contexts):
        # Double precision CDF subtraction reduces tail cancellation. Tiny clipping
        # is an explicit numerical floor, followed by probability normalization.
        cdf = self.cdf(self.edges[None, :].expand(len(contexts), -1), contexts)
        cdf = torch.cat([torch.zeros_like(cdf[:, :1]), cdf, torch.ones_like(cdf[:, :1])], 1)
        masses = (cdf[:, 1:] - cdf[:, :-1]).clamp_min(1e-12)
        return masses / masses.sum(1, keepdim=True)


class ConditionalSplineFlow:
    name = 'flow'
    description = 'Conditional rational-quadratic spline; exact logistic-CDF bin masses'

    def __init__(self, alphabet_size, window=32, seed=0, epochs=15,
                 batch_size=256, hidden=48, spline_bins=8, learning_rate=0.003,
                 device=None, **kwargs):
        if alphabet_size < 2:
            raise ValueError('alphabet_size must be at least 2')
        self.alphabet_size = int(alphabet_size)
        self.window = int(window)
        self.seed = int(seed)
        self.epochs = int(epochs)
        self.batch_size = int(batch_size)
        self.hidden = int(hidden)
        self.spline_bins = int(spline_bins)
        self.learning_rate = float(learning_rate)
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))
        self.history = []
        self.model = None

    def _tensor(self, X):
        X = np.asarray(X)
        if X.ndim != 2 or X.shape[1] != self.window:
            raise ValueError(f'Expected shape (n, {self.window}), got {X.shape}')
        if not np.isfinite(X).all() or ((X < 0) | (X >= self.alphabet_size)).any():
            raise ValueError('Contexts contain invalid symbols')
        return torch.as_tensor(X.copy(), dtype=torch.float32, device=self.device)

    def fit(self, X, y, X_val=None, y_val=None):
        torch.set_num_threads(1)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        torch.use_deterministic_algorithms(True, warn_only=True)
        self.model = ConditionalSplineNetwork(self.alphabet_size, self.window,
                                              self.hidden, self.spline_bins).to(self.device)
        xt = self._tensor(X)
        yt = torch.as_tensor(np.asarray(y).copy(), dtype=torch.long, device=self.device)
        if len(xt) == 0 or len(yt) != len(xt):
            raise ValueError('Empty or mismatched training data')
        has_val = X_val is not None and y_val is not None and len(y_val) > 0
        if has_val:
            xv = self._tensor(X_val)
            yv = torch.as_tensor(np.asarray(y_val).copy(), dtype=torch.long, device=self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        generator = torch.Generator(device='cpu').manual_seed(self.seed)
        best, best_state = float('inf'), None
        self.history = []
        for epoch in range(self.epochs):
            self.model.train()
            order = torch.randperm(len(xt), generator=generator).to(self.device)
            total = 0.0
            for start in range(0, len(xt), self.batch_size):
                ix = order[start:start + self.batch_size]
                probabilities = self.model(xt[ix])
                loss = -torch.log(probabilities.gather(1, yt[ix, None]).squeeze(1)).mean()
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 5.0)
                optimizer.step()
                total += float(loss.detach()) * len(ix)
            train_loss = total / len(xt) / math.log(2)
            self.model.eval()
            with torch.no_grad():
                if has_val:
                    total_val = 0.0
                    for start in range(0, len(xv), self.batch_size * 4):
                        pp = self.model(xv[start:start + self.batch_size * 4])
                        yy = yv[start:start + self.batch_size * 4]
                        total_val += float(-torch.log(pp.gather(1, yy[:, None])).sum())
                    val_loss = total_val / len(xv) / math.log(2)
                else:
                    val_loss = train_loss
            self.history.append({'epoch': epoch + 1, 'train_loss': train_loss,
                                 'val_loss': val_loss, 'loss_units': 'bits'})
            if val_loss < best:
                best = val_loss
                best_state = copy.deepcopy(self.model.state_dict())
        if best_state is not None:
            self.model.load_state_dict(best_state)
        self.model.eval()
        return self

    def predict_proba(self, X):
        if self.model is None:
            raise RuntimeError('Call fit before predict_proba')
        xt = self._tensor(X)
        if len(xt) == 0:
            return np.empty((0, self.alphabet_size))
        self.model.eval()
        with torch.no_grad():
            out = [self.model(xt[s:s + self.batch_size * 4]).cpu().numpy()
                   for s in range(0, len(xt), self.batch_size * 4)]
        return np.concatenate(out, 0)


def build_flow(alphabet_size, window=32, seed=0, epochs=15, **kwargs):
    return ConditionalSplineFlow(alphabet_size=alphabet_size, window=window,
                                 seed=seed, epochs=epochs, **kwargs)
