"""Synthetic QRNG/control simulator. No hardware or certification claims."""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import numpy as np
from scipy.special import ndtr, i0e
from scipy.signal import lfilter

@dataclass(frozen=True)
class Config:
    n: int = 262144
    seed: int = 20261114
    amplitude: float = 1.0
    gaussian_sigma: float = 0.15
    gaussian_rho: float = 0.0
    phase_mode: str = "iid"
    phase_step_sigma: float = 0.25
    gain: float = 0.5
    window: int = 256
    update_period: int = 256
    deadband: float = 0.0
    target: float = 0.5
    initial_threshold: float = 0.0
    threshold_limit: float = 3.0
    offset: float = 0.0
    drift_amplitude: float = 0.0
    drift_period: int = 32768
    burn_in: int = 8192

    def validate(self):
        for name in ["n", "seed", "window", "update_period", "drift_period", "burn_in"]:
            if isinstance(getattr(self,name), bool) or not isinstance(getattr(self,name), int):
                raise ValueError(f"{name} must be an integer")
        if self.seed < 0:
            raise ValueError("seed must be nonnegative")
        if self.n < 2 or self.amplitude <= 0 or self.gaussian_sigma < 0:
            raise ValueError("invalid sample count/amplitude/noise")
        if not -1 < self.gaussian_rho < 1:
            raise ValueError("AR coefficient must be inside (-1, 1)")
        if self.phase_mode not in {"iid", "diffusion"} or self.phase_step_sigma <= 0:
            raise ValueError("invalid phase model")
        if self.window < 1 or self.update_period < 1 or self.gain < 0:
            raise ValueError("invalid controller")
        if not 0 <= self.deadband < .5 or not 0 < self.target < 1:
            raise ValueError("invalid deadband/target")
        if self.threshold_limit <= 0 or abs(self.initial_threshold) > self.threshold_limit:
            raise ValueError("initial threshold outside rails")
        if not 0 <= self.burn_in < self.n or self.drift_period < 1:
            raise ValueError("invalid burn-in/period")
        for value in asdict(self).values():
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("non-finite parameter")


def iid_phase_probability(threshold, classical, amplitude=1.0):
    """P(A cos(Phi)+C > theta | C,theta), Phi uniform and independent."""
    z = (np.asarray(threshold) - np.asarray(classical)) / amplitude
    return np.arccos(np.clip(z, -1, 1)) / np.pi


def diffusion_probability(threshold, classical, previous_phase, sigma, amplitude=1.0):
    """Conditional on revealed preceding phase; wrapped Gaussian innovation.

    Numerical sum of Gaussian interval probabilities, with neglected mass far
    below 1e-14 for finite sigma in tested range. This is a stronger side-info
    experiment, not a claim that the preceding phase is observed in hardware.
    """
    z = (np.asarray(threshold) - np.asarray(classical)) / amplitude
    alpha = np.arccos(np.clip(z, -1, 1))
    mu = np.remainder(np.asarray(previous_phase) + np.pi, 2*np.pi) - np.pi
    kmax = int(np.ceil((10*sigma + 2*np.pi) / (2*np.pi)))
    p = np.zeros_like(z, dtype=float)
    for k in range(-kmax, kmax+1):
        p += ndtr((alpha+2*np.pi*k-mu)/sigma) - ndtr((-alpha+2*np.pi*k-mu)/sigma)
    return np.clip(p, 0, 1)


def simulate(config: Config):
    config.validate()
    c = config
    # Independent child streams prevent changing one component from changing all.
    seeds = np.random.SeedSequence(c.seed).spawn(2)
    phase_rng, noise_rng = (np.random.default_rng(s) for s in seeds)
    if c.phase_mode == "iid":
        phase = phase_rng.uniform(-np.pi, np.pi, c.n)
        previous_phase = np.r_[0., phase[:-1]]
    else:
        phi0 = phase_rng.uniform(-np.pi, np.pi)
        innovations = phase_rng.normal(0, c.phase_step_sigma, c.n)
        phase = np.remainder(phi0+np.cumsum(innovations)+np.pi, 2*np.pi)-np.pi
        previous_phase = np.r_[phi0, phase[:-1]]
    innovations = noise_rng.normal(0, c.gaussian_sigma*np.sqrt(1-c.gaussian_rho**2), c.n)
    # Stationary AR(1) initialization: x[-1] ~ N(0,sigma^2).
    prior_noise = noise_rng.normal(0, c.gaussian_sigma)
    classical = lfilter([1.], [1., -c.gaussian_rho], innovations,
                        zi=[c.gaussian_rho*prior_noise])[0]
    classical += c.offset + c.drift_amplitude*np.sin(2*np.pi*np.arange(c.n)/c.drift_period)
    analog = c.amplitude*np.cos(phase) + classical
    bits = np.empty(c.n, dtype=np.uint8)
    thresholds = np.empty(c.n, dtype=float)
    theta = c.initial_threshold
    rows = []
    # Cumulative counts allow overlapping-window feedback without copying buffers.
    prefix = np.zeros(c.n+1, dtype=np.int64)
    for start in range(0, c.n, c.update_period):
        stop = min(start+c.update_period, c.n)
        thresholds[start:stop] = theta
        bits[start:stop] = analog[start:stop] > theta
        prefix[start+1:stop+1] = prefix[start] + np.cumsum(bits[start:stop])
        if stop % c.update_period == 0 and stop >= c.window:
            observed = (prefix[stop]-prefix[stop-c.window])/c.window
            error = observed-c.target
            step = c.gain*error if abs(error) > c.deadband else 0.
            new_theta = float(np.clip(theta+step, -c.threshold_limit, c.threshold_limit))
            rows.append((stop, theta, observed, error, new_theta, float(step != 0)))
            theta = new_theta
    if c.phase_mode == "iid":
        p = iid_phase_probability(thresholds, classical, c.amplitude)
    else:
        p = diffusion_probability(thresholds, classical, previous_phase,
                                  c.phase_step_sigma, c.amplitude)
    return {"config": c, "phase": phase, "classical": classical, "analog": analog,
            "bits": bits, "threshold": thresholds, "conditional_p": p,
            "updates": np.asarray(rows, dtype=float).reshape(-1, 6)}


