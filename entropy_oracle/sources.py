"""Reproducible discrete sources with carefully scoped conditional references.

The oracle, when supplied, conditions only on past *observed* samples and known
source parameters (including the public sample clock), never future observations.
An exactly uniform marginal means a probability law, not forced sample balancing.
"""
from dataclasses import dataclass
from typing import Optional
import numpy as np
from scipy.special import ndtr
from numpy.polynomial.legendre import leggauss

SOURCE_NAMES = ["bernoulli", "markov", "higher_order", "periodic", "hmm", "ar1",
                "arcsine", "drift", "long_range", "nonlinear"]

@dataclass
class SourceData:
    x: np.ndarray
    alphabet_size: int
    oracle_probs: Optional[np.ndarray]
    metadata: dict


def _binary_probs(p):
    p = np.asarray(p, dtype=float)
    return np.column_stack((1-p, p))


def _prob(value, name):
    value = float(value)
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


def _positive_int(value, name):
    if int(value) != value or int(value) < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _result(name, x, alphabet, q, seed, params, **metadata):
    x = np.asarray(x, dtype=np.int64)
    if q is not None:
        q = np.asarray(q, dtype=np.float64)
        if q.shape != (len(x), alphabet) or not np.allclose(q.sum(axis=1), 1):
            raise RuntimeError("Invalid oracle distribution")
    base = dict(source=name, seed=int(seed), parameters=params,
                oracle_scope="P(X_t | observed X_0,...,X_{t-1}, known parameters and t)",
                stationary=True)
    base.update(metadata)
    if q is not None:
        base["oracle_mean_guessing_probability"] = float(np.max(q, axis=1).mean())
    return SourceData(x, int(alphabet), q, base)


