#!/usr/bin/env python3
"""Laboratorio sintético Toeplitz. Exact finite probabilities; no entropy certification."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path
import random


def toeplitz_hash(seed: int, x: int, n: int, m: int) -> int:
    """GF(2), bits LSB first. T[i,j] = seed[i-j+n-1]."""
    if n < 1 or m < 1 or not 0 <= seed < 1 << (n+m-1) or not 0 <= x < 1 << n:
        raise ValueError('invalid dimensions, seed, or input')
    return sum((sum(((seed >> (i-j+n-1)) & 1) * ((x >> j) & 1)
                    for j in range(n)) % 2) << i for i in range(m))


def rank_gf2(rows: list[int]) -> int:
    pivots: dict[int, int] = {}
    for row in rows:
        while row:
            bit = row.bit_length()-1
            if bit in pivots:
                row ^= pivots[bit]
            else:
                pivots[bit] = row
                break
    return len(pivots)


def toeplitz_rank(seed: int, n: int, m: int) -> int:
    rows = [sum(((seed >> (i-j+n-1)) & 1) << j for j in range(n)) for i in range(m)]
    return rank_gf2(rows)


def output_distribution(seed: int, probs: dict[int, Fraction], n: int, m: int) -> dict[int, Fraction]:
    result = defaultdict(Fraction)
    for x, px in probs.items():
        result[toeplitz_hash(seed, x, n, m)] += px
    return dict(result)


def tv_uniform(probs: dict[int, Fraction], alphabet_size: int) -> Fraction:
    if sum(probs.values()) != 1 or any(p < 0 for p in probs.values()):
        raise ValueError('probabilities must be nonnegative and sum to 1')
    if any(not 0 <= x < alphabet_size for x in probs):
        raise ValueError('outside alphabet')
    u = Fraction(1, alphabet_size)
    return sum((abs(probs.get(x, Fraction())-u) for x in range(alphabet_size)), Fraction())/2


def bernoulli_distribution(n: int, p: Fraction) -> dict[int, Fraction]:
    if not 0 <= p <= 1:
        raise ValueError('p out of range')
    return {x: p**x.bit_count()*(1-p)**(n-x.bit_count()) for x in range(1 << n)}


def min_entropy(probs: dict[int, Fraction]) -> float:
    return -math.log2(float(max(probs.values())))


def universal_check(n: int, m: int) -> dict:
    counts = [sum(toeplitz_hash(s, d, n, m) == 0 for s in range(1 << (n+m-1)))
              for d in range(1, 1 << n)]
    expected = 1 << (n-1)
    return {'n': n, 'm': m, 'differences_checked': len(counts),
            'seeds_checked_per_difference': 1 << (n+m-1),
            'expected_collision_count': expected, 'min_count': min(counts),
            'max_count': max(counts), 'all_exact': all(c == expected for c in counts)}


def exact_reuse(n: int = 6, m: int = 2) -> dict:
    """Uniform independent blocks versus a repeated block and seed-adaptive kernels."""
    total = 1 << (n+m-1)
    ranks = Counter(toeplitz_rank(s, n, m) for s in range(total))
    single = sum((Fraction(c, total)*(1-Fraction(2**r, 2**m)) for r,c in ranks.items()), Fraction())
    independent = sum((Fraction(c,total)*(1-Fraction(2**(2*r),2**(2*m))) for r,c in ranks.items()), Fraction())
    repeated = sum((Fraction(c,total)*(1-Fraction(2**r,2**(2*m))) for r,c in ranks.items()), Fraction())
    adaptive_pguess = sum((Fraction(c,total)*Fraction(1,2**(n-r)) for r,c in ranks.items()), Fraction())
    return {'n':n, 'm':m, 'seed_bits':n+m-1, 'rank_histogram':dict(sorted(ranks.items())),
            'tv_seed_and_single':single, 'tv_seed_and_two_independent_blocks':independent,
            'tv_seed_and_two_repeated_blocks':repeated,
            'repeated_full_rank_seed_tv':1-Fraction(1,2**m),
            'adaptive_kernel_tv':1-Fraction(1,2**m),
            'adaptive_kernel_conditional_min_entropy_bits':-math.log2(float(adaptive_pguess)),
            'adaptive_kernel_worst_seed_min_entropy_bits':n-min(n,m),
            'single_lhl_bound':.5*math.sqrt(2**(m-n)),
            'two_block_composition_bound':math.sqrt(2**(m-n)),
            'interpretation':'Exact enumeration/rank formulas; not inference about a physical source.'}


def biased_source(n: int = 6, m: int = 2, p: Fraction = Fraction(3,4)) -> dict:
    probs = bernoulli_distribution(n,p)
    distances = [tv_uniform(output_distribution(s,probs,n,m),1 << m) for s in range(1 << (n+m-1))]
    avg = sum(distances,Fraction())/len(distances)
    second = sum((d*d for d in distances),Fraction())/len(distances)
    k = min_entropy(probs)
    collision = sum((px*px for px in probs.values()),Fraction())
    second_bound = Fraction((1 << m)-1,4)*collision
    return {'n':n,'m':m,'bernoulli_p':p,'input_min_entropy':k,'average_tv':avg,
            'average_squared_tv':second,'second_moment_collision_bound':second_bound,
            'lhl_min_entropy_bound':.5*2**((m-k)/2),'worst_seed_tv':max(distances),
            'number_of_seeds':len(distances),'bad_seed_fraction_tv_gt_one_quarter':Fraction(sum(d>Fraction(1,4) for d in distances),len(distances))}


def correlated_blocks(n: int=6,m: int=2,rho: Fraction=Fraction(3,4)) -> dict:
    """X1 uniform; X2=X1 with probability rho, otherwise fresh uniform."""
    total_seeds = 1 << (n+m-1)
    all_tv = Fraction()
    all_single = Fraction()
    for seed in range(total_seeds):
        out = output_distribution(seed, {x:Fraction(1,1<<n) for x in range(1<<n)}, n,m)
        pair = {}
        for a in range(1 << m):
            for b in range(1 << m):
                pa,pb = out.get(a,Fraction()),out.get(b,Fraction())
                pair[(a << m)|b] = (1-rho)*pa*pb + (rho*pa if a == b else 0)
        all_tv += tv_uniform(pair,1 << (2*m))/total_seeds
        all_single += tv_uniform(out,1 << m)/total_seeds
    pguess = rho+(1-rho)/2**n
    return {'n':n,'m':m,'repeat_probability':rho,'marginal_min_entropy':n,
            'conditional_min_entropy_X2_given_X1':-math.log2(float(pguess)),
            'tv_seed_and_each_marginal':all_single,'tv_seed_and_pair':all_tv,
            'full_rank_seed_joint_tv':rho*(1-Fraction(1,2**m))}


def parity_dependency(m: int=4) -> dict:
    """A,B uniform independent, C=A xor B. All pairs independent; triple not."""
    q = 1 << m
    return {'m':m,'each_output_entropy_bits':m,'each_pair_joint_entropy_bits':2*m,
            'triple_joint_entropy_bits':2*m,'triple_conditional_last_entropy_bits':0,
            'triple_tv_from_uniform':1-Fraction(1,q),
            'probability_xor_zero_actual':1,'probability_xor_zero_ideal':Fraction(1,q)}


def monte_carlo(n: int=24,m: int=8,samples: int=20000,random_seed: int=20261114) -> dict:
    """Synthetic reproducible experiment, not security randomness generation."""
    rng=random.Random(random_seed)
    seed=rng.randrange(1 << (n+m-1))
    while toeplitz_rank(seed,n,m) != m:
        seed=rng.randrange(1 << (n+m-1))
    singles=Counter(); eq_independent=0; eq_repeated=0; eq_correlated=0
    rho=.8
    for _ in range(samples):
        x=rng.getrandbits(n); x2=rng.getrandbits(n)
        a=toeplitz_hash(seed,x,n,m); b=toeplitz_hash(seed,x2,n,m)
        singles[a]+=1
        eq_independent += a == b
        eq_repeated += a == toeplitz_hash(seed,x,n,m)
        xc=x if rng.random()<rho else x2
        eq_correlated += a == toeplitz_hash(seed,xc,n,m)
    return {'n':n,'m':m,'samples':samples,'simulation_random_seed':random_seed,
            'toeplitz_seed_hex':hex(seed),'rank':m,
            'marginal_plugin_tv':sum(abs(c/samples-1/(1<<m)) for c in [singles[y] for y in range(1<<m)])/2,
            'equal_output_independent_fraction':eq_independent/samples,
            'equal_output_independent_expectation':1/(1<<m),
            'equal_output_repeated_fraction':eq_repeated/samples,
            'equal_output_correlated_fraction':eq_correlated/samples,
            'equal_output_correlated_expectation':rho+(1-rho)/(1<<m),
            'warning':'Plugin TV has sampling bias; equality distinguisher is the meaningful comparison.'}


def lifetime_budget(k: float,m: int,blocks: int,seed_tv: float=0,model_failure: float=0) -> dict:
    if k < 0 or m < 1 or blocks < 1 or not 0 <= seed_tv <= 1 or not 0 <= model_failure <= 1:
        raise ValueError('invalid budget')
    eps=.5*2**((m-k)/2)
    return {'conditional_entropy_bits_per_block':k,'output_bits_per_block':m,'blocks':blocks,
            'per_block_lhl_error':eps,'sum_hash_error':blocks*eps,
            'seed_tv_once':seed_tv,'model_failure_once':model_failure,
            'total_tv_bound_capped':min(1.,blocks*eps+seed_tv+model_failure),
            'assumptions':'S independent of whole raw process and side information; block conditional min-entropy bounds; fixed horizon; seed/model costs justified separately.'}


def encode(value):
    if isinstance(value,Fraction):
        return {'exact':str(value),'decimal':float(value)}
    raise TypeError(type(value).__name__)


def run_all() -> dict:
    return {'schema_version':'1.0','status':'synthetic research, not certification',
            'universal_checks':[universal_check(n,m) for n,m in [(1,1),(3,2),(6,3)]],
            'reuse':exact_reuse(),'biased':biased_source(),
            'correlation_sweep':[correlated_blocks(rho=r) for r in [Fraction(0),Fraction(1,4),Fraction(1,2),Fraction(3,4),Fraction(1)]],
            'pairwise_independence_failure':parity_dependency(),
            'monte_carlo':monte_carlo(),
            'lifetime_examples':[lifetime_budget(1024,m,10**12) for m in [768,784,896]]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('results/results.json'))
    args=parser.parse_args()
    result=run_all(); args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,default=encode)+'\n',encoding='utf8')
    print(json.dumps({'output':str(args.output),'universal_checks_pass':all(x['all_exact'] for x in result['universal_checks']),
                      'repeated_pair_tv':result['reuse']['tv_seed_and_two_repeated_blocks'],
                      'independent_pair_tv':result['reuse']['tv_seed_and_two_independent_blocks']},default=encode))

if __name__=='__main__':
    main()
