"""Exact small-space checks of the local counts added to the exposition.

These verify combinatorial identities in reduced domains; written arguments
establish their generality. No external libraries or network are required.
"""
from collections import Counter
from fractions import Fraction as F
from itertools import combinations, permutations, product
from pathlib import Path
import json


def falling(n, u):
    out=1
    for j in range(u):
        out*=n-j
    return out


def projection(value, positions):
    return tuple((value >> bit) & 1 for bit in positions)


def main():
    width,n=3,8
    projection_cases=0
    for size in range(n):
        for excluded in combinations(range(n),size):
            remaining=[x for x in range(n) if x not in excluded]
            for count in range(1,width+1):
                for positions in combinations(range(width),count):
                    for guess in product((0,1),repeat=count):
                        observed=sum(projection(x,positions)==guess for x in remaining)
                        forbidden=sum(projection(c,positions)==guess for c in excluded)
                        expected=F(2**(width-count)-forbidden,n-size)
                        assert F(observed,len(remaining))==expected
                        assert expected <= F(1,2**count)*F(n,n-size)
                        projection_cases+=1

    masked_key_cases=0
    for q in (0,2):
        public=tuple(range(q))
        triples=list(permutations([x for x in range(n) if x not in public],3))
        assert len(triples)==falling(n-q,3)
        for mask in product(range(n),repeat=3):
            states=Counter((u[0]^mask[0],u[1]^mask[1],u[2]^mask[2]) for u in triples)
            assert set(states.values())=={1}
            keys=Counter((state[0],state[1]) for state in states)
            assert set(keys.values())=={n-q-2}
            for key,count in keys.items():
                assert F(count,len(triples))==F(1,falling(n-q,2))
                unmasked=(key[0]^mask[0],key[1]^mask[1])
                assert unmasked[0]!=unmasked[1] and not set(unmasked)&set(public)
                masked_key_cases+=1

    interval_cases=0
    for l1,l2 in product(range(1,4),repeat=2):
        assert l1+l2-1<n
        offsets={z%n for z in range(1-l2,l1)}
        assert len(offsets)==l1+l2-1
        for v1,v2 in product(range(n),repeat=2):
            first={(v1+j)%n for j in range(1,l1+1)}
            second={(v2+j)%n for j in range(1,l2+1)}
            assert bool(first&second)==((v2-v1)%n in offsets)
            interval_cases+=1

    inverse_cases=0
    for table in permutations(range(n)):
        inverse=[table.index(x) for x in range(n)]
        for w in range(n):
            current=table[w]
            assert table[(inverse[current]+1)%n]==table[(w+1)%n]
            assert table[(inverse[current]-1)%n]==table[(w-1)%n]
            # First final-Update input follows the last output input by one.
            first_update=table[(w+1)%n]
            assert table[(inverse[first_update]-1)%n]==current
            inverse_cases+=1

    report={'status':'all exact reduced-domain assertions passed',
            'scope':'local projection counts, masked key marginals, interval equivalence and counter identities; not a formal proof of the full generator',
            'counts':{'fixed_projection_cases':projection_cases,'masked_key_cases':masked_key_cases,
                      'interval_equivalences':interval_cases,'inverse_counter_cases':inverse_cases}}
    Path(__file__).with_name('verification-local.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
