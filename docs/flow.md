# Conditional rational-quadratic spline flow

For context `c = (x[t-k], ..., x[t-1])`, an MLP emits a location `mu(c)`, positive scale `s(c)`, and the positive widths, heights, and derivatives of an eight-bin monotone rational-quadratic spline `S_c` with identity tails outside `[-4,4]`. Widths and heights use softmax plus a positive floor; interior derivatives use softplus plus a positive floor. End derivatives are one.

Let `U` have the standard logistic distribution and define the invertible conditional generative transform

```
Y = mu(c) + s(c) S_c^{-1}(U).
F_Y(y|c) = sigmoid(S_c((y-mu(c))/s(c))).
```

For alphabet size `A`, the fixed interior edges are `e_j=-3+6j/A`, `j=1,...,A-1`, with `e_0=-infinity`, `e_A=infinity`. The observable is `X=j` exactly when `e_j <= Y < e_{j+1}`. The implemented discrete mass is

```
q_theta(j|c) = F_Y(e_{j+1}|c) - F_Y(e_j|c).
```

Training minimizes the negative logarithm of this **integrated mass**. It is a discrete likelihood, not a differential likelihood or dequantization lower bound. Numerical CDF differences use float64; masses have a `1e-12` numerical floor and are renormalized. Recorded training and validation losses are in bits. Predictions are frozen during final testing; checkpoints use validation log-loss only.

This is a conditional scalar Neural Spline Flow. A MAF over the full window is not implemented: it would model unnecessary context dimensions and consume the fixed experiment budget. The context network can express nonlinear temporal relationships, while the spline allows non-Gaussian conditional shapes. It is not a guarantee of better prediction: bin integration removes information about the within-bin shape, particularly for binary observations where all such flows reduce observationally to Bernoulli conditional probabilities. Many continuous densities induce identical bin masses. There is no claim of identifiable latent density, calibrated physical noise model, or entropy certification.

The source's numerical categories are treated as ordered. No bin edges or context transforms are fitted to test data. If applying the model to physical ADC output, the physical bin boundaries and clipping behavior should replace these standardized category coordinates.

The spline equations follow the rational-quadratic formulation in Durkan et al., *Neural Spline Flows*, NeurIPS 2019 (arXiv:1906.04032). The implementation is independent and includes inverse/Jacobian tests and exact-mass normalization tests.