def binary_entropy(p):
    p = np.asarray(p, dtype=float)
    ans = np.zeros_like(p)
    inside = (p > 0) & (p < 1)
    ans[inside] = -p[inside]*np.log2(p[inside])-(1-p[inside])*np.log2(1-p[inside])
    return ans


def corr(x, lag=1):
    x = np.asarray(x, dtype=float)
    if lag < 1 or len(x) <= lag or np.std(x[:-lag]) == 0 or np.std(x[lag:]) == 0:
        return None
    return float(np.corrcoef(x[:-lag], x[lag:])[0,1])


def context_predictor(bits, depth=6):
    """Chronological train/test predictor, Laplace smoothing; diagnostic only."""
    b = np.asarray(bits, dtype=np.uint8)
    if len(b) <= depth+2:
        return {"accuracy": None, "unseen_fraction": None, "test_samples": 0}
    contexts = np.zeros(len(b)-depth, dtype=np.int64)
    for j in range(depth):
        contexts = (contexts << 1) | b[j:len(b)-depth+j]
    y = b[depth:]
    split = len(y)//2
    counts = np.bincount(contexts[:split], minlength=2**depth)
    ones = np.bincount(contexts[:split], weights=y[:split], minlength=2**depth)
    probs = (ones+1)/(counts+2)
    prediction = probs[contexts[split:]] >= .5
    return {"accuracy": float(np.mean(prediction == y[split:])),
            "unseen_fraction": float(np.mean(counts[contexts[split:]] == 0)),
            "test_samples": int(len(y)-split)}


def distribution_pdf(x, amplitude=1.0, sigma=.15, phase_nodes=16384):
    """Midpoint quadrature of arcsine * normal; singular arcsine avoided."""
    if sigma <= 0:
        z = np.asarray(x, dtype=float)
        out = np.zeros_like(z)
        interior = abs(z) < amplitude
        out[interior] = 1/(np.pi*np.sqrt(amplitude**2-z[interior]**2))
        return out
    phases = 2*np.pi*(np.arange(phase_nodes)+.5)/phase_nodes
    centers = amplitude*np.cos(phases)
    return np.array([np.mean(np.exp(-.5*((v-centers)/sigma)**2))/(sigma*np.sqrt(2*np.pi))
                     for v in np.asarray(x).reshape(-1)])


def center_density(amplitude=1.0, sigma=.15):
    """Closed-form centered arcsine/Gaussian density via scaled Bessel I0.

    For sigma/A below 1e-8, the limiting density differs by O((sigma/A)^2).
    This avoids unresolved narrow kernels in phase quadrature.
    """
    if amplitude <= 0 or sigma < 0:
        raise ValueError("invalid amplitude/sigma")
    if sigma/amplitude < 1e-8:
        return 1/(np.pi*amplitude)
    a = (amplitude/(2*sigma))**2
    return float(i0e(a)/(sigma*np.sqrt(2*np.pi)))


def linear_roots(gain, density, ratio=1):
    """W=L*U equal complete windows; deterministic mean linearization."""
    if ratio < 1 or int(ratio) != ratio:
        raise ValueError("ratio must be a positive integer")
    l = int(ratio)
    coefficients = np.full(l+1, gain*density/l)
    coefficients[0] = 1.
    coefficients[1] -= 1.
    return np.roots(coefficients)


