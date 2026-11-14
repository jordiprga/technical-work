#!/usr/bin/env python3
"""Illustrative CryptoSure economics. EUR, synthetic assumptions, no network."""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


def positive(value: float, name: str) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive")


def valuation_accounts(enterprise_value: float, arr_multiple: float, acv: float) -> dict:
    for value, name in [(enterprise_value, "enterprise_value"), (arr_multiple, "arr_multiple"), (acv, "acv")]:
        positive(value, name)
    arr = enterprise_value / arr_multiple
    return {"enterprise_value_eur": enterprise_value, "arr_multiple": arr_multiple,
            "acv_eur": acv, "required_arr_eur": arr,
            "accounts_rounded_up": math.ceil(arr / acv)}


def unit_economics(acv: float, gross_margin: float, fully_loaded_cac: float,
                   annual_logo_retention: float, fixed_annual_cost: float,
                   incremental_replacement_cac: float) -> dict:
    for value, name in [(acv, "acv"), (fully_loaded_cac, "fully_loaded_cac"), (fixed_annual_cost, "fixed_annual_cost")]:
        positive(value, name)
    if not 0 < gross_margin <= 1 or not 0 < annual_logo_retention <= 1:
        raise ValueError("margin and retention must lie in (0, 1]")
    if not math.isfinite(incremental_replacement_cac) or incremental_replacement_cac < 0:
        raise ValueError("incremental replacement CAC must be finite and nonnegative")
    annual_contribution = acv * gross_margin
    churn = 1 - annual_logo_retention
    # Fixed GTM cost is already in fixed_annual_cost. Only incremental replacement
    # cost belongs here; full CAC is used separately for payback/LTV efficiency.
    replacement_contribution = annual_contribution - churn * incremental_replacement_cac
    # Simple steady-state undiscounted approximation, not a company valuation.
    ltv = annual_contribution / churn if churn else None
    return {"acv_eur": acv, "gross_margin": gross_margin, "fully_loaded_cac_eur": fully_loaded_cac,
            "annual_logo_retention": annual_logo_retention,
            "incremental_replacement_cac_eur": incremental_replacement_cac,
            "annual_gross_profit_per_account_eur": annual_contribution,
            "cac_payback_months": 12 * fully_loaded_cac / annual_contribution,
            "simple_ltv_eur": ltv,
            "simple_ltv_cac_ratio": None if ltv is None else ltv / fully_loaded_cac,
            "accounts_to_cover_fixed_cost_before_replacement": math.ceil(fixed_annual_cost / annual_contribution),
            "accounts_to_cover_fixed_cost_with_replacement": None if replacement_contribution <= 0 else math.ceil(fixed_annual_cost / replacement_contribution)}


@dataclass(frozen=True)
class Ramp:
    name: str
    acv: float
    gross_margin: float
    annual_retention: float
    fixed_monthly_cost: float
    incremental_acquisition_cost: float
    onboarding_fee: float
    onboarding_delivery_cost: float
    initial_cash: float
    new_accounts: tuple[int, ...]
    # Additional fixed cost levels from the given month, not increments.
    fixed_cost_steps: tuple[tuple[int, float], ...] = ()

    def validate(self) -> None:
        for key in ("acv", "fixed_monthly_cost"):
            positive(getattr(self, key), key)
        for key in ("incremental_acquisition_cost", "onboarding_fee", "onboarding_delivery_cost", "initial_cash"):
            value = getattr(self, key)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{key} must be finite and nonnegative")
        if not 0 < self.gross_margin <= 1 or not 0 < self.annual_retention <= 1:
            raise ValueError("margin and retention must lie in (0, 1]")
        if not self.new_accounts or any(type(n) is not int or n < 0 for n in self.new_accounts):
            raise ValueError("new_accounts must contain nonnegative integers")
        previous = 0
        for month, amount in self.fixed_cost_steps:
            if type(month) is not int or month <= previous or month > len(self.new_accounts):
                raise ValueError("cost-step months must increase within the simulation horizon")
            positive(amount, "fixed_cost_step")
            previous = month


