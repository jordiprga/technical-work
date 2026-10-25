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

    # Representation identity only: a restricted-width counter is tested
    # against the same width on both sides. This does not extend the
    # permutation-security proof to restricted counter widths.
    tuple_cases=0
    def inc(value, ell):
        lowmask=(1<<ell)-1
        return (value & ~lowmask) | ((value+1)&lowmask)
    def cipher(key, value):
        # A deterministic family of permutations on the four-element space.
        return (((1+2*(key//4))*value)+(key%4))%4
    def update(mask, key, value, ell):
        values=[]
        for _ in range(3):
            value=inc(value,ell)
            values.append(cipher(key,value))
        encoded=((values[0]<<4)|(values[1]<<2)|values[2])^mask
        return encoded>>2,encoded&3
    for ell,key,value,c,mask,p in product((1,2),range(16),range(4),
                                         (1,2),(None,*range(64)),range(1,9)):
        if mask is None:
            workkey,workvalue=key,value
            data=0
        else:
            workkey,workvalue=update(mask,key,value,ell)
            data=mask
        q=(p+1)//2
        # Reference: BSI Sreq retains RC; phi_req increments before output.
        full=(workkey,inc(workvalue,ell),c)
        reduced=full[:2]
        refbits=[]
        gotbits=[]
        endvalue=workvalue
        for j in range(q):
            ref=cipher(full[0],full[1])
            got=cipher(*reduced)
            refbits.extend(((ref>>1)&1,ref&1))
            gotbits.extend(((got>>1)&1,got&1))
            full=(full[0],inc(full[1],ell),full[2])
            reduced=(reduced[0],inc(reduced[1],ell))
            assert full[:2]==reduced and full[2]==c
            endvalue=inc(endvalue,ell)
        assert refbits[:p]==gotbits[:p]
        reference_next=(*update(data,workkey,endvalue,ell),c+1)
        # Direct description: Generate increments q times, then Update.
        direct_v=workvalue
        direct_bits=[]
        for _ in range(q):
            direct_v=inc(direct_v,ell)
            block=cipher(workkey,direct_v)
            direct_bits.extend(((block>>1)&1,block&1))
        direct_next=(*update(data,workkey,direct_v,ell),min(c+1,3))
        assert reference_next==direct_next
        assert direct_bits[:p]==refbits[:p]
        tuple_cases+=1
    assert inc(1,1)==0 and inc(1,2)==2  # Width change is substantive.

    report={'status':'all exact reduced-domain assertions passed',
            'scope':'local probability identities and same-parameter tuple/Generate correspondence; not a formal proof of the full generator',
            'counts':{'fixed_projection_cases':projection_cases,'masked_key_cases':masked_key_cases,
                      'interval_equivalences':interval_cases,'inverse_counter_cases':inverse_cases,
                      'tuple_projection_and_generate_cases':tuple_cases}}
    Path(__file__).with_name('verification-local.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
