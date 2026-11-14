#!/usr/bin/env python3
"""Exact distribution of a fixed Toeplitz map for a *specified* binary Markov model.

Uses Walsh transforms and 2x2 transfer matrices. No IID inference; the model is input.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path
import random

from extractor_lab import toeplitz_hash, toeplitz_rank, tv_uniform, encode


def transpose_mask(seed: int, v: int, n: int, m: int) -> int:
    return sum((sum(((v >> i)&1)*((seed >> (i-j+n-1))&1) for i in range(m))%2)<<j for j in range(n))


def validate_model(initial, transitions):
    if len(initial)!=2 or len(transitions)!=2 or any(len(row)!=2 for row in transitions):
        raise ValueError('binary initial distribution and 2x2 transition matrix required')
    for row in [initial,*transitions]:
        if sum(row)!=1 or min(row)<0:
            raise ValueError('nonnegative normalized probabilities required')


def markov_walsh(mask: int,n: int,initial: list[Fraction],transitions: list[list[Fraction]]) -> Fraction:
    """E[(-1)**dot(mask,X)] for a precisely specified Markov distribution."""
    validate_model(initial,transitions)
    if n<1 or not 0<=mask<1<<n: raise ValueError('invalid dimension or mask')
    a,b=initial[0],initial[1]*(-1 if mask&1 else 1)
    for j in range(1,n):
        a,b=a*transitions[0][0]+b*transitions[1][0],a*transitions[0][1]+b*transitions[1][1]
        if (mask>>j)&1: b=-b
    return a+b


def fwht(values):
    values=list(values); stride=1
    if not values or len(values)&(len(values)-1): raise ValueError('length must be a power of two')
    while stride<len(values):
        for start in range(0,len(values),2*stride):
            for j in range(start,start+stride):
                a,b=values[j],values[j+stride]
                values[j],values[j+stride]=a+b,a-b
        stride*=2
    return values


def exact_output(seed,n,m,initial,transitions):
    if toeplitz_rank(seed,n,m)>m: raise AssertionError('impossible rank')
    coefficients=[markov_walsh(transpose_mask(seed,v,n,m),n,initial,transitions) for v in range(1<<m)]
    probabilities=[p/(1<<m) for p in fwht(coefficients)]
    if min(probabilities)<0 or sum(probabilities)!=1:
        raise ArithmeticError('invalid Fourier reconstruction')
    return dict(enumerate(probabilities))


def maximum_path_probability(n,initial,transitions):
    validate_model(initial,transitions)
    if n<1: raise ValueError('positive length required')
    best=list(initial)
    for _ in range(1,n):
        best=[max(best[a]*transitions[a][b] for a in [0,1]) for b in [0,1]]
    return max(best)


def enumerate_output(seed,n,m,initial,transitions):
    out={y:Fraction() for y in range(1<<m)}
    for bits in product([0,1],repeat=n):
        probability=initial[bits[0]]
        for a,b in zip(bits,bits[1:]): probability*=transitions[a][b]
        x=sum(b<<j for j,b in enumerate(bits))
        out[toeplitz_hash(seed,x,n,m)]+=probability
    return out


def independent_bias_bounds(seed,n,m,bias_bounds):
    """Sound deterministic-map bounds for conditionally independent bits.

    Each bias bound is |1-2*p_j|, not |p_j-1/2|. Does not verify independence.
    """
    if len(bias_bounds)!=n or any(not 0<=b<=1 for b in bias_bounds):
        raise ValueError('one absolute expectation bound in [0,1] per input bit required')
    l1=Fraction(); l2=Fraction()
    for v in range(1,1<<m):
        mask=transpose_mask(seed,v,n,m)
        bound=Fraction(1)
        for j in range(n):
            if (mask>>j)&1: bound*=bias_bounds[j]
        l1+=bound; l2+=bound*bound
    return {'maximum_probability_upper_bound':min(Fraction(1),(1+l1)/(1<<m)),
            'tv_squared_upper_bound':min(Fraction(1),l2/4)}


def run():
    n,m=32,8; rng=random.Random(20261114); seed=rng.getrandbits(n+m-1)
    while toeplitz_rank(seed,n,m)!=m: seed=rng.getrandbits(n+m-1)
    models=[('IID p=0.6',[Fraction(2,5),Fraction(3,5)],[[Fraction(2,5),Fraction(3,5)]]*2),
            ('Markov symmetric stay=0.8',[Fraction(1,2)]*2,[[Fraction(4,5),Fraction(1,5)],[Fraction(1,5),Fraction(4,5)]]),
            ('Markov symmetric stay=0.95',[Fraction(1,2)]*2,[[Fraction(19,20),Fraction(1,20)],[Fraction(1,20),Fraction(19,20)]]),
            ('IID p=0.5',[Fraction(1,2)]*2,[[Fraction(1,2)]*2]*2)]
    rows=[]
    for name,initial,transition in models:
        dist=exact_output(seed,n,m,initial,transition)
        initial_k=-math.log2(float(maximum_path_probability(n,initial,transition)))
        worst_pguess=max(maximum_path_probability(n,transition[previous],transition) for previous in [0,1])
        rows.append({'model':name,'initial':initial,'transition':transition,
                     'input_block_min_entropy':initial_k,
                     'input_worst_previous_bit_conditional_min_entropy':-math.log2(float(worst_pguess)),
                     'output_min_entropy':-math.log2(float(max(dist.values()))),
                     'output_tv':tv_uniform(dist,1<<m),
                     'output_max_probability':max(dist.values()),
                     'hypothetical_uniform_seed_lhl_bound':min(1.,.5*2**((m-initial_k)/2))})
    spectrum=Counter(transpose_mask(seed,v,n,m).bit_count() for v in range(1,1<<m))
    beta=Fraction(1,5)
    max_probability_bound=(1+sum((count*beta**weight for weight,count in spectrum.items()),Fraction()))/(1<<m)
    tv_squared_bound=sum((count*beta**(2*weight) for weight,count in spectrum.items()),Fraction())/4
    return {'claim':'exact only within the specified classical Markov model; fixed seed, no universal guarantee',
            'nonzero_rowspace_weight_enumerator':dict(sorted(spectrum.items())),
            'independent_bit_class_abs_bias_max':beta,
            'class_output_max_probability_bound':max_probability_bound,
            'class_output_min_entropy_lower_bound':-math.log2(float(max_probability_bound)),
            'class_output_tv_upper_bound':math.sqrt(float(tv_squared_bound)),
            'n':n,'m':m,'fixed_seed_hex':hex(seed),'rank':m,'rows':rows,
            'caution':'The LHL column is a comparison for a uniformly selected seed, NOT a bound for this fixed seed.'}

if __name__=='__main__':
    result=run(); out=Path(__file__).resolve().parent/'results/fixed_matrix.json'
    out.write_text(json.dumps(result,indent=2,default=encode)+'\n')
    print(json.dumps({'output':str(out),'rows':[{k:r[k] for k in ['model','input_block_min_entropy','output_min_entropy','output_tv']} for r in result['rows']]},default=encode))
