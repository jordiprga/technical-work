"""Selected mechanical checks, not a proof of DRG.3 or AES security."""
from pathlib import Path
import sys
import json
from fractions import Fraction
from itertools import product

local_packages = Path(__file__).resolve().parents[1] / 'tools' / 'python_packages'
if local_packages.is_dir():
    sys.path.insert(0, str(local_packages))
import z3

results = []
def prove(name, formula):
    s = z3.Solver()
    s.add(z3.Not(formula))
    result = s.check()
    assert result == z3.unsat, (name, str(result))
    results.append(dict(id=name,kind='universal bit-vector identity',result=str(result)))

x,t = z3.BitVecs('x t',384)
prove('V02_XOR_inverse_384', ((x ^ t) ^ t) == x)
prove('V02_projection_256', z3.Extract(383,128,x ^ t) == (z3.Extract(383,128,x) ^ z3.Extract(383,128,t)))
w,j = z3.BitVecs('w j',128)
prove('V07_counter_inverse_128', (w + j) - j == w)
prove('V07_request_transition_inverse', (w + 1) - 1 == w)
# Counting steps use arbitrary precision integer arithmetic, not floats.
assert 2**384 // 2**128 == 2**256
assert 368-128 == 240 and 378-128 == 250
assert 122+128 == 250 and 256-128 == 128
for h in range(128,385):
    assert Fraction(2**(h-128),2**256) * 2**384 == 2**h
results.append(dict(id='V03_V04_V06',kind='exact integer exponent checks',result='pass'))
q=4096
delta=Fraction(q*(q-1),2**129)
assert delta < Fraction(1,2**105)
assert q == (2**19+127)//128
results.append(dict(id='V08',kind='exact rational arithmetic',q=q,bound=str(delta),result='pass'))
# Exhaustively verify largest-fibre sum bound for EVERY map 3bits -> 2bits.
# Here d=8, N=4, t=2: the largest two fibres contain at least four inputs.
count=0
for mapping in product(range(4), repeat=8):
    fibres=sorted([mapping.count(y) for y in range(4)],reverse=True)
    assert sum(fibres[:2]) >= 4
    count+=1
results.append(dict(id='V06_small_model',kind='exhaustive maps 8 -> 4',maps=count,result='pass',limit='Consistency example only; not a proof for AES domains'))
report=dict(checker='z3-solver',version=z3.get_version_string(),python=sys.version,checks=results,scope='No probability-library formalization, AES hardness proof, DRBG implementation validation or DRG.3 proof')
target=Path(__file__).parent/'verification_smt.json'
target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
