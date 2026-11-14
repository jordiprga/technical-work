"""Independent quadrature checks; parameter sensitivity remains model-dependent."""
import json
import math
from pathlib import Path
from scipy.integrate import quad
from scipy.special import ndtr
from nonlinear_bifurcation import MeanMap
from qrng_sim import center_density


def known_noise_guess(sigma,amplitude=1.):
    """Exact 1D integral for theta=0, iid phase, revealed N(0,sigma²)."""
    if sigma==0:
        return .5
    def integrand(u):
        c=amplitude*math.sin(u)
        density=math.exp(-.5*(c/sigma)**2)/(sigma*math.sqrt(2*math.pi))
        return 2*density*(.5+u/math.pi)*amplitude*math.cos(u)
    core,error=quad(integrand,0,math.pi/2,epsabs=2e-13,epsrel=2e-13)
    return core+2*float(ndtr(-amplitude/sigma))


def main():
    convergence=[]
    for nodes in [256,1024,4096,16384]:
        m=MeanMap(nodes=nodes)
        convergence.append({'phase_nodes':nodes,'saddle_node':m.saddle_node(),
                            'g5_cycles':m.cycles(5.),
                            'center_density_error_vs_bessel':m.density(0.)-center_density()})
    rows=[]
    for sigma in [.01,.05,.15,.3,.6,1.]:
        guess=known_noise_guess(sigma)
        rows.append({'classical_sigma':sigma,'marginal_bit_min_entropy':1.,
                     'causal_revealed_noise_guess_probability':guess,
                     'causal_revealed_noise_average_min_entropy':-math.log2(guess),
                     'center_density':center_density(sigma=sigma),
                     'mean_map_local_critical_gain':2/center_density(sigma=sigma)})
    result={'quadrature_convergence':convergence,'known_noise_integral':rows,
            'scope':'fixed theta=0 for noise integral; no future controller transcript; deterministic quadrature error not physical uncertainty'}
    root=Path(__file__).resolve().parent/'results'
    (root/'numerical_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
