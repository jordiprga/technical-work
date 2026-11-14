"""Exact finite-state feedback analysis: iid phase, no classical noise, W=U=1.

Floating-point evaluations of analytic formulas; not interval-certified arithmetic.
No controller transcript is released to the adversary in the entropy-rate model.
"""
import csv
import json
import math
from pathlib import Path
import numpy as np
from qrng_sim import iid_phase_probability, binary_entropy


def analyze(gain=1., amplitude=1., max_length=256):
    if gain <= 0 or amplitude <= 0 or max_length < 1:
        raise ValueError('positive gain/amplitude/length required')
    delta=gain/2
    radius=math.ceil(amplitude/delta)
    if radius>10000:
        raise ValueError('gain too small for this explicit finite-state analysis')
    theta=delta*np.arange(-radius,radius+1,dtype=float)
    p=iid_phase_probability(theta,0.,amplitude)
    count=len(theta)
    # Birth-death stationary probabilities from detailed balance, in log space.
    logpi=np.zeros(count)
    for i in range(count-1):
        logpi[i+1]=logpi[i]+np.log(p[i])-np.log1p(-p[i+1])
    pi=np.exp(logpi-np.max(logpi)); pi/=pi.sum()
    stationary_residual=np.zeros(count)
    stationary_residual[1:] += pi[:-1]*p[:-1]
    stationary_residual[:-1] += pi[1:]*(1-p[1:])
    pair_products=p[:-1]*(1-p[1:])
    min_entropy_rate=-.5*math.log2(float(np.max(pair_products)))
    shannon_rate=float(np.sum(pi*binary_entropy(p)))
    # Max probability of a word of each length, starting at theta=0. Output
    # labels determine the state path; maxima, not probability sums, are used.
    dp=np.full(count,-np.inf); dp[radius]=0.
    lengths=[]
    for n in range(1,max_length+1):
        nxt=np.full(count,-np.inf)
        for i in range(count):
            if p[i]>0:
                nxt[i+1]=max(nxt[i+1],dp[i]+math.log2(float(p[i])))
            if p[i]<1:
                nxt[i-1]=max(nxt[i-1],dp[i]+math.log2(float(1-p[i])))
        dp=nxt
        h=-float(np.max(dp))
        lengths.append({'n':n,'joint_min_entropy':h,'per_bit':h/n})
    return {'gain':gain,'amplitude':amplitude,'states':count,
            'threshold_grid':theta.tolist(),'probability_one':p.tolist(),
            'stationary_distribution':pi.tolist(),
            'stationarity_residual_max':float(max(abs(stationary_residual-pi))),
            'chain_period':2,'asymptotic_min_entropy_rate':min_entropy_rate,
            'shannon_entropy_rate':shannon_rate,
            'largest_two_cycle_probability_product':float(max(pair_products)),
            'conditioning':'no classical noise; no release of controller transcript',
            'finite_lengths':lengths}


def main():
    root=Path(__file__).resolve().parent/'results'
    root.mkdir(exist_ok=True)
    all_results=[analyze(g) for g in [.1,.25,.5,1.,1.5,2.,3.]]
    (root/'finite_state_analysis.json').write_text(json.dumps(all_results,indent=2)+'\n')
    rows=[]
    for r in all_results:
        rows.append({k:v for k,v in r.items() if k in ['gain','states','asymptotic_min_entropy_rate',
                    'shannon_entropy_rate','chain_period','stationarity_residual_max']})
    with (root/'finite_state_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(rows,indent=2))

if __name__=='__main__':
    main()
