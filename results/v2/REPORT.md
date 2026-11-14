# Measured results — v0.2

Generated directly from 9 saved benchmark JSON files. Seeds: [211, 229, 247]. Accuracy SD describes seed variability, not a confidence interval. CPU timings can vary with concurrent load.

All 14 base predictors were trained and evaluated. The MLP now restores the checkpoint with minimum temporal validation log-loss. Previous v0.1 data remain separately archived; version comparisons using different seeds are descriptive, not paired causal claims.

| Source | Predictor | Accuracy mean | Seed SD | Log-loss bits | Fit seconds mean |
|---|---|---:|---:|---:|---:|
| nonlinear | marginal | 0.24681 | 0.00591 | 2.00029 | 0.001 |
| nonlinear | markov1 | 0.24444 | 0.00376 | 2.00062 | 0.010 |
| nonlinear | markov2 | 0.25056 | 0.01018 | 2.00345 | 0.008 |
| nonlinear | markov3 | 0.24194 | 0.01179 | 2.01973 | 0.010 |
| nonlinear | markov4 | 0.28875 | 0.02107 | 2.03876 | 0.012 |
| nonlinear | markov5 | 0.27514 | 0.02073 | 2.30510 | 0.021 |
| nonlinear | ppm | 0.27069 | 0.01354 | 2.86888 | 0.401 |
| nonlinear | lz78 | 0.26111 | 0.01069 | 2.39265 | 0.009 |
| nonlinear | gb | 0.49181 | 0.00461 | 1.24536 | 0.882 |
| nonlinear | rf | 0.49028 | 0.00197 | 1.35015 | 0.857 |
| nonlinear | mlp | 0.47875 | 0.00753 | 1.31396 | 0.397 |
| nonlinear | gru | 0.48764 | 0.00479 | 1.24979 | 5.976 |
| nonlinear | transformer | 0.48167 | 0.00832 | 1.26287 | 5.383 |
| nonlinear | flow | 0.47111 | 0.00387 | 1.25614 | 1.414 |
| nonlinear | selected | 0.48542 | 0.01324 | 1.29338 | 15.388 |
| nonlinear | ensemble | 0.48444 | 0.00747 | 1.22578 | 15.388 |
| nonlinear | oracle | 0.48889 | 0.00646 | 1.19578 | 0.000 |
| bernoulli | marginal | 0.81771 | 0.01721 | 0.68809 | 0.000 |
| bernoulli | markov1 | 0.81771 | 0.01721 | 0.68946 | 0.001 |
| bernoulli | markov2 | 0.81771 | 0.01721 | 0.69170 | 0.001 |
| bernoulli | markov3 | 0.81771 | 0.01721 | 0.69513 | 0.001 |
| bernoulli | markov4 | 0.81771 | 0.01721 | 0.70020 | 0.001 |
| bernoulli | markov5 | 0.81667 | 0.01721 | 0.70602 | 0.001 |
| bernoulli | ppm | 0.76042 | 0.01183 | 1.10531 | 0.026 |
| bernoulli | lz78 | 0.76354 | 0.02345 | 0.83692 | 0.001 |
| bernoulli | gb | 0.79167 | 0.00955 | 0.79924 | 0.134 |
| bernoulli | rf | 0.81771 | 0.01721 | 0.70883 | 0.227 |
| bernoulli | mlp | 0.81771 | 0.01721 | 0.70691 | 0.114 |
| bernoulli | gru | 0.81771 | 0.01721 | 0.69357 | 1.345 |
| bernoulli | transformer | 0.81771 | 0.01721 | 0.70611 | 0.761 |
| bernoulli | flow | 0.81771 | 0.01721 | 0.69546 | 0.213 |
| bernoulli | selected | 0.81771 | 0.01721 | 0.69239 | 2.836 |
| bernoulli | ensemble | 0.81771 | 0.01721 | 0.69849 | 2.836 |
| bernoulli | oracle | 0.81771 | 0.01721 | 0.68651 | 0.000 |
| ar1 | marginal | 0.31347 | 0.04372 | 2.31511 | 0.001 |
| ar1 | markov1 | 0.70028 | 0.00709 | 1.15031 | 0.012 |
| ar1 | markov2 | 0.70000 | 0.00655 | 1.11913 | 0.013 |
| ar1 | markov3 | 0.69819 | 0.00567 | 1.13271 | 0.016 |
| ar1 | markov4 | 0.69431 | 0.00747 | 1.16379 | 0.022 |
| ar1 | markov5 | 0.68250 | 0.00473 | 1.21532 | 0.023 |
| ar1 | ppm | 0.60458 | 0.01173 | 1.98773 | 0.338 |
| ar1 | lz78 | 0.60153 | 0.02167 | 1.64008 | 0.009 |
| ar1 | gb | 0.67556 | 0.01171 | 1.19627 | 1.759 |
| ar1 | rf | 0.67833 | 0.00751 | 1.19538 | 0.857 |
| ar1 | mlp | 0.68236 | 0.00988 | 1.21852 | 0.438 |
| ar1 | gru | 0.68792 | 0.01052 | 1.19420 | 5.749 |
| ar1 | transformer | 0.67597 | 0.01203 | 1.22468 | 4.114 |
| ar1 | flow | 0.69694 | 0.00809 | 1.14761 | 1.146 |
| ar1 | selected | 0.70014 | 0.00646 | 1.12924 | 14.505 |
| ar1 | ensemble | 0.69986 | 0.00664 | 1.11894 | 14.505 |

