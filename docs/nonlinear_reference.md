# Exact references for the nonlinear experiment

The default source is

\[
X_t=2U_t+V_t,\qquad
V_t=\operatorname{mux}(U_{t-9},U_{t-13},U_{t-17})\oplus E_t,
\]

where \(U_t\overset{\mathrm{iid}}\sim\mathrm{Bernoulli}(1/2)\),
\(E_t\overset{\mathrm{iid}}\sim\mathrm{Bernoulli}(\varepsilon)\), the two
families are independent, and \(\operatorname{mux}(a,s,b)=a\) if \(s=1\)
and \(b\) otherwise. Symbols expose both bits: \(U_t=\lfloor X_t/2\rfloor\)
and \(V_t=X_t\bmod2\). The implementation initializes the first 17 symbols
independently and uniformly. The formulas below concern the stationary regime
of the explicit rule; they apply to the benchmark test segment, well after this
initialization.

The three distinct lagged driver bits are independent and fair. The clean
multiplexer output is fair, and adding independent Bernoulli noise preserves
fairness. Fresh \(U_t\) is independent of \(V_t\); therefore every symbol has
probability exactly \(1/4\), for every \(\varepsilon\). This is an exact
marginal probability law, not a constraint that balances finite sample counts.
Consequently the marginal min-entropy is exactly 2 bits per symbol.

## Full observed-history reference

Given the past observations, all three relevant driver bits are known. The
optimal probability of predicting the low bit is
\(\max\{\varepsilon,1-\varepsilon\}\), while the fresh high bit still has
success probability \(1/2\). Thus

\[
p_{\mathrm{guess},\infty}
=\tfrac12\max\{\varepsilon,1-\varepsilon\}.
\]

At \(\varepsilon=0.03\), the optimal symbol prediction success is 0.485.
The maximum conditional symbol mass is the same for every past context, so
worst-case conditional min-entropy and average conditional min-entropy both
are \(-\log_2(0.485)\approx1.04394\) bits here. The Shannon entropy rate is
instead \(1+h_2(0.03)\approx1.19439\) bits per symbol. These distinct
quantities must not be replaced by a trained model's held-out log-loss.

## Optimal prediction using only the last one to five symbols

The naive assertion that *all* short Markov models have chance success 0.25
would be incorrect. The chosen lags differ by four. Each low bit \(V_s\)
depends only on driver indices congruent to \(s-1\pmod4\). This separates
the driver families for the target and the immediately preceding three low
bits. The recent high bits are also independent of the older drivers used by
the target. Hence for context orders \(k=1,2,3\),

\[
p_{\mathrm{guess},k}=\tfrac14.
\]

At orders four and five, \(V_{t-4}\) is informative. All other observed bits
in these contexts are independent of the joint pair \((V_t,V_{t-4})\).
Write four independent fair bits as

\[
A=U_{t-9},\quad S=U_{t-13},\quad B=U_{t-17},\quad C=U_{t-21}.
\]

Before noise, the relevant pair is

\[
Y=\operatorname{mux}(A,S,B),\qquad
Z=\operatorname{mux}(S,B,C).
\]

Exhaustive enumeration of the 16 equally likely driver states gives, with
rows indexed by \(Y\) and columns by \(Z\),

\[
P_{Y,Z}=\begin{pmatrix}3/16&5/16\\5/16&3/16\end{pmatrix}.
\]

The clean low bits are anticorrelated: predicting \(Y=1-Z\) succeeds with
probability \(5/8\). Independent binary-symmetric noise on both observations
multiplies the centered correlation by \((1-2\varepsilon)^2\). With
\(r=(1-2\varepsilon)^2\), the noisy joint distribution is

\[
P_{V_t,V_{t-4}}
=\begin{pmatrix}1/4-r/16&1/4+r/16\\1/4+r/16&1/4-r/16\end{pmatrix}.
\]

The optimal low-bit success is \(1/2+r/8\). Multiplying by the independent
high-bit success \(1/2\),

\[
\boxed{p_{\mathrm{guess},4}=p_{\mathrm{guess},5}
=\tfrac14+\tfrac1{16}(1-2\varepsilon)^2.}
\]

At \(\varepsilon=0.03\), this equals **0.305225**, versus the full-history
reference **0.485**. These are optimal finite-context references, not promised
performances for estimated Markov tables. Finite training samples, smoothing,
and the 1,024 possible order-five four-symbol contexts can lower the measured
performance. A measured finite-sample accuracy can also exceed its expected
reference by sampling fluctuation.

The exact enumeration, including both independent noise bits with their
probability weights, is checked in `tests/test_nonlinear_reference.py`. The
closed forms here are specific to the default lag pattern; changing the lags
can change which short contexts carry information.
