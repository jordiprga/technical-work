from fractions import Fraction
from itertools import product
import unittest

from rct_risk import alarm_probability_iid, union_bound


def reference_fails(bits, cutoff):
    return any(len(set(bits[start:start + cutoff])) == 1
               for start in range(len(bits) - cutoff + 1))


class RiskTests(unittest.TestCase):
    def test_matches_independent_exhaustive_windows(self):
        for p in (Fraction(1, 2), Fraction(1, 3), Fraction(4, 5)):
            for n in range(1, 10):
                for cutoff in (2, 3, 5):
                    expected = sum((p ** sum(bits) * (1 - p) ** (n - sum(bits))
                                    for bits in product((0, 1), repeat=n)
                                    if reference_fails(bits, cutoff)), Fraction(0))
                    self.assertEqual(alarm_probability_iid(n, cutoff, p), expected)

    def test_first_full_window_formula(self):
        for cutoff in (2, 7, 21):
            p = Fraction(3, 5)
            self.assertEqual(alarm_probability_iid(cutoff, cutoff, p),
                             p ** cutoff + (1 - p) ** cutoff)

    def test_below_cutoff_never_fails(self):
        self.assertEqual(alarm_probability_iid(20, 21, Fraction(1, 2)), 0)
        self.assertEqual(alarm_probability_iid(0, 21, Fraction(1, 2)), 0)

    def test_deterministic_source(self):
        for p in (Fraction(0), Fraction(1)):
            self.assertEqual(alarm_probability_iid(21, 21, p), 1)

    def test_union_bound_dominates_exact_iid(self):
        for p in (Fraction(1, 2), Fraction(3, 4)):
            for n in (10, 50, 100):
                self.assertLessEqual(alarm_probability_iid(n, 7, p),
                                     union_bound(n, 7, max(p, 1 - p)))

    def test_rejects_float_probabilities(self):
        with self.assertRaises(ValueError):
            alarm_probability_iid(10, 5, 0.5)
        with self.assertRaises(ValueError):
            union_bound(10, 5, 0.5)


if __name__ == "__main__":
    unittest.main()
