# Notation used in the manuscript

| Symbol | Meaning |
|---|---|
| K,V,c | Persistent key,128-bit counter and public reseed counter. |
| a,p | Actual public additional input and requested bit length. |
| pad | Zero-padding to384 bits. |
| g(a) | Processed input provided to Update; the only notation used for it. |
| f(a,K,V) | Working key/counter pair after the optional pre-update. |
| barred K,V | Components of f(a,K,V), not another processing function. |
| phiA,phiB,phi | Pre-update, output advancement/final Update and their full composition. |
| Z_(y,j),Y_y | Internal block and returned/truncated output of request y. |
| y(i) | Request containing auxiliary group i; input is always a_y(i), without a second mask function. |
| sigma_i | Cryptographic pair before auxiliary group i. |
| Pi_i | Private permutation used only for the auxiliary probability calculation. |
| R_i,U_i | Public output list and three Update values of group i. |
| N,b,L |2^128, maximum4096 output blocks and maximum4099 evaluations per group. |
| r,t,Q | Number of output requests, auxiliary groups and external primitive computations. |
| epsilon_(t,r)(Q) | Single composition-error bound; no second epsilon alias. |

The temporary notation d(a)=g(a) has been removed. The formal argument of Update is x; instantiated Generate processing always uses g(a). Padding and auxiliary permutations have distinct names.
