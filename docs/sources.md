# Synthetic source definitions and references

All randomness uses a local `numpy.random.Generator` with an explicit seed. Bin edges depend on supplied distribution parameters, never sample extrema or test data. Exact uniformity describes the marginal law; finite samples are not artificially balanced.

| Name | Definition / default | Reference |
|---|---|---|
| `bernoulli` | IID Bernoulli(.7) | Exact success max(p,1-p), IID |
| `markov` | Stationary binary chain p01=p10=.05 | Exact conditional transition probabilities and stationary success |
| `higher_order` | X[t]=X[t-5] XOR (X[t-1] AND X[t-2]) XOR noise(.03) | Exact conditional law; uniform initial 5-bit state is invariant under a bijective shift map |
| `periodic` | X[t]=X[t-32] XOR noise(.05) | Seasonal dependence: independent Markov chains across 32 phases; exact success .95 after initialization |
| `hmm` | Symmetric hidden chain stay=.97; observation flips=.1 | Exact forward filtering from observed samples only |
| `ar1` | Z[t]=.95 Z[t-1]+N(0,.3²), 8 fixed bins | Exact Gaussian marginal; NO observed-history oracle; quadrature of privileged continuous-state success is separately labeled |
| `arcsine` | cos(Uniform[0,π])+N(0,.15²), 8 fixed bins | Numerical IID bin masses by integrating Gaussian CDF over angle, checked at two quadrature orders; approximate oracle labeled explicitly |
| `drift` | Independent Bernoulli(.5+.4 sin(2πt/4000)) | Exact time-indexed conditional probabilities; nonstationary, known clock oracle |
| `long_range` | X[t]=X[t-16] XOR noise(.03) | Uniform marginal, exact success .97; 16 interleaved Markov chains |
| `nonlinear` | X[t]=2U[t]+V[t], V[t]=U[t-9] if U[t-13]=1 else U[t-17], then flip(.03) | U are iid fair bits. Exact 4-symbol uniform marginal, exact success .485 after initialization |

For the nonlinear source the initial 17 symbols are iid uniform and observed. Subsequent driver bits U[t] remain iid fair. Three distinct lagged fair drivers imply a fair multiplexer output; the current fresh driver is independent of this output, so P(X[t]=x)=1/4 for every x. The oracle probabilities are `(1-pV)/2,pV/2,(1-pV)/2,pV/2`. Its optimal success is `(1-noise)/2` for noise≤1/2: one fresh bit per sample is intrinsically unpredictable. The finite initialized process is labeled nonstationary even though every one-dimensional marginal is uniform. Once the initial prefix has passed, it is a finite-memory function of iid drivers and noise. Markov contexts of order ≤5 do not include the required driver indices; incidental correlations through past response lanes may nevertheless exist, so their actual accuracy must be measured rather than asserted to equal chance.

For the AR(1) source, supplying Z[t-1] instead of only its quantized history provides strictly more information. Therefore its quadrature-derived success is only a privileged reference upper bound on achievable observed-history success, subject to numerical integration error. It is not inserted into `oracle_probs` and cannot be silently compared as an attainable predictor. Eight fixed bins include both infinite tails; no samples are clipped away.

The drift oracle knows the public deterministic sample clock and source parameters, while the generic predictors receive only windows. This advantage is explicit. Prediction performance under drift does not imply a stationary entropy rate or justify IID binomial confidence intervals.

## Exact rates for the controlled dependence examples

Write h₂(p)=−p log₂p−(1−p)log₂(1−p) and r=max(p,1−p).

For a binary lag-L copy source with iid fair initial state and flip probability p, a length-n path (n≥L) has maximum probability 2^(−L)r^(n−L). Hence its **block min-entropy rate** is −log₂r; its **Shannon entropy rate** is h₂(p); and its **marginal min-entropy** is 1 bit. Its one-step average conditional min-entropy after initialization also equals −log₂r because every history has the same maximum conditional probability. This coincidence follows from the source structure and must not be generalized to arbitrary dependent processes.

For the four-symbol noisy multiplexer with initialized length L=max(lags), maximum path probability is 4^(−L)(r/2)^(n−L). Consequently its block min-entropy rate is 1−log₂r and its Shannon entropy rate is 1+h₂(p), while its marginal min-entropy is 2 bits. The one-step maximum conditional probability is r/2. With p=.03, success is .485 and average conditional min-entropy is −log₂(.485)≈1.04394 bits; the fresh driver contributes one intrinsically unpredictable bit per symbol.

These rates describe the specified synthetic laws. A learned predictor's empirical log-loss or transformed observed success is not a certified estimate of these true rates.
