#!/usr/bin/env python3
"""Revisión independiente finita del algoritmo del coordinador, sin modificarlo."""
from collections import defaultdict
from fractions import Fraction
import hashlib
import importlib.util
from itertools import product
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "00_coordination" / "feedback_leakage" / "leakage.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location("reviewed_leakage", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scenarios = words = transcripts = 0
    for width in range(1, 7):
        for length in range(width, width + 6):
            groups = defaultdict(set)
            for bits in product((0, 1), repeat=length):
                groups[module.count_transcript(bits, width, 1)].add(bits)
                words += 1
            for counts, expected in groups.items():
                actual = set(module.reconstruct_rolling(counts, width))
                if actual != expected:
                    raise AssertionError((width, length, counts, actual, expected))
                if len(actual) > math.comb(width, counts[0]):
                    raise AssertionError("Violación de cota de soporte binomial")
                transcripts += 1
            scenarios += 1
    source = {(0, 0): Fraction(1, 2), (0, 1): Fraction(1, 4),
              (1, 0): Fraction(1, 8), (1, 1): Fraction(1, 8)}
    nonuniform = module.measure(source, 2, 2)
    if Fraction(nonuniform["guess_probability_exact"]) != Fraction(7, 8):
        raise AssertionError("Falla referencia no uniforme 7/8")
    report = {
        "review_kind": "independent_exhaustive_reconstruction_check",
        "reviewed_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "widths": list(range(1, 7)), "length_range": "n=W..W+5",
        "parameter_cases": scenarios, "words_checked": words,
        "transcript_groups_checked": transcripts,
        "nonuniform_reference": nonuniform, "status": "passed",
    }
    out = ROOT / "results" / "feedback_review.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {scenarios} escenarios, {words} palabras, {transcripts} transcripts; Pguess=7/8")


if __name__ == "__main__":
    main()
