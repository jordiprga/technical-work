#!/usr/bin/env python3
"""Export generated symbols for independent inspection or an external estimator."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from entropy_oracle.sources import make_source,SOURCE_NAMES
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',choices=SOURCE_NAMES,default='nonlinear')
p.add_argument('--n',type=int,default=1000000)
p.add_argument('--seed',type=int,default=11)
p.add_argument('--params',default='{}')
p.add_argument('--out',default='source.bin')
a=p.parse_args();d=make_source(a.source,n=a.n,seed=a.seed,**json.loads(a.params))
if d.alphabet_size>256: raise ValueError('Raw byte export requires alphabet_size<=256')
path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
raw=d.x.astype(np.uint8).tobytes();path.write_bytes(raw)
path.with_suffix(path.suffix+'.json').write_text(json.dumps({'n':a.n,'sha256':hashlib.sha256(raw).hexdigest(),'format':'one unsigned byte per discrete symbol','metadata':d.metadata},indent=2)+'\n')
print(path)
