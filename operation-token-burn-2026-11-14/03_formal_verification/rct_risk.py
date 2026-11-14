#!/usr/bin/env python3
"""Probabilidad EXACTA de alarma RCT para un modelo Bernoulli IID declarado.

No estima entropía ni decide que una fuente física sea IID. Sólo stdlib.
"""
from fractions import Fraction
import json
from pathlib import Path


def alarm_probability_iid(length: int, cutoff: int, p_one: Fraction) -> Fraction:
    if type(length) is not int or not 0 <= length <= 4096:
        raise ValueError("length debe ser entero 0..4096")
    if type(cutoff) is not int or not 2 <= cutoff <= 256:
        raise ValueError("cutoff debe ser entero 2..256")
    if not isinstance(p_one, Fraction) or not 0 <= p_one <= 1:
        raise ValueError("p_one debe ser Fraction en [0,1]")
    if length == 0:
        return Fraction(0)
    weights = (1 - p_one, p_one)
    alive = {(0, 1): weights[0], (1, 1): weights[1]}
    for _ in range(1, length):
        nxt = {}
        for (last, run), mass in alive.items():
            for bit in (0, 1):
                count = run + 1 if bit == last else 1
                if count < cutoff:
                    key = (bit, count)
                    nxt[key] = nxt.get(key, Fraction(0)) + mass * weights[bit]
        alive = nxt
    return 1 - sum(alive.values(), Fraction(0))


def union_bound(length: int, cutoff: int, q: Fraction) -> Fraction:
    """Cota bajo P(Bt=b|pasado)≤q para toda historia con probabilidad positiva.

    No requiere IID. La premisa condicional debe justificarse externamente.
    """
    if type(length) is not int or length < 0 or type(cutoff) is not int or cutoff < 2:
        raise ValueError("length no negativo y cutoff≥2 requeridos")
    if not isinstance(q, Fraction) or not Fraction(1, 2) <= q <= 1:
        raise ValueError("q debe ser Fraction en [1/2,1]")
    return min(Fraction(1), max(0, length - cutoff + 1) * q ** (cutoff - 1))


def main() -> None:
    rows = []
    for length, cutoff, p in ((21, 21, Fraction(1, 2)), (1024, 21, Fraction(1, 2)),
                              (4096, 21, Fraction(1, 2)), (1024, 11, Fraction(3, 5))):
        exact = alarm_probability_iid(length, cutoff, p)
        upper = union_bound(length, cutoff, max(p, 1 - p))
        rows.append({"length": length, "cutoff": cutoff, "p_one": str(p),
                     "alarm_probability_exact": str(exact), "alarm_probability": float(exact),
                     "conditional_bound_exact": str(upper), "conditional_bound": float(upper)})
    result = {"model": "synthetic_iid_bernoulli_only", "rows": rows,
              "correlated_counterexample": {
                  "source": "B1 uniform; Bt=B1 for all t", "marginal_min_entropy_bits": 1,
                  "alarm_probability_for_n_at_least_cutoff": 1,
                  "conditional_min_entropy_after_first_bit": 0}}
    target = Path(__file__).resolve().parent / "results" / "rct_risk.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    for row in rows:
        print(f"n={row['length']} C={row['cutoff']} p={row['p_one']}: "
              f"P(alarm)={row['alarm_probability']:.12g}; bound={row['conditional_bound']:.12g}")


if __name__ == "__main__":
    main()
