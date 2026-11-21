"""Generate the paper's synthetic sensitivity analysis with the reviewed rate model."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rate_budget import budget

ROOT = Path(__file__).resolve().parents[1]


def main():
    kernels = json.loads((ROOT / "experiments" / "results.json").read_text())["kernels"]
    profiles = (("ais", "AES/SHA", kernels["ais_aes_sha"]["median_Mbit_s"], "#234f77"),
                ("ctr", "CTR directo", kernels["ctr_v"]["median_Mbit_s"], "#a14a22"))
    fig, (supply, quality) = plt.subplots(1, 2, figsize=(8.5, 3.55))
    speeds = range(1, 501)
    quality_grid = [i/100 for i in range(10, 101)]
    for mode, label, cap, color in profiles:
        speed_rows = [budget(mode, raw_samples_s=y*1e6, core_mbit_s=cap) for y in speeds]
        supply.plot(speeds, [r["port_bit_s"]/1e6 for r in speed_rows], color=color, label=label)
        rows = [budget(mode, raw_samples_s=2e8, entropy_per_sample=h, core_mbit_s=cap)
                for h in quality_grid]
        quality.plot(quality_grid, [r["port_hmin_s"]/1e6 for r in rows], color=color)
        quality.axhline(rows[0]["port_bit_s"]/1e6, linestyle=":", linewidth=1, color=color)
    supply.set(xlabel="Millones de muestras/s", ylabel="Millones de bits/s",
               title="Bits emitidos con h = 0,75", xlim=(0,500), ylim=(0,28))
    quality.set(xlabel="Minentropía por muestra (h)", ylabel="Millones de bits/s",
                title="Crédito con 200 Mmuestras/s", xlim=(.1,1), ylim=(0,18))
    # Minimum h for the illustrative lifetime TV target, including selector error.
    lo, hi = 0.1, 1.
    for _ in range(50):
        mid = (lo+hi)/2
        if budget("ais",entropy_per_sample=mid)["block_tv_bound"]*2**32 <= 2**-64:
            hi = mid
        else:
            lo = mid
    quality.axvspan(.1,hi,color="#888888",alpha=.12,linewidth=0)
    for ax in (supply,quality):
        ax.spines[["top","right"]].set_visible(False)
        ax.grid(axis="y", linewidth=.5, alpha=.35)
    fig.legend(*supply.get_legend_handles_labels(), loc="upper center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0,0,1,.90))
    fig.savefig(ROOT/"figures"/"port-rates.pdf", metadata={"CreationDate":None,"ModDate":None})


if __name__ == "__main__":
    main()
