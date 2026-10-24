"""Exact finite checks for the written proof; not a proof-assistant certificate."""
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import permutations, product
from pathlib import Path
import json,sys

N=2**128; b=4096; t=64
D=(N-b)*(N-b-1)
C=F(t*(t+1)//2,D)
p=F(1,(N-1)*(N-2))
checks={}
def check(name,predicate):
    assert predicate, name
    checks[name]='pass'
check('classical_collision_lt_2^-244',C<F(1,2**244))
check('classical_query_coeff_lt_2^-249',F(t,D)<F(1,2**249))
check('any_preimage_query_coeff_lt_2^-248',F(t,D)+p<F(1,2**248))
check('statistics_lt_2^-99',F(t*b*(b-1),2*N)+C<F(1,2**99))
alpha=F(b*(b+3),N)
check('prediction_multiplicative_correction',alpha/(1-alpha)<F(1,2**100))
check('quantum_hybrid_coeff_squared',F(4*t,D)<F(1,2**246))
Q=2**100
check('quantum_anypreimage_at_2^100_lt_2^-22',C+F(Q+3,2**123)+(4*(Q+3)+1)**2*p<F(1,2**22))
Q=2**246
check('classical_anypreimage_at_2^246_below_half',C+(Q+1)*(F(t,D)+p)<F(1,2))
# Exhaustive toy virtual chain: N=4, one output block and three update blocks.
# The reduced key label comprises two 2-bit blocks (16 possible labels).
# The table at a key is a permutation of four points.
P=list(permutations(range(4)))
joint=defaultdict(Counter)
cases=0
for k0,p0,p1 in product(range(16),P,P):
    # V0=0 fixed. Its value does not affect the sampled-output law.
    r0,a0,b0,c0=[p0[(1+j)%4] for j in range(4)]
    k1=4*a0+b0
    r1,a1,b1,c1=[p1[(c0+1+j)%4] for j in range(4)]
    k2=4*a1+b1
    joint[(r0,r1,k2,c1)][(k0,k1)]+=1
    cases+=1
for (r0,r1,k2,v2), counts in joint.items():
    support=[(k,4*a+b_) for k in range(16) for a in range(4) for b_ in range(4) if a!=b_ and a!=r0 and b_!=r0]
    assert set(counts)==set(support)
    assert len(set(counts.values()))==1
check('toy_hidden_labels_product_cond_outputs_and_final_state',True)
marked=0
for perm in P:
    inv=[perm.index(y) for y in range(4)]
    marked+=int(inv[1]==(inv[0]+1)%4 and inv[2]==(inv[0]+2)%4)
check('toy_any_preimage_alignment_exact',F(marked,len(P))==F(1,(4-1)*(4-2)))
# Conditional ordered-triple distribution for the toy four-value sampling.
batch=Counter(tuple(perm[(j+1)%4] for j in range(4)) for perm in P)
check('toy_distinct_batch_sampling',len(batch)==24 and set(batch.values())=={1})
report={'python':sys.version,'profile':'P64 fixed length schedule','checks':checks,'toy_cases':cases,'collision_exact':str(C),'query_coefficient_exact':str(F(t,D)), 'any_inverse_coefficient_exact':str(F(t,D)+p),'scope':'Exact arithmetic and reduced finite consistency checks. General coupling, entropy and quantum proofs are written and manually reviewed, not formalized end to end.'}
(Path(__file__).parent/'verification_chain.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
