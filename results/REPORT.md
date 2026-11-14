# Measured results

Generated directly from saved benchmark JSON files. Three independent seeds per source: 11, 29, 47. Accuracy SD describes seed variability, not a confidence interval. CPU timings may vary with concurrent load.

| Source | Predictor | Accuracy mean | Seed SD | Log-loss bits | Fit seconds mean |
|---|---|---:|---:|---:|---:|
| nonlinear | marginal | 0.24944 | 0.01009 | 2.00028 | 0.002 |
| nonlinear | markov1 | 0.24903 | 0.00474 | 2.00100 | 0.012 |
| nonlinear | markov2 | 0.24847 | 0.01265 | 2.00517 | 0.011 |
| nonlinear | markov3 | 0.24861 | 0.01174 | 2.01990 | 0.017 |
| nonlinear | markov4 | 0.28597 | 0.00610 | 2.05249 | 0.018 |
| nonlinear | markov5 | 0.26889 | 0.00277 | 2.31850 | 0.020 |
| nonlinear | ppm | 0.26958 | 0.00125 | 2.87969 | 0.559 |
| nonlinear | lz78 | 0.26653 | 0.00315 | 2.39099 | 0.010 |
| nonlinear | gb | 0.47236 | 0.00963 | 1.25511 | 1.227 |
| nonlinear | rf | 0.47722 | 0.01039 | 1.35679 | 1.199 |
| nonlinear | mlp | 0.46708 | 0.01078 | 5.21095 | 1.654 |
| nonlinear | gru | 0.47472 | 0.00385 | 1.25958 | 8.529 |
| nonlinear | transformer | 0.47722 | 0.02081 | 1.24612 | 4.180 |
| nonlinear | flow | 0.47292 | 0.01242 | 1.26208 | 1.162 |
| nonlinear | selected | 0.47694 | 0.01718 | 1.25548 | 0.000 |
| nonlinear | ensemble | 0.47458 | 0.01086 | 1.22713 | 0.000 |
| nonlinear | oracle | 0.48931 | 0.00858 | 1.19648 | 0.000 |
| bernoulli | marginal | 0.80417 | 0.01604 | 0.71343 | 0.000 |
| bernoulli | markov1 | 0.80417 | 0.01604 | 0.71210 | 0.001 |
| bernoulli | markov2 | 0.80417 | 0.01604 | 0.71458 | 0.001 |
| bernoulli | markov3 | 0.80417 | 0.01604 | 0.72091 | 0.001 |
| bernoulli | markov4 | 0.80312 | 0.01654 | 0.74413 | 0.002 |
| bernoulli | markov5 | 0.79896 | 0.02081 | 0.74589 | 0.002 |
| bernoulli | ppm | 0.74375 | 0.00625 | 1.33068 | 0.031 |
| bernoulli | lz78 | 0.73125 | 0.05422 | 0.87444 | 0.001 |
| bernoulli | gb | 0.79167 | 0.01005 | 0.82412 | 0.141 |
| bernoulli | rf | 0.80417 | 0.01604 | 0.73729 | 0.197 |
| bernoulli | mlp | 0.73958 | 0.00722 | 1.71295 | 0.206 |
| bernoulli | gru | 0.80417 | 0.01604 | 0.71655 | 1.115 |
| bernoulli | transformer | 0.80417 | 0.01604 | 0.73269 | 0.768 |
| bernoulli | flow | 0.80417 | 0.01604 | 0.71748 | 0.212 |
| bernoulli | selected | 0.80417 | 0.01604 | 0.71401 | 0.000 |
| bernoulli | ensemble | 0.80417 | 0.01604 | 0.72125 | 0.000 |
| bernoulli | oracle | 0.80417 | 0.01604 | 0.71359 | 0.000 |
| ar1 | marginal | 0.31194 | 0.04284 | 2.31881 | 0.001 |
| ar1 | markov1 | 0.69986 | 0.01418 | 1.15329 | 0.011 |
| ar1 | markov2 | 0.70042 | 0.01473 | 1.11981 | 0.012 |
| ar1 | markov3 | 0.69889 | 0.01284 | 1.12630 | 0.014 |
| ar1 | markov4 | 0.69500 | 0.01481 | 1.15940 | 0.012 |
| ar1 | markov5 | 0.68264 | 0.01545 | 1.22766 | 0.012 |
| ar1 | ppm | 0.61361 | 0.01428 | 1.99345 | 0.264 |
| ar1 | lz78 | 0.59694 | 0.01128 | 1.64129 | 0.007 |
| ar1 | gb | 0.67375 | 0.01737 | 1.20602 | 1.886 |
| ar1 | rf | 0.67444 | 0.01592 | 1.21025 | 0.702 |
| ar1 | mlp | 0.54097 | 0.00855 | 4.21697 | 1.655 |
| ar1 | gru | 0.68056 | 0.01935 | 1.20450 | 5.020 |
| ar1 | transformer | 0.67972 | 0.01441 | 1.21364 | 3.584 |
| ar1 | flow | 0.69431 | 0.01929 | 1.15058 | 1.042 |
| ar1 | selected | 0.69708 | 0.01627 | 1.15300 | 0.000 |
| ar1 | ensemble | 0.70042 | 0.01393 | 1.11838 | 0.000 |

## Simultaneous nonlinear contrasts

Two-sided paired conditional Hoeffding bounds, Bonferroni over all nine contrasts across the three seeds; family coverage at least 95%. Target: realized trajectory-average conditional success difference. These are not future-population guarantees.

| Seed | A vs Markov-5 | Accuracy difference | Simultaneous lower | Simultaneous upper |
|---:|---|---:|---:|---:|
| 11 | selected | 0.19917 | 0.12913 | 0.26920 |
| 11 | ensemble | 0.20792 | 0.13788 | 0.27795 |
| 11 | transformer | 0.20833 | 0.13830 | 0.27837 |
| 29 | selected | 0.22875 | 0.15871 | 0.29879 |
| 29 | ensemble | 0.21417 | 0.14413 | 0.28420 |
| 29 | transformer | 0.22875 | 0.15871 | 0.29879 |
| 47 | selected | 0.19625 | 0.12621 | 0.26629 |
| 47 | ensemble | 0.19500 | 0.12496 | 0.26504 |
| 47 | transformer | 0.18792 | 0.11788 | 0.25795 |

All nine lower bounds are positive in the recorded experiment. RF and gradient boosting also exploit the nonlinear source; these data do not establish superiority of attention or flows over all shallow ML.

Nonlinear source: exact marginal min-entropy 2 bits; full-history optimal success 0.485; average conditional min-entropy and block min-entropy rate 1.043943 bits; Shannon entropy rate 1.194392 bits. The special equalities follow from the specified source, not from fitted predictors.

AR(1): no exact oracle conditional on quantized history is claimed. The metadata numerical reference has access to the latent previous continuous state and is privileged. Markov-2 has lower mean log-loss than all three advanced architectures on this benchmark.

IID Bernoulli p=0.8, n=1600: the marginal predictor ties the accuracy of GRU/Transformer/flow while giving lower mean log-loss; the fixed-budget MLP overfits. MLP has no validation checkpoint, so this is a pipeline failure, not proof of an inherent architecture limitation.

Learning curves use a separate seed 101 and fixed held-out segments at n=12000. They are exploratory and are not counted as new independent confirmations. All 14 implemented model families were trained and scored on each primary source.
