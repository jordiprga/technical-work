import math
import unittest
from collections import defaultdict
from fractions import Fraction
from leakage import (count_transcript, exact_threshold_trace, fair_source, measure,
                     paired_source, reconstruct_rolling, recover_counts)


class DisclosureTests(unittest.TestCase):
    def test_single_bit_update_reveals_every_bit(self):
        for source in (fair_source(8), paired_source(4)):
            result = measure(source, 1, 1)
            self.assertEqual(result['guess_probability_exact'], '1')
            self.assertEqual(result['average_conditional_min_entropy'], 0)

    def test_disjoint_formula_exact(self):
        for window, blocks in [(2, 4), (3, 3), (4, 3)]:
            result = measure(fair_source(window*blocks), window, window)
            expected = Fraction((window+1)**blocks, 2**(window*blocks))
            self.assertEqual(Fraction(result['guess_probability_exact']), expected)

    def test_raw_feedback_pair_entropy_is_not_secret_after_telemetry(self):
        result = measure(paired_source(6), 1, 1)
        self.assertEqual(result['unconditional_min_entropy'], 6)
        self.assertEqual(result['average_conditional_min_entropy'], 0)

    def test_reconstruction_matches_exhaustive_partition(self):
        groups = defaultdict(set)
        for word in fair_source(10):
            groups[count_transcript(word, 4, 1)].add(word)
        for trace, words in groups.items():
            self.assertEqual(set(reconstruct_rolling(trace, 4)), words)
            self.assertLessEqual(len(words), math.comb(4, trace[0]))

    def test_threshold_recovery_without_float_rounding(self):
        word = (1, 0, 1, 1, 0, 0, 1, 0, 0, 1)
        for window, period in [(1, 1), (4, 1), (4, 4)]:
            trace = exact_threshold_trace(word, window, period, Fraction(7, 11), Fraction(2, 5))
            self.assertEqual(recover_counts(trace, window, Fraction(7, 11), Fraction(2, 5)),
                             count_transcript(word, window, period))

    def test_no_gain_cannot_be_inverted(self):
        with self.assertRaises(ValueError):
            recover_counts((Fraction(), Fraction()), 4, Fraction())

    def test_general_update_period_transcript_cardinality_bounds(self):
        for n, window, period in [(8, 4, 2), (12, 6, 2), (12, 6, 3), (12, 9, 3)]:
            result = measure(fair_source(n), window, period)
            groups, overlap = n//period, window//period
            self.assertGreaterEqual(result['distinct_transcripts'], (period+1)**(groups-overlap+1))
            self.assertLessEqual(result['distinct_transcripts'], (period+1)**groups)

    def test_inconsistent_rolling_transcript_has_no_preimage(self):
        self.assertEqual(reconstruct_rolling((0, 4), 4), [])

    def test_nonbinary_input_rejected(self):
        with self.assertRaises(ValueError):
            count_transcript((0, 2), 1, 1)


if __name__ == '__main__':
    unittest.main()