def make_source(name, n=12000, seed=0, **params):
    """Generate one source; unknown parameter keys fail to catch configuration errors.

    Default ``nonlinear`` has a uniform four-symbol marginal with a delayed noisy
    multiplexer whose complete driver set is absent from short contexts. ``long_range`` has a fair
    binary marginal and copy dependence at lag 16. Both have exact causal oracles.
    """
    aliases = {"iid": "bernoulli", "markov_binary": "markov", "quantized_ar1": "ar1"}
    name = aliases.get(name, name)
    if name not in SOURCE_NAMES:
        raise ValueError(f"Unknown source {name!r}; choose {SOURCE_NAMES}")
    n = _positive_int(n, "n")
    rng = np.random.default_rng(seed)
    p = dict(params)
    def pop(key, default):
        return p.pop(key, default)
    def done():
        if p:
            raise ValueError(f"Unknown parameters for {name}: {sorted(p)}")

    if name == "bernoulli":
        prob = _prob(pop("p", .7), "p"); done()
        q = _binary_probs(np.full(n, prob))
        x = rng.binomial(1, prob, n)
        return _result(name, x, 2, q, seed, dict(p=prob), marginal_probs=[1-prob, prob],
                       exact_optimal_success=max(prob, 1-prob), iid=True)

    if name == "markov":
        p01 = _prob(pop("p01", .05), "p01")
        p10 = _prob(pop("p10", .05), "p10"); done()
        if p01+p10 == 0:
            pi1 = .5
        else:
            pi1 = p01/(p01+p10)
        x = np.empty(n, dtype=np.int64); probs = np.empty(n)
        probs[0] = pi1; x[0] = rng.random() < pi1
        for t in range(1, n):
            probs[t] = (1-p10) if x[t-1] else p01
            x[t] = rng.random() < probs[t]
        g = (1-pi1)*max(p01, 1-p01) + pi1*max(p10, 1-p10)
        return _result(name, x, 2, _binary_probs(probs), seed, dict(p01=p01,p10=p10),
                       marginal_probs=[1-pi1,pi1], exact_stationary_optimal_success=g,
                       marginal_uniform=bool(p01 == p10), dependence_order=1)

    if name == "higher_order":
        order = _positive_int(pop("order", 5), "order")
        noise = _prob(pop("noise", .03), "noise"); done()
        if order < 3:
            raise ValueError("higher_order requires order >= 3")
        x = rng.integers(0, 2, n, dtype=np.int64)
        probs = np.full(n, .5)
        for t in range(order, n):
            bit = int(x[t-order] ^ (x[t-1] & x[t-2]))
            probs[t] = (1-noise) if bit else noise
            x[t] = rng.random() < probs[t]
        return _result(name, x, 2, _binary_probs(probs), seed, dict(order=order,noise=noise),
                       marginal_probs=[.5,.5], marginal_uniform=True,
                       exact_steady_optimal_success=max(noise,1-noise), dependence_order=order,
                       rule="X[t-order] XOR (X[t-1] AND X[t-2]) XOR Bernoulli(noise)",
                       uniformity_proof="State shift is a permutation for each noise bit because oldest state bit appears exactly once via XOR; uniform initial state is invariant.")

    if name == "periodic":
        period = _positive_int(pop("period", 32), "period")
        noise = _prob(pop("noise", .05), "noise"); done()
        x = rng.integers(0,2,n,dtype=np.int64); probs = np.full(n,.5)
        for t in range(period,n):
            probs[t] = (1-noise) if x[t-period] else noise
            x[t] = rng.random()<probs[t]
        return _result(name,x,2,_binary_probs(probs),seed,dict(period=period,noise=noise),
                       marginal_probs=[.5,.5],marginal_uniform=True,
                       exact_steady_optimal_success=max(noise,1-noise),dependence_order=period,
                       rule="Seasonal binary process: X[t]=X[t-period] XOR Bernoulli(noise); independent Markov chains across phases.")

    if name == "drift":
        period = _positive_int(pop("period", 4000), "period")
        amplitude = float(pop("amplitude", .4)); phase = float(pop("phase", 0.0)); done()
        if not 0 <= amplitude <= .5:
            raise ValueError("amplitude must be in [0, .5]")
        probs = .5+amplitude*np.sin(2*np.pi*np.arange(n)/period+phase)
        x = (rng.random(n)<probs).astype(np.int64)
        return _result(name, x, 2, _binary_probs(probs), seed,
                       dict(period=period,amplitude=amplitude,phase=phase), stationary=False,
                       conditional_independence="Independent given known deterministic clock; slowly drifting marginal probabilities.",
                       oracle_uses_public_clock=True,
                       model_limitation="Window predictors do not receive explicit time or phase features.")

    if name == "hmm":
        stay = _prob(pop("stay", .97), "stay")
        emission_noise = _prob(pop("emission_noise", .1), "emission_noise"); done()
        transition = np.array([[stay,1-stay],[1-stay,stay]])
        emission = np.array([[1-emission_noise,emission_noise],[emission_noise,1-emission_noise]])
        q = np.empty((n,2)); x = np.empty(n,dtype=np.int64)
        predictive_hidden = np.array([.5,.5]); hidden = int(rng.integers(2))
        for t in range(n):
            if t:
                hidden = hidden if rng.random()<stay else 1-hidden
            q[t] = predictive_hidden @ emission
            x[t] = hidden ^ int(rng.random()<emission_noise)
            posterior = predictive_hidden*emission[:,x[t]]
            posterior /= posterior.sum()
            predictive_hidden = posterior @ transition
        return _result(name,x,2,q,seed,dict(stay=stay,emission_noise=emission_noise),
                       marginal_probs=[.5,.5], marginal_uniform=True,
                       reference="Exact forward Bayesian filtering over hidden state using observed past only.")

    if name == "ar1":
        rho = float(pop("rho", .95)); sigma = float(pop("sigma", .3))
        alphabet = _positive_int(pop("alphabet_size", 8), "alphabet_size"); done()
        if not abs(rho)<1 or sigma<=0 or alphabet<2:
            raise ValueError("ar1 requires |rho|<1, sigma>0, alphabet_size>=2")
        stationary_sd = sigma/np.sqrt(1-rho*rho)
        interior = np.array([0.0]) if alphabet == 2 else np.linspace(-2.5*stationary_sd,2.5*stationary_sd,alphabet-1)
        edges = np.r_[-np.inf,interior,np.inf]
        z = np.empty(n); z[0] = rng.normal(scale=stationary_sd)
        for t in range(1,n):
            z[t] = rho*z[t-1]+rng.normal(scale=sigma)
        x = np.searchsorted(edges[1:-1],z,side="right")
        marginal = np.diff(ndtr(edges/stationary_sd))
        # Gaussian quadrature integrates E[max_j P(bin j | latent Z[t-1])].
        # This is privileged side information, NOT the quantized-history oracle.
        nodes,weights = np.polynomial.hermite.hermgauss(120)
        means = rho*np.sqrt(2)*stationary_sd*nodes
        masses = np.diff(ndtr((edges[None,:]-means[:,None])/sigma),axis=1)
        privileged = float(weights @ masses.max(axis=1)/np.sqrt(np.pi))
        return _result(name,x,alphabet,None,seed,dict(rho=rho,sigma=sigma,alphabet_size=alphabet),
                       marginal_probs=marginal.tolist(),bin_edges=[None if not np.isfinite(e) else float(e) for e in edges],
                       oracle_scope="Unavailable: conditioning on quantized history requires nonlinear filtering.",
                       privileged_latent_success_upper_bound_numeric=privileged,
                       privileged_reference="120-point Gauss-Hermite approximation with continuous previous state supplied; never evaluated as an observed-history predictor.")

    if name == "arcsine":
        amplitude = float(pop("amplitude", 1.0)); sigma = float(pop("sigma", .15))
        alphabet = _positive_int(pop("alphabet_size", 8), "alphabet_size"); done()
        if amplitude<=0 or sigma<0 or alphabet<2:
            raise ValueError("arcsine requires amplitude>0, sigma>=0, alphabet_size>=2")
        edge_limit = amplitude+2*sigma
        interior = np.array([0.0]) if alphabet == 2 else np.linspace(-edge_limit,edge_limit,alphabet-1)
        edges = np.r_[-np.inf,interior,np.inf]
        z = amplitude*np.cos(rng.uniform(0,np.pi,n))+rng.normal(0,sigma,n)
        x = np.searchsorted(edges[1:-1],z,side="right")
        if sigma == 0:
            cdf = .5+np.arcsin(np.clip(edges/amplitude,-1,1))/np.pi
            masses = np.diff(cdf); error = 0.0
        else:
            def integrate(degree):
                nodes,weights = leggauss(degree)
                mu = amplitude*np.cos((nodes+1)*np.pi/2)
                return weights @ np.diff(ndtr((edges[None,:]-mu[:,None])/sigma),axis=1)/2
            masses = integrate(256); error = float(np.max(np.abs(masses-integrate(512))))
        masses = np.maximum(masses,0); masses /= masses.sum()
        return _result(name,x,alphabet,np.tile(masses,(n,1)),seed,
                       dict(amplitude=amplitude,sigma=sigma,alphabet_size=alphabet),
                       marginal_probs=masses.tolist(),iid=True,
                       **({"numerical_optimal_success":float(max(masses))} if sigma>0 else {"exact_optimal_success":float(max(masses))}),
                       oracle_is_approximate=bool(sigma>0),
                       reference_scope="numerical quadrature" if sigma>0 else "analytic arcsine CDF",
                       reference="Arcsine convolved with Gaussian; bin masses integrated over uniform angle by 256-point Gauss-Legendre quadrature (analytic arcsine CDF for sigma=0).",
                       quadrature_256_vs_512_max_error=error,
                       bin_edges=[None if not np.isfinite(e) else float(e) for e in edges])

    if name == "long_range":
        lag = _positive_int(pop("lag", 16), "lag"); noise = _prob(pop("noise", .03), "noise"); done()
        x = rng.integers(0,2,n,dtype=np.int64); probs = np.full(n,.5)
        for t in range(lag,n):
            probs[t] = (1-noise) if x[t-lag] else noise
            x[t] = rng.random()<probs[t]
        return _result(name,x,2,_binary_probs(probs),seed,dict(lag=lag,noise=noise),
                       marginal_probs=[.5,.5], marginal_uniform=True,
                       exact_steady_optimal_success=max(noise,1-noise),dependence_order=lag,
                       rule="X[t] = X[t-lag] XOR Bernoulli(noise)",
                       uniformity_proof="Uniform initial lag-state is invariant under cyclic shift and independent symmetric bit flip.")

    if name == "nonlinear":
        lags = tuple(int(v) for v in pop("lags", (9,13,17)))
        noise = _prob(pop("noise", .03), "noise"); done()
        if len(lags)!=3 or len(set(lags))!=3 or min(lags)<1:
            raise ValueError("nonlinear lags must be three distinct positive integers")
        lag_a,lag_selector,lag_b = lags; burn = max(lags)
        u = rng.integers(0,2,n,dtype=np.int64)
        x = np.empty(n,dtype=np.int64); q = np.full((n,4),.25)
        # Expose initialization as observed iid symbols. This makes every oracle
        # row exact without conditioning on inaccessible prehistory drivers.
        prefix = min(n,burn)
        x[:prefix] = 2*u[:prefix]+rng.integers(0,2,prefix,dtype=np.int64)
        for t in range(burn,n):
            a = x[t-lag_a]//2; selector = x[t-lag_selector]//2; b = x[t-lag_b]//2
            v = int(a if selector else b)
            x[t] = 2*u[t]+(v ^ int(rng.random()<noise))
            pv = (1-noise) if v else noise
            q[t] = [.5*(1-pv),.5*pv,.5*(1-pv),.5*pv]
        return _result(name,x,4,q,seed,dict(lags=list(lags),noise=noise),
                       marginal_probs=[.25]*4,marginal_uniform=True,
                       exact_steady_optimal_success=.5*max(noise,1-noise),
                       dependence_order=burn,initial_iid_prefix=burn,
                       rule="X[t]=2 U[t]+V[t]; iid fair U; V[t]=(U[t-a] if U[t-selector] else U[t-b]) XOR noise.",
                       uniformity_proof="Distinct lagged iid fair driver bits make multiplexer output fair; fresh U[t] is independent of V[t], so each symbol has probability 1/4.",
                       initialization="First max(lags) symbols iid uniform; recurrent rule follows. Finite prefix is a documented nonstationary initialization.",
                       stationary=False)
    raise AssertionError("unreachable")
