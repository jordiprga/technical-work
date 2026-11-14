"""Deterministic mean-map two-cycles, distinct from stochastic stationarity."""
import csv
import json
import math
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/qrng-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/qrng-cache')
from pathlib import Path
import numpy as np
from scipy.special import ndtr
from scipy.optimize import brentq, minimize_scalar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class MeanMap:
    def __init__(self,amplitude=1.,sigma=.15,nodes=4096):
        if amplitude<=0 or sigma<=0:
            raise ValueError('positive amplitude and Gaussian sigma required')
        self.amplitude=amplitude
        self.sigma=sigma
        self.centers=amplitude*np.cos(2*np.pi*(np.arange(nodes)+.5)/nodes)

    def p(self,theta):
        return float(np.mean(ndtr((self.centers-theta)/self.sigma)))

    def density(self,theta):
        return float(np.mean(np.exp(-.5*((theta-self.centers)/self.sigma)**2)) /
                     (self.sigma*np.sqrt(2*np.pi)))

    def cycle_gain(self,theta):
        if theta<=0:
            return 2/self.density(0.)
        return 2*theta/(.5-self.p(theta))

    def cycles(self,gain,upper=3.,points=400):
        grid=np.linspace(1e-5,upper,points)
        values=[self.cycle_gain(t)-gain for t in grid]
        roots=[]
        for left,right,fl,fr in zip(grid[:-1],grid[1:],values[:-1],values[1:]):
            if fl*fr<0:
                r=brentq(lambda t:self.cycle_gain(t)-gain,left,right,xtol=1e-13)
                multiplier=(1-gain*self.density(r))**2
                roots.append({'amplitude':r,'two_step_multiplier':multiplier,
                              'locally_stable':bool(multiplier<1)})
        return roots

    def saddle_node(self):
        grid=np.linspace(.01,2*self.amplitude+4*self.sigma,400)
        vals=[self.cycle_gain(t) for t in grid]
        idx=int(np.argmin(vals))
        bracket=(grid[max(0,idx-1)],grid[min(len(grid)-1,idx+1)])
        fit=minimize_scalar(self.cycle_gain,bounds=bracket,method='bounded',
                            options={'xatol':1e-13})
        return {'amplitude':float(fit.x),'gain':float(fit.fun),
                'optimizer_success':bool(fit.success)}


def main():
    root=Path(__file__).resolve().parent
    m=MeanMap()
    critical=2/m.density(0.)
    saddle=m.saddle_node()
    records=[]
    for gain in np.linspace(3.7,7.,100):
        for cycle in m.cycles(float(gain)):
            records.append({'gain':float(gain),**cycle})
    detail={'amplitude':1.,'gaussian_sigma':.15,'quadrature_nodes':4096,
            'local_zero_threshold_critical_gain':critical,
            'symmetric_two_cycle_saddle_node':saddle,
            'examples':{str(g):m.cycles(g) for g in [4.,4.5,5.,5.5,6.,6.3,7.]},
            'scope':'deterministic nonlinear mean map, W=U; numerical bifurcation, no invariant-distribution claim'}
    (root/'results/nonlinear_bifurcation.json').write_text(json.dumps(detail,indent=2)+'\n')
    with (root/'results/nonlinear_cycles.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    fig,ax=plt.subplots(figsize=(8,4.8),constrained_layout=True)
    for state,color,label in [(True,'tab:blue','Ciclo ±θ estable'),(False,'tab:orange','Ciclo ±θ inestable')]:
        subset=[r for r in records if r['locally_stable']==state]
        ax.plot([r['gain'] for r in subset],[r['amplitude'] for r in subset],color=color,label=label)
    ax.plot([3.7,critical],[0,0],color='green',lw=3,label='Equilibrio θ=0 estable')
    ax.plot([critical,7],[0,0],color='red',ls='--',label='Equilibrio θ=0 inestable')
    ax.axvspan(saddle['gain'],critical,color='grey',alpha=.12,label='Coexistencia en el mapa medio')
    ax.set(xlabel='Ganancia g por actualización',ylabel='Amplitud de umbral |θ|',
           title='Estabilidad local y coexistencia de ciclos (A=1, σ=0.15)')
    ax.spines[['right','top']].set_visible(False)
    ax.legend(fontsize=9)
    fig.savefig(root/'figures/nonlinear_bifurcation.png',dpi=180)
    fig.savefig(root/'figures/nonlinear_bifurcation.svg')
    plt.close(fig)
    print(json.dumps(detail,indent=2))

if __name__=='__main__':
    main()
