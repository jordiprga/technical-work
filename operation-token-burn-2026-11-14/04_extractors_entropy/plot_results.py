#!/usr/bin/env python3
"""Generate standalone static figures from saved synthetic experiment results."""
import json
import os
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/tmp/operation-extractors-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/operation-extractors-cache")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
results=json.loads((root/'results/results.json').read_text())
rows=results['correlation_sweep']
x=[r['repeat_probability']['decimal'] for r in rows]
y=[r['tv_seed_and_pair']['decimal'] for r in rows]
z=[r['tv_seed_and_each_marginal']['decimal'] for r in rows]
fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
axes[0].plot(x,y,'o-',label='TV conjunta (S,Y1,Y2)',color='#b23a48')
axes[0].plot(x,z,'s--',label='TV marginal (S,Yi)',color='#287271')
axes[0].set(xlabel='Probabilidad de repetir el bloque anterior',ylabel='Distancia total de variación',ylim=(0,1),title='Marginales estables ocultan dependencia')
axes[0].legend();axes[0].grid(alpha=.25)
axes[1].plot(x,[r['conditional_min_entropy_X2_given_X1'] for r in rows],'o-',label='Hmin(X2 | X1)',color='#b23a48')
axes[1].plot(x,[r['marginal_min_entropy'] for r in rows],'s--',label='Hmin(X2)',color='#287271')
axes[1].set(xlabel='Probabilidad de repetir el bloque anterior',ylabel='Bits de minentropía',ylim=(-.2,6.5),title='La entropía útil es condicional')
axes[1].legend();axes[1].grid(alpha=.25)
fig.suptitle('Toeplitz: n=6, m=2; enumeración exacta de las 128 semillas',fontsize=13)
fig.savefig(root/'results/correlation_vs_entropy.png',dpi=180)
fig.savefig(root/'results/correlation_vs_entropy.svg')
plt.close(fig)
print('Generated results/correlation_vs_entropy.{png,svg}')
