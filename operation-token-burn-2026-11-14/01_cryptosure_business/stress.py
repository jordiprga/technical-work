#!/usr/bin/env python3
"""Deterministic sensitivities: these scenarios have no assigned probabilities."""
from dataclasses import replace
from pathlib import Path
import json

from model import default_ramps, simulate, write_csv


def shifted(values, months):
    if type(months) is not int or not 0 <= months <= len(values):
        raise ValueError("delay must be an integer inside the simulation horizon")
    return tuple([0] * months + list(values[:len(values)-months])) if months else values


def main():
    base = default_ramps()[1]
    cases = [
        base,
        replace(base, name="ventas_retraso_3m", new_accounts=shifted(base.new_accounts, 3)),
        replace(base, name="ventas_retraso_6m", new_accounts=shifted(base.new_accounts, 6)),
        replace(base, name="acv_menos_30pct", acv=base.acv*.7),
        replace(base, name="margen_60pct", gross_margin=.6),
        replace(base, name="adquisicion_doble", incremental_acquisition_cost=12000),
        replace(base, name="coste_fijo_mas_25pct", fixed_monthly_cost=base.fixed_monthly_cost*1.25,
                fixed_cost_steps=tuple((m,c*1.25) for m,c in base.fixed_cost_steps)),
        replace(base, name="combinado_adverso", acv=base.acv*.8, gross_margin=.7,
                incremental_acquisition_cost=9000, new_accounts=shifted(base.new_accounts, 6),
                fixed_monthly_cost=base.fixed_monthly_cost*1.25,
                fixed_cost_steps=tuple((m,c*1.25) for m,c in base.fixed_cost_steps)),
    ]
    summaries = []
    for case in cases:
        rows = simulate(case)
        minimum = min([case.initial_cash] + [r["cash_eur"] for r in rows])
        summaries.append({"case": case.name, "arr_month_36_eur": rows[-1]["arr_eur"],
                          "minimum_cash_eur": minimum,
                          "minimum_initial_cash_eur": case.initial_cash - minimum,
                          "additional_funding_over_500k_eur": max(0, -minimum),
                          "first_negative_balance_month": next((r["month"] for r in rows if r["cash_eur"] < 0), None),
                          "operating_cash_month_36_eur": rows[-1]["net_operating_cash_eur"]})
    out = Path(__file__).parent / "results"
    write_csv(out / "stress.csv", summaries)
    (out / "stress.json").write_text(json.dumps({
        "disclaimer": "No probabilities, forecasts or capacity validation. Cost hiring schedule is not delayed when sales are delayed.",
        "cases": summaries}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in summaries:
        print(f"{row['case']}: minimum starting cash {row['minimum_initial_cash_eur']:,.0f} EUR; "
              f"first negative month with 500k={row['first_negative_balance_month']}")


if __name__ == "__main__":
    main()