## Simultaneous nonlinear contrasts

Two-sided paired conditional Hoeffding bounds, Bonferroni over all 9 contrasts across the recorded seeds; family coverage at least 95%. Target: realized trajectory-average conditional success difference. These are not future-population guarantees.

| Seed | A vs Markov-5 | Accuracy difference | Simultaneous lower | Simultaneous upper |
|---:|---|---:|---:|---:|---:|
| 211 | selected | 0.23542 | 0.16538 | 0.30545 |
| 211 | ensemble | 0.23500 | 0.16496 | 0.30504 |
| 211 | transformer | 0.21875 | 0.14871 | 0.28879 |
| 229 | selected | 0.17625 | 0.10621 | 0.24629 |
| 229 | ensemble | 0.18125 | 0.11121 | 0.25129 |
| 229 | transformer | 0.19250 | 0.12246 | 0.26254 |
| 247 | selected | 0.21917 | 0.14913 | 0.28920 |
| 247 | ensemble | 0.21167 | 0.14163 | 0.28170 |
| 247 | transformer | 0.20833 | 0.13830 | 0.27837 |

9 of 9 family-adjusted lower bounds are positive. RF and boosting also exploit the nonlinear source; these data do not establish superiority of attention or flows over all shallow ML.

Nonlinear source: exact marginal min-entropy 2 bits; full-history optimal success 0.485; average conditional min-entropy and block min-entropy rate 1.043943 bits; Shannon entropy rate 1.194392 bits. These identities follow from this specified source, not from trained models.

AR(1): the metadata numerical bound uses the latent previous continuous state. No exact observed-quantized-history oracle is claimed.

Every run includes a complete compressed NPZ with labels, target indices and all test probabilities. SHA-256 and metrics are independently checked with `python scripts/verify_results.py results/v2 --require-audit`. This detects inconsistency or corruption; a hash does not prove the absence of methodological error.

Policy costs include the candidate search and selected/ensemble inference components; original model rows report their individual fit and test-only inference. RSS is whole-process sampled memory.

Exploratory block bootstrap is suppressed when the declared source is nonstationary or of unknown stationarity. Martingale intervals remain available. Learning curves use a separate seed 201 with fixed validation/test segments and are exploratory.
