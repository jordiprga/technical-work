import unittest
from rate_budget import budget, resolve_raw_rates


class RateBudgetTests(unittest.TestCase):
    def test_unit_conversion_and_allocation(self):
        r = budget("ais")
        self.assertEqual(r["raw_bit_s"], 1e8)
        self.assertEqual(r["raw_hmin_s"], .75e8)
        self.assertEqual((r["data_columns"], r["selector_bits"], r["selector_samples"]), (427, 554, 1108))
        self.assertAlmostEqual(r["target_calls_s"], 1e8 * .99 / 1567 * 1024 / 1026)
        self.assertLess(r["port_hmin_s"], r["port_bit_s"])
        self.assertGreater(r["kappa"], 127.99999999)

    def test_packing_and_cmac(self):
        r = budget("ctr_cmac", sample_bits=8, samples_per_data=54)
        self.assertEqual((r["data_columns"], r["selector_bits"], r["selector_samples"]), (432,559,140))
        self.assertEqual(r["toeplitz_blocks_per_epoch"], 2054)
        self.assertEqual(budget("rs_cmac")["toeplitz_blocks_per_epoch"], 6150)
        self.assertEqual(budget("ctr_seed_cmac")["toeplitz_blocks_per_epoch"], 1030)

    def test_slow_core(self):
        r = budget("ctr", core_mbit_s=1)
        self.assertAlmostEqual(r["port_bit_s"], 1e6)
        self.assertLess(r["serial_bit_s"], r["port_bit_s"])

    def test_no_credit_or_no_output(self):
        self.assertEqual(budget("ais", entropy_per_sample=0)["port_hmin_s"], 0)
        self.assertEqual(budget("ctr", raw_samples_s=0)["port_bit_s"], 0)
        self.assertEqual(budget("ais", acceptance=0)["port_hmin_s"], 0)
        self.assertEqual(budget("ais", selector_error=1)["kappa"], 0)

    def test_out_of_domain(self):
        with self.assertRaises(ValueError):
            budget("ais", entropy_per_sample=2)
        with self.assertRaises(ValueError):
            budget("xor_cmac", epoch_calls=1025)


    def test_direct_raw_rates(self):
        self.assertEqual(resolve_raw_rates(100e6, 75e6, 8, None, None), (12.5e6, 6))
        self.assertEqual(resolve_raw_rates(0, 0, 1, None, None), (0, 0))
        for args in [(10, 11, 1, None, None), (10, 3, 1, None, .3), (10, 3, 1, 10, None)]:
            with self.assertRaises(ValueError):
                resolve_raw_rates(*args)

    def test_small_entropy_deficit(self):
        r = budget("ais", samples_per_data=2000, selector_error=0)
        self.assertGreater(r["entropy_deficit_bound"], 0)
        self.assertLess(r["kappa"], 128)
