"""Exact finite disclosure-channel experiments; no physical entropy claims.

All probabilities use Fraction. The source models here are explicitly defined
finite distributions, separate from the QRNG simulator in mission 05.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path


def count_transcript(bits, window, period):
    if type(window) is not int or type(period) is not int or min(window, period) < 1:
        raise ValueError("positive integer window and period required")
    if window > len(bits) or any(type(b) is not int or b not in (0, 1) for b in bits):
        raise ValueError("nonempty full window of binary integers required")
    return tuple(sum(bits[end-window:end]) for end in range(window, len(bits)+1, period))


def fair_source(n):
    if type(n) is not int or not 1 <= n <= 18:
        raise ValueError("exhaustive n must be 1..18")
    probability = Fraction(1, 2**n)
    return {bits: probability for bits in product((0, 1), repeat=n)}


def paired_source(pairs):
    """Each independent pair is 01 or 10 with equal probability."""
    if type(pairs) is not int or not 1 <= pairs <= 18:
        raise ValueError("pairs must be 1..18")
    probability = Fraction(1, 2**pairs)
    return {tuple(b for first in choices for b in (first, 1-first)): probability
            for choices in product((0, 1), repeat=pairs)}


def measure(source, window, period):
    if not source or sum(source.values()) != 1 or min(source.values()) <= 0:
        raise ValueError("source must be a normalized positive finite distribution")
    lengths = {len(word) for word in source}
    if len(lengths) != 1:
        raise ValueError("source words must have the same length")
    groups = defaultdict(dict)
    for word, probability in source.items():
        groups[count_transcript(word, window, period)][word] = probability
    # Pguess(X|T) = sum_t max_x P(X=x,T=t), NOT max_t max_x P(X=x|T=t).
    guessing = sum((max(group.values()) for group in groups.values()), Fraction())
    unique_mass = sum((sum(group.values()) for group in groups.values() if len(group) == 1), Fraction())
    return {
        "n": next(iter(lengths)), "window": window, "period": period,
        "source_support": len(source), "distinct_transcripts": len(groups),
        "unconditional_min_entropy": -math.log2(float(max(source.values()))),
        "average_conditional_min_entropy": -math.log2(float(guessing)),
        "guess_probability_exact": str(guessing),
        "unique_reconstruction_probability_exact": str(unique_mass),
        "maximum_posterior_support": max(map(len, groups.values())),
    }


def reconstruct_rolling(counts, window):
    """All binary words compatible with full rolling counts, update period 1.

    First W bits plus count differences determine every later bit. At most 2**W
    branches are inspected; this is an algorithm, not an entropy estimator.
    """
    if type(window) is not int or not 1 <= window <= 18 or not counts:
        raise ValueError("window 1..18 and a nonempty transcript required")
    if any(type(c) is not int or not 0 <= c <= window for c in counts):
        raise ValueError("invalid rolling count")
    candidates = []
    for prefix in product((0, 1), repeat=window):
        if sum(prefix) != counts[0]:
            continue
        word = list(prefix)
        for index in range(1, len(counts)):
            next_bit = word[index-1] + counts[index] - counts[index-1]
            if next_bit not in (0, 1):
                break
            word.append(next_bit)
        else:
            candidates.append(tuple(word))
    return candidates


def exact_threshold_trace(bits, window, period, gain=Fraction(1), target=Fraction(1, 2)):
    """Unclipped controller, zero deadband, exact rational public telemetry."""
    if gain <= 0:
        raise ValueError("strictly positive gain required for recovery")
    thresholds = [Fraction()]
    for count in count_transcript(bits, window, period):
        thresholds.append(thresholds[-1] + gain * (Fraction(count, window) - target))
    return tuple(thresholds)


def recover_counts(thresholds, window, gain=Fraction(1), target=Fraction(1, 2)):
    if gain <= 0 or len(thresholds) < 2:
        raise ValueError("nonzero gain and consecutive thresholds required")
    recovered = tuple(window * ((b-a)/gain + target) for a, b in zip(thresholds, thresholds[1:]))
    if any(c.denominator != 1 or not 0 <= c <= window for c in recovered):
        raise ValueError("telemetry is not an exact unsaturated count channel")
    return tuple(int(c) for c in recovered)


def run():
    rows = []
    for n, window, period in [(8, 1, 1), (8, 2, 2), (12, 4, 4),
                               (12, 4, 1), (16, 4, 1), (16, 8, 1),
                               (16, 8, 2), (16, 8, 4), (16, 8, 8)]:
        rows.append({"source": "iid_fair_finite_model", **measure(fair_source(n), window, period)})
    rows.append({"source": "equiprobable_01_or_10_pairs", **measure(paired_source(6), 1, 1)})
    return {"claim_kind": "exact_finite_enumeration_with_analytical_proofs_in_README",
            "conditional_entropy_definition": "-log2 sum_t max_x P(X=x,T=t)",
            "rows": rows,
            "disjoint_fair_block_formula": [
                {"window": w, "entropy_per_block": w-math.log2(w+1),
                 "entropy_per_input_bit": 1-math.log2(w+1)/w}
                for w in (1, 2, 4, 16, 64, 256, 1024)]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results.json"))
    args = parser.parse_args()
    output = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps(output, indent=2, allow_nan=False))
