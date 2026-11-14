#!/usr/bin/env python3
"""Rational interval branch-and-bound for a fixed map and a binary Markov box.

Certificate covers a SYNTHETIC parameter box, not the adequacy of a physical model.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import heapq
import itertools
import json
import math
from pathlib import Path

from fixed_matrix_analysis import exact_output, transpose_mask

@dataclass(frozen=True)
class Interval:
    lo:F
    hi:F
    def __post_init__(self):
        if any(type(value) not in (int,F) for value in [self.lo,self.hi]):
            raise TypeError('exact Fraction or integer endpoints required; floats are rejected')
        object.__setattr__(self,'lo',F(self.lo));object.__setattr__(self,'hi',F(self.hi))
        if self.lo>self.hi:raise ValueError('reversed interval')
    def __add__(self,other):
        other=as_interval(other);return Interval(self.lo+other.lo,self.hi+other.hi)
    __radd__=__add__
    def __neg__(self):return Interval(-self.hi,-self.lo)
    def __sub__(self,other):return self+-as_interval(other)
    def __rsub__(self,other):return as_interval(other)+-self
    def __mul__(self,other):
        other=as_interval(other);corners=[x*y for x in [self.lo,self.hi] for y in [other.lo,other.hi]]
        return Interval(min(corners),max(corners))
    __rmul__=__mul__
    def midpoint(self):return (self.lo+self.hi)/2
    def width(self):return self.hi-self.lo


def as_interval(value):
    if isinstance(value,Interval):return value
    if type(value) not in (int,F):raise TypeError('exact Fraction or integer scalar required')
    return Interval(F(value),F(value))


def probability_enclosures(seed,n,m,box):
    a,b=box
    if min(a.lo,b.lo)<0 or max(a.hi,b.hi)>1:raise ValueError('transition probabilities outside [0,1]')
    transition=[[1-a,a],[b,1-b]]
    coeff=[]
    for v in range(1<<m):
        if v==0:
            coeff.append(as_interval(1))
            continue
        mask=transpose_mask(seed,v,n,m)
        x=as_interval(F(1,2));y=as_interval(F(-1 if mask&1 else 1,2))
        for j in range(1,n):
            x,y=x*transition[0][0]+y*transition[1][0],x*transition[0][1]+y*transition[1][1]
            if mask>>j&1:y=-y
        coeff.append(x+y)
    result=[]
    for out in range(1<<m):
        bound=sum((co*(-1 if (v&out).bit_count()%2 else 1) for v,co in enumerate(coeff)),as_interval(0))*F(1,1<<m)
        result.append(Interval(max(F(0),bound.lo),min(F(1),bound.hi)))
    return result


def split(box):
    dim=0 if box[0].width()>=box[1].width() else 1
    mid=box[dim].midpoint();children=[]
    for interval in [Interval(box[dim].lo,mid),Interval(mid,box[dim].hi)]:
        child=list(box);child[dim]=interval;children.append(tuple(child))
    return children


def box_at(root,path):
    box=root
    for digit in path:
        if digit not in '01':raise ValueError('invalid path')
        box=split(box)[int(digit)]
    return box


def node(seed,n,m,box,path):
    upper=max(p.hi for p in probability_enclosures(seed,n,m,box))
    a,b=[x.midpoint() for x in box]
    probs=exact_output(seed,n,m,[F(1,2)]*2,[[1-a,a],[b,1-b]])
    lower=max(probs.values())
    return {'path':path,'upper':upper,'witness_lower':lower,'witness_parameters':[a,b]}


def solve(seed=133,n=8,m=2,max_leaves=256,tolerance=F(1,1000)):
    root=(Interval(F(1,10),F(3,20)),Interval(F(1,5),F(1,4)))
    counter=itertools.count();first=node(seed,n,m,root,'');lower=first['witness_lower'];best=first
    heap=[(-first['upper'],next(counter),first)]
    while len(heap)<max_leaves and -heap[0][0]-lower>tolerance:
        _,_,old=heapq.heappop(heap)
        for suffix,box in zip('01',split(box_at(root,old['path']))):
            new=node(seed,n,m,box,old['path']+suffix)
            if new['witness_lower']>lower:lower=new['witness_lower'];best=new
            heapq.heappush(heap,(-new['upper'],next(counter),new))
    leaves=[entry[2] for entry in heap]
    # Retain the best witness even when its parent cell was subdivided.
    upper=max(x['upper'] for x in leaves)
    return {'schema':1,'seed':seed,'n':n,'m':m,'initial':['1/2','1/2'],
            'a_interval':['1/10','3/20'],'b_interval':['1/5','1/4'],
            'lower':str(lower),'upper':str(upper),'gap':str(upper-lower),
            'best_witness_parameters':[str(v) for v in best['witness_parameters']],
            'min_entropy_lower_bits_approx':-math.log2(float(upper)),
            'min_entropy_upper_bits_approx':-math.log2(float(lower)),
            'leaves':[{k:([str(z) for z in v] if isinstance(v,list) else str(v) if isinstance(v,F) else v) for k,v in leaf.items()} for leaf in sorted(leaves,key=lambda x:x['path'])],
            'meaning':'lower <= sup_(a,b in box) max_y P(Y=y) <= upper; rational bounds exact, displayed logarithms approximate'}


def verify(certificate):
    c=certificate
    if type(c.get('schema')) is not int or c['schema']!=1:raise ValueError('unsupported certificate schema')
    root=tuple(Interval(F(lo),F(hi)) for lo,hi in [c['a_interval'],c['b_interval']])
    if c['initial']!=['1/2','1/2']:raise ValueError('unsupported initial distribution')
    paths=[x['path'] for x in c['leaves']]
    if len(set(paths))!=len(paths) or not paths:raise ValueError('empty/duplicate leaves')
    paths.sort()
    if any(b.startswith(a) for a,b in zip(paths,paths[1:])):raise ValueError('overlapping prefix leaves')
    if sum((F(1,2**len(path)) for path in paths),F())!=1:raise ValueError('partition does not cover root')
    checked=[]
    for saved in c['leaves']:
        actual=node(c['seed'],c['n'],c['m'],box_at(root,saved['path']),saved['path'])
        if F(saved['upper'])!=actual['upper'] or F(saved['witness_lower'])!=actual['witness_lower']:
            raise ValueError('bound does not replay')
        if [F(v) for v in saved['witness_parameters']]!=actual['witness_parameters']:
            raise ValueError('witness does not replay')
        checked.append(actual)
    a,b=map(F,c['best_witness_parameters'])
    if not (root[0].lo<=a<=root[0].hi and root[1].lo<=b<=root[1].hi):raise ValueError('best witness outside parameter box')
    lower=max(exact_output(c['seed'],c['n'],c['m'],[F(1,2)]*2,[[1-a,a],[b,1-b]]).values())
    upper=max(x['upper'] for x in checked)
    if (F(c['lower']),F(c['upper']),F(c['gap']))!=(lower,upper,upper-lower):raise ValueError('aggregate mismatch')
    entropy_lower=-math.log2(float(upper));entropy_upper=-math.log2(float(lower))
    for name,expected in [('min_entropy_lower_bits_approx',entropy_lower),('min_entropy_upper_bits_approx',entropy_upper)]:
        value=c.get(name)
        if type(value) not in (int,float) or not math.isfinite(value) or not math.isclose(value,expected,rel_tol=0,abs_tol=1e-12):
            raise ValueError('approximate display entropy does not match rational bounds')
    return {'verified':True,'leaves':len(paths),'gap_decimal':float(upper-lower),
            'min_entropy_lower_bits_approx':entropy_lower,'min_entropy_upper_bits_approx':entropy_upper,
            'meaning_field_is_informational':True}

if __name__=='__main__':
    result=solve();verification=verify(result)
    out=Path(__file__).resolve().parent/'results/interval_markov_certificate.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**verification,'output':str(out),'min_entropy_lower_bits_approx':result['min_entropy_lower_bits_approx'],'min_entropy_upper_bits_approx':result['min_entropy_upper_bits_approx']}))
