"""Exact weighted enumeration; no Monte Carlo approximation."""
from itertools import product

import numpy as np
import pytest


def _mux(a, selector, b):
    return a if selector else b


def _enumerate_pair(noise):
    joint = np.zeros((2, 2), dtype=float)
    for a, selector, b, c in product((0, 1), repeat=4):
        clean_target = _mux(a, selector, b)
        clean_old = _mux(selector, b, c)
        for e_target, e_old in product((0, 1), repeat=2):
            weight = (noise if e_target else 1 - noise)
            weight *= noise if e_old else 1 - noise
            joint[clean_target ^ e_target, clean_old ^ e_old] += weight / 16
    return joint


@pytest.mark.parametrize('noise', [0.0, 0.03, 0.2, 0.5, 0.8, 1.0])
def test_exact_nonlinear_order_four_five_success(noise):
    joint = _enumerate_pair(noise)
    attenuation = (1 - 2 * noise) ** 2
    expected = np.array([
        [.25 - attenuation / 16, .25 + attenuation / 16],
        [.25 + attenuation / 16, .25 - attenuation / 16],
    ])
    np.testing.assert_allclose(joint, expected, atol=1e-14)
    np.testing.assert_allclose(joint.sum(axis=0), [.5, .5], atol=1e-14)
    np.testing.assert_allclose(joint.sum(axis=1), [.5, .5], atol=1e-14)
    # Sum max joint masses for low-bit guessing, then guess the independent U_t.
    symbol_guessing_success = .5 * joint.max(axis=0).sum()
    assert symbol_guessing_success == pytest.approx(.25 + attenuation / 16)


def test_default_nonlinear_references():
    noise = .03
    joint = _enumerate_pair(noise)
    assert .5 * joint.max(axis=0).sum() == pytest.approx(.305225)
    # Marginal low bit is fair; a past independent of the target gives 1/4.
    assert .5 * joint.sum(axis=1).max() == pytest.approx(.25)
    # Full past reveals the clean low bit but never the fresh high bit.
    assert .5 * max(noise, 1 - noise) == pytest.approx(.485)


def test_clean_pair_exhaustive_enumeration():
    np.testing.assert_allclose(_enumerate_pair(0), [[3 / 16, 5 / 16], [5 / 16, 3 / 16]])
