import math
import unittest
from dataclasses import replace

from model import Ramp, default_ramps, simulate, unit_economics, valuation_accounts


class EconomicsTest(unittest.TestCase):
    def test_valuation_rounds_up_actual_accounts(self):
        row = valuation_accounts(1_000_000, 3, 25_000)
        self.assertEqual(row["accounts_rounded_up"], 14)
        self.assertGreaterEqual(row["accounts_rounded_up"] * 25_000 * 3, 1_000_000)

    def test_unit_economics_has_monthly_payback_units(self):
        row = unit_economics(30000, .8, 12000, .9, 360000, 6000)
        self.assertEqual(row["cac_payback_months"], 6)
        self.assertEqual(row["accounts_to_cover_fixed_cost_before_replacement"], 15)
        self.assertEqual(row["accounts_to_cover_fixed_cost_with_replacement"], 16)

    def test_no_churn_does_not_claim_finite_ltv(self):
        self.assertIsNone(unit_economics(30000, .8, 12000, 1, 360000, 6000)["simple_ltv_eur"])

    def test_full_cac_does_not_double_count_fixed_sales_cost(self):
        lower = unit_economics(30000, .8, 12000, .9, 360000, 6000)
        higher = unit_economics(30000, .8, 25000, .9, 360000, 6000)
        self.assertGreater(higher["cac_payback_months"], lower["cac_payback_months"])
        self.assertEqual(higher["accounts_to_cover_fixed_cost_with_replacement"],
                         lower["accounts_to_cover_fixed_cost_with_replacement"])

    def test_retention_conversion_matches_annual_contract(self):
        ramp = Ramp("test", 12000, 1, .81, 1, 0, 0, 0, 1000, (100,) + (0,)*12)
        rows = simulate(ramp)
        self.assertAlmostEqual(rows[-1]["expected_active_accounts"], 81)

    def test_onboarding_is_not_arr(self):
        ramp = Ramp("test", 12000, .5, 1, 100, 200, 1000, 300, 5000, (1,))
        row = simulate(ramp)[0]
        self.assertEqual(row["arr_eur"], 12000)
        self.assertEqual(row["net_operating_cash_eur"], 900)
        self.assertEqual(row["cash_eur"], 5900)

    def test_cash_reconciliation(self):
        for ramp in default_ramps():
            rows = simulate(ramp)
            self.assertAlmostEqual(rows[-1]["cash_eur"], ramp.initial_cash + sum(r["net_operating_cash_eur"] for r in rows))

    def test_cost_steps_are_levels_and_apply_at_boundary(self):
        ramp = Ramp("test", 12000, 1, 1, 100, 0, 0, 0, 1000,
                    (0, 0, 0), ((2, 200), (3, 250)))
        rows = simulate(ramp)
        self.assertEqual([r["fixed_cost_eur"] for r in rows], [100, 200, 250])
        self.assertEqual(rows[-1]["cash_eur"], 450)

    def test_reject_invalid_values(self):
        for multiple in (0, -1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                valuation_accounts(1_000_000, multiple, 25000)
        for retention in (0, -1, 1.01, math.nan):
            with self.assertRaises(ValueError):
                simulate(replace(default_ramps()[0], annual_retention=retention))
        with self.assertRaises(ValueError):
            simulate(replace(default_ramps()[0], new_accounts=(1.5,)))


if __name__ == "__main__":
    unittest.main()
