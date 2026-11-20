"""Descriptive checks on the emitted bit stream of four synthetic configurations."""
import hashlib
import json
import math

from profiles import ZERO16, ais_instantiate, ais_step, ctr_step, generate, instantiate

EPOCHS, REQUESTS, COMPARISONS = 16, 1024, 12
FAMILY_ALPHA = 0.01
ALTERNATE = int('55' * 16, 16)


def synthetic(label, length):
    return hashlib.shake_256(label.encode()).digest(length)


def summarize(ones, trials):
    # Two-sided Hoeffding under a reference of fair, independent bits.
    limit = math.sqrt(trials / 2 * math.log(2 * COMPARISONS / FAMILY_ALPHA))
    return {"ones": ones, "trials": trials, "max_abs_deviation": round(limit, 4),
            "inside_reference_band": abs(ones - trials / 2) < limit}


def measure(profile, injected):
    frequency = within = temporal = 0
    digest = hashlib.sha256()
    for epoch in range(EPOCHS):
        material = synthetic(f"PTG3/diagnostics/seed/{epoch}", 48)
        state = (ais_instantiate(material[:16], material[16:32]) if profile == "AES/SHA"
                 else instantiate(material))
        previous = 0
        for i in range(REQUESTS):
            block = synthetic(f"PTG3/diagnostics/A/{epoch}/{i}", 16) if injected else ZERO16
            if profile == "AES/SHA":
                out, state = ais_step(state, block)
            elif injected:
                out, state = ctr_step(state, block)
            else:
                out, state = generate(state, 1)
            digest.update(out)
            number = int.from_bytes(out, "big")
            frequency += number.bit_count()
            within += ((number ^ (number >> 1)) & ALTERNATE).bit_count()
            if i % 2:
                temporal += (number ^ previous).bit_count()
            previous = number
    bits = 128 * EPOCHS * REQUESTS
    return {"mode": "synthetic_injection" if injected else "autonomous",
            "profile": profile, "stream_sha256": digest.hexdigest(),
            "ones": summarize(frequency, bits),
            "xor_within_disjoint_pairs": summarize(within, bits // 2),
            "xor_adjacent_disjoint_blocks": summarize(temporal, bits // 2)}


if __name__ == "__main__":
    print(json.dumps({"epochs": EPOCHS, "calls_per_epoch": REQUESTS,
                      "family_alpha": FAMILY_ALPHA, "comparisons": COMPARISONS,
                      "reference": "iid fair bits; union bound over the 12 comparisons",
                      "outputs": [measure(profile, injected)
                                  for profile in ("AES/SHA", "CTR")
                                  for injected in (False, True)]}, indent=2))