def linear_theory(config):
    c = config
    f = center_density(c.amplitude,c.gaussian_sigma)
    a = c.gain*f
    applicable = (c.phase_mode == "iid" and c.gaussian_rho == 0 and c.offset == 0
                  and c.drift_amplitude == 0 and c.target == .5 and c.deadband == 0
                  and c.gain > 0)
    result = {"density_at_zero": f, "dimensionless_gain": a,
              "linear_theory_applicable": applicable,
              "linear_theory_scope": "local near zero; IID phase/white noise; target 0.5; no offset/drift/deadband; rails inactive"}
    if not applicable:
        return result
    if c.window % c.update_period == 0:
        ratio = c.window//c.update_period
        roots = linear_roots(c.gain, f, ratio)
        result.update({"window_update_ratio": ratio,
                       "linear_spectral_radius": float(max(abs(roots))),
                       "critical_dimensionless_gain": float(2*ratio*np.sin(np.pi/(2*ratio))**2)})
    if c.window == c.update_period and 0 < a < 2:
        result.update({"threshold_variance_linear": c.gain*.25/(c.window*f*(2-a)),
                       "block_lag1_corr_linear": -a/2})
    return result


def metrics(result):
    c = result["config"]
    b = result["bits"][c.burn_in:]
    t = result["threshold"][c.burn_in:]
    p = result["conditional_p"][c.burn_in:]
    q = float(np.mean(b))
    # Fixed original controller alignment retained for block diagnostics.
    aligned = ((c.burn_in+c.update_period-1)//c.update_period)*c.update_period
    count = max(0,(c.n-aligned)//c.update_period)
    blocks = result["bits"][aligned:aligned+count*c.update_period].reshape(count,c.update_period).mean(1)
    guesses = np.maximum(p,1-p)
    out = {"samples_analyzed": len(b), "one_fraction": q,
           "marginal_min_entropy_plugin": -math.log2(max(q, 1-q)),
           "bit_lag1_corr": corr(b), "bit_lag8_corr": corr(b,8),
           "block_lag1_corr": corr(blocks), "block_mean_variance": float(np.var(blocks)) if count else None,
           "threshold_mean": float(np.mean(t)), "threshold_variance": float(np.var(t)),
           "threshold_rail_fraction": float(np.mean(abs(t) >= c.threshold_limit)),
           "model_causal_sideinfo_mean_guess_probability": float(np.mean(guesses)),
           "model_causal_sideinfo_average_min_entropy_mc": float(-np.log2(np.mean(guesses))),
           "model_causal_sideinfo_mean_pointwise_min_entropy_mc": float(np.mean(-np.log2(guesses))),
           "model_causal_sideinfo_mean_shannon_entropy_mc": float(np.mean(binary_entropy(p))),
           "model_causal_sideinfo_worst_observed_min_entropy": float(-np.log2(max(guesses))),
           "context6_test_accuracy": context_predictor(b,6)["accuracy"],
           "conditioning": "causal_classical_noise_and_current_threshold_excludes_future_transcript" if c.phase_mode=="iid"
                          else "causal_classical_noise_current_threshold_previous_phase_excludes_future_transcript"}
    out["diagnostics_status"] = "ok" if len(b)>8 and count>2 else "insufficient_data_for_some_diagnostics"
    out.update(linear_theory(c))
    return out


def enumerate_feedback(n=12, gain=2., amplitude=1., limit=3.):
    """Exact binary tree, iid uniform phase, C=0, W=U=1; no sampling."""
    states = [(0.,1.,0)]
    marginal = []
    for _ in range(n):
        new = []
        one_mass = 0.
        for theta, probability, word in states:
            p = float(iid_phase_probability(theta,0.,amplitude))
            one_mass += probability*p
            for bit, weight in ((0,1-p),(1,p)):
                if weight > 0:
                    updated = float(np.clip(theta+gain*(bit-.5), -limit,limit))
                    new.append((updated, probability*weight,(word<<1)|bit))
        states = new
        marginal.append(one_mass)
    largest = max(v[1] for v in states)
    return {"n":n,"gain":gain,"paths_nonzero":len(states),
            "probability_sum":sum(v[1] for v in states), "bit_marginals":marginal,
            "max_word_probability":largest,"joint_min_entropy":-math.log2(largest),
            "joint_min_entropy_per_bit":-math.log2(largest)/n}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--out", type=Path, default=Path("results/single"))
    args = parser.parse_args()
    config = Config(**json.loads(args.config.read_text())) if args.config else Config()
    result = simulate(config)
    args.out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out/"trace.npz", **{k:v for k,v in result.items() if k != "config"})
    (args.out/"config.json").write_text(json.dumps(asdict(config),indent=2)+"\n")
    diagnostic = metrics(result)
    (args.out/"metrics.json").write_text(json.dumps(diagnostic,indent=2,allow_nan=False)+"\n")
    print(json.dumps(diagnostic,indent=2,allow_nan=False))

if __name__ == "__main__":
    main()