def simulate(ramp: Ramp) -> list[dict]:
    """Expected accounts, monthly collections; no annual-prepay cash advantage.

    New accounts arrive at start of month; existing accounts churn at that point.
    Fractional active accounts represent a cohort expectation, not actual contracts.
    Costs and revenue are pre-tax; balances may go negative to expose funding needs.
    """
    ramp.validate()
    monthly_retention = ramp.annual_retention ** (1 / 12)
    accounts = 0.0
    cash = ramp.initial_cash
    rows = []
    for month, new in enumerate(ramp.new_accounts, start=1):
        fixed_cost = ramp.fixed_monthly_cost
        for step_month, step_cost in ramp.fixed_cost_steps:
            if step_month <= month:
                fixed_cost = step_cost
        churned = accounts * (1 - monthly_retention)
        accounts = accounts * monthly_retention + new
        arr = accounts * ramp.acv
        subscription_revenue = arr / 12
        onboarding_revenue = new * ramp.onboarding_fee
        gross_profit = subscription_revenue * ramp.gross_margin
        onboarding_contribution = new * (ramp.onboarding_fee - ramp.onboarding_delivery_cost)
        acquisition_expense = new * ramp.incremental_acquisition_cost
        net_cash = gross_profit + onboarding_contribution - fixed_cost - acquisition_expense
        cash += net_cash
        rows.append({"scenario": ramp.name, "month": month, "new_accounts": new,
                     "expected_churned_accounts": churned, "expected_active_accounts": accounts,
                     "arr_eur": arr, "subscription_revenue_eur": subscription_revenue,
                     "onboarding_revenue_eur": onboarding_revenue,
                     "subscription_gross_profit_eur": gross_profit,
                     "onboarding_contribution_eur": onboarding_contribution,
                     "incremental_acquisition_expense_eur": acquisition_expense,
                     "fixed_cost_eur": fixed_cost,
                     "net_operating_cash_eur": net_cash, "cash_eur": cash})
    return rows


def default_ramps() -> tuple[Ramp, ...]:
    common = dict(fixed_monthly_cost=30000, incremental_acquisition_cost=6000,
                  onboarding_fee=5000, onboarding_delivery_cost=4000, initial_cash=500000)
    return (
        Ramp("conservador", acv=24000, gross_margin=.7, annual_retention=.85,
             new_accounts=tuple([0]*6 + [1]*18 + [2]*12), **common),
        Ramp("base", acv=30000, gross_margin=.8, annual_retention=.9,
             new_accounts=tuple([0]*3 + [1]*6 + [2]*9 + [3]*18),
             fixed_cost_steps=((19, 45000), (31, 60000)), **common),
        Ramp("expansion", acv=42000, gross_margin=.85, annual_retention=.95,
             new_accounts=tuple([0]*3 + [1]*3 + [2]*6 + [4]*12 + [6]*12),
             fixed_cost_steps=((13, 50000), (25, 80000)), **common),
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("cannot write empty table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    valuation = [valuation_accounts(value, multiple, acv)
                 for value in (1_000_000, 10_000_000, 100_000_000)
                 for multiple in (3, 5, 8, 12) for acv in (25000, 50000, 75000)]
    units = [unit_economics(acv, margin, cac, retention, 360000, 6000)
             for acv in (12000, 30000, 60000) for margin in (.6, .8)
             for cac in (10000, 25000) for retention in (.8, .9, .95)]
    write_csv(out / "valuation_sensitivity.csv", valuation)
    write_csv(out / "unit_economics.csv", units)
    summaries = []
    for ramp in default_ramps():
        rows = simulate(ramp)
        write_csv(out / f"ramp_{ramp.name}.csv", rows)
        min_cash = min([ramp.initial_cash] + [r["cash_eur"] for r in rows])
        first_positive = next((r["month"] for r in rows if r["net_operating_cash_eur"] >= 0), None)
        sustained_positive = next((row["month"] for index, row in enumerate(rows)
                                   if all(r["net_operating_cash_eur"] >= 0 for r in rows[index:])), None)
        first_negative_balance = next((r["month"] for r in rows if r["cash_eur"] < 0), None)
        summaries.append({"scenario": ramp.name, "assumptions": asdict(ramp),
                          "month_12_arr_eur": rows[11]["arr_eur"],
                          "month_24_arr_eur": rows[23]["arr_eur"],
                          "month_36_arr_eur": rows[35]["arr_eur"],
                          "minimum_cash_eur": min_cash,
                          "extra_funding_to_avoid_negative_cash_eur": max(0, -min_cash),
                          "first_month_positive_operating_cash": first_positive,
                          "first_month_nonnegative_cashflow_through_remaining_horizon": sustained_positive,
                          "first_month_negative_cash_balance": first_negative_balance,
                          "month_36_cash_eur": rows[35]["cash_eur"]})
    result = {"disclaimer": "Synthetic illustrative scenarios; not forecasts, market evidence or investment advice.",
              "currency": "EUR", "fixed_annual_cost_eur": 360000,
              "cash_method": "monthly collections, no financing, tax, VAT, working capital lag or annual upfront benefit",
              "valuation_formula": "enterprise_value = ARR * assumed_multiple; equity_value requires debt/cash bridge",
              "ramps": summaries}
    (out / "summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    result = generate(args.out)
    for row in result["ramps"]:
        print(f"{row['scenario']}: ARR m36={row['month_36_arr_eur']:,.0f} EUR; "
              f"minimum cash={row['minimum_cash_eur']:,.0f} EUR; "
              f"first positive monthly cash={row['first_month_positive_operating_cash']}; "
              f"nonnegative to horizon from={row['first_month_nonnegative_cashflow_through_remaining_horizon']}")
