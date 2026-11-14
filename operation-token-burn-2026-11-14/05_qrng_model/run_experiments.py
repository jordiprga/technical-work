"""Reproduce synthetic comparisons, CSV summaries, exact example and figures."""
from dataclasses import asdict, replace
import csv
import json
from pathlib import Path
import platform
import sys
import time
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/qrng-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/qrng-cache")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import scipy
from qrng_sim import Config, simulate, metrics, enumerate_feedback, distribution_pdf, linear_roots

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT/'results'
FIGURES = ROOT/'figures'


def scenarios(n=524288):
    b = Config(n=n,burn_in=16384)
    cases = {
        'fixed_threshold': replace(b,gain=0),
        'feedback_g0.5_w256': b,
        'feedback_g2_w256': replace(b,gain=2),
        'feedback_g5_w256': replace(b,gain=5),
        'unstable_g7_w256': replace(b,gain=7),
        'short_w32': replace(b,window=32,update_period=32),
        'long_w2048': replace(b,window=2048,update_period=2048),
        'overlap4_g0.5': replace(b,window=1024),
        'overlap4_g4': replace(b,window=1024,gain=4),
        'overlap16_g0.5': replace(b,window=4096),
        'overlap16_g2': replace(b,window=4096,gain=2),
        'deadband_0.02': replace(b,deadband=.02),
        'deadband_0.05': replace(b,deadband=.05),
        'deadband_biased': replace(b,deadband=.05,initial_threshold=.1),
        'noise_known_sigma1': replace(b,gaussian_sigma=1.,gain=0),
        'classical_ar0.99': replace(b,gaussian_rho=.99),
        'classical_ar0.99_fixed': replace(b,gaussian_rho=.99,gain=0),
        'phase_diffusion_0.25': replace(b,phase_mode='diffusion',phase_step_sigma=.25),
        'phase_diffusion_0.25_fixed': replace(b,phase_mode='diffusion',phase_step_sigma=.25,gain=0),
        'phase_diffusion_1': replace(b,phase_mode='diffusion',phase_step_sigma=1.),
        'drift_fixed': replace(b,gain=0,drift_amplitude=.4,drift_period=32768),
        'drift_w256': replace(b,drift_amplitude=.4,drift_period=32768),
        'drift_w2048': replace(b,window=2048,update_period=2048,drift_amplitude=.4,drift_period=32768),
        'drift_overlap16': replace(b,window=4096,drift_amplitude=.4,drift_period=32768),
    }
    return cases


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    started = time.time()
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    rows = []
    retained = {}
    for name, config in scenarios().items():
        for rep in range(4):
            c = replace(config,seed=20261114+rep)
            result = simulate(c)
            row = {'scenario':name,'replicate':rep,**asdict(c),**metrics(result)}
            rows.append(row)
            if rep == 0:
                updates = result['updates']
                write_csv(RESULTS/(name+'_updates.csv'), [dict(zip(
                    ['sample','threshold_before','window_one_fraction','error','threshold_after','update_applied'],r))
                    for r in updates])
                retained[name] = {k: v[16384:32768].copy() for k,v in result.items()
                                  if k in ['analog','bits','threshold','classical']}
            del result
        print(name, flush=True)
    write_csv(RESULTS/'experiments.csv', rows)
    numeric = ['one_fraction','marginal_min_entropy_plugin','bit_lag1_corr','block_lag1_corr',
               'threshold_variance','threshold_rail_fraction','model_causal_sideinfo_average_min_entropy_mc',
               'model_causal_sideinfo_mean_pointwise_min_entropy_mc','model_causal_sideinfo_mean_shannon_entropy_mc',
               'context6_test_accuracy','linear_spectral_radius']
    summary = []
    for name in scenarios():
        group = [r for r in rows if r['scenario']==name]
        rec = {'scenario':name,'replicates':len(group),'n_each':group[0]['n']}
        for key in numeric:
            values = np.array([r.get(key,float('nan')) for r in group])
            rec[key+'_mean'] = float(np.mean(values))
            rec[key+'_sd'] = float(np.std(values,ddof=1))
        summary.append(rec)
    write_csv(RESULTS/'summary.csv',summary)
    exact = [enumerate_feedback(n=16,gain=g) for g in [0.,.5,1.,2.]]
    (RESULTS/'exact_feedback.json').write_text(json.dumps(exact,indent=2)+'\n')
    metadata = {'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,
                'matplotlib':matplotlib.__version__,'platform':platform.platform(),
                'seconds':time.time()-started,'replicate_seeds':[20261114+i for i in range(4)],
                'n_per_run':524288,'burn_in':16384,'scenarios':len(scenarios()),
                'warning':'All metrics are model/Monte Carlo diagnostics; no certified entropy bound.'}
    (RESULTS/'run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    make_figures(summary,retained)
    print(json.dumps(metadata,indent=2))


def make_figures(summary, retained):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    lookup = {r['scenario']:r for r in summary}
    fig,axs = plt.subplots(1,2,figsize=(12,4.3),constrained_layout=True)
    x = np.linspace(-1.6,1.6,600)
    axs[0].plot(x,distribution_pdf(x,sigma=.15),label='Arcsine * N(0, 0.15²)',lw=2)
    for name,label in [('fixed_threshold','Fase IID'),('phase_diffusion_0.25_fixed','Fase correlacionada')]:
        axs[0].hist(retained[name]['analog'],bins=70,density=True,histtype='step',label=label)
    axs[0].set(xlabel='Amplitud sintética',ylabel='Densidad',title='Marginal similar; dependencia distinta')
    axs[0].legend(fontsize=8)
    selected = ['fixed_threshold','phase_diffusion_0.25_fixed','phase_diffusion_0.25','noise_known_sigma1']
    labels = ['IID, fijo','Difusión, fijo','Difusión, control','Ruido σ=1']
    z = np.arange(len(selected))
    axs[1].bar(z-.18,[lookup[s]['marginal_min_entropy_plugin_mean'] for s in selected],.36,label='Hmin marginal empírica')
    axs[1].bar(z+.18,[lookup[s]['model_causal_sideinfo_average_min_entropy_mc_mean'] for s in selected],.36,label='Hmin causal un paso | estado (MC)')
    axs[1].set_xticks(z,labels,rotation=15)
    axs[1].set(ylabel='Bits por símbolo (métricas diferentes)',ylim=(0,1.05),title='El histograma no acredita entropía condicional')
    axs[1].legend(fontsize=8,loc='lower left')
    fig.savefig(FIGURES/'marginal_vs_conditional.png',dpi=180)
    fig.savefig(FIGURES/'marginal_vs_conditional.svg')
    plt.close(fig)

    names=['feedback_g0.5_w256','feedback_g2_w256','feedback_g5_w256']
    gains=np.array([.5,2,5])
    f=distribution_pdf([0.],sigma=.15)[0]
    fig,axs=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    axs[0].errorbar(gains,[lookup[s]['block_lag1_corr_mean'] for s in names],
                    yerr=[lookup[s]['block_lag1_corr_sd'] for s in names],fmt='o',label='Simulación ± SD, 4 semillas')
    axs[0].plot(gains,-gains*f/2,'--',label='Linealización −g f(0)/2')
    axs[0].set(xlabel='Ganancia g',ylabel='Correlación de fracción de unos entre bloques',title='El controlador crea memoria')
    axs[0].legend(fontsize=8)
    with (RESULTS/'experiments.csv').open() as stream:
        all_rows=list(csv.DictReader(stream))
    for index,name in enumerate(names):
        vals=[float(r['threshold_variance']) for r in all_rows if r['scenario']==name]
        axs[1].scatter(gains[index]+np.linspace(-.07,.07,len(vals)),vals,alpha=.7,
                       color='tab:blue',label='Cuatro réplicas' if index==0 else None)
    axs[1].scatter(gains,[lookup[s]['threshold_variance_mean'] for s in names],
                   color='black',marker='D',s=30,label='Media')
    axs[1].plot(gains,gains*.25/(256*f*(2-gains*f)),'--',label='Teoría lineal')
    axs[1].set(xlabel='Ganancia g',ylabel='Varianza del umbral',title='Mayor ganancia amplifica jitter')
    axs[1].legend(fontsize=8)
    fig.savefig(FIGURES/'feedback_theory.png',dpi=180)
    fig.savefig(FIGURES/'feedback_theory.svg')
    plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    a=np.linspace(.01,2.3,400)
    for ratio in [1,4,16]:
        rho=[max(abs(linear_roots(v,1.,ratio))) for v in a]
        axs[0].plot(a,rho,label=f'W/U={ratio}')
    axs[0].axhline(1,color='black',ls=':')
    axs[0].set(xlabel='Ganancia adimensional a = g f(0)',ylabel='Radio espectral',title='Solapar ventanas cambia la estabilidad',ylim=(.6,1.4))
    axs[0].legend()
    for name,label in [('overlap4_g0.5','W/U=4, g=.5'),('overlap4_g4','W/U=4, g=4'),('overlap16_g2','W/U=16, g=2')]:
        data=np.genfromtxt(RESULTS/(name+'_updates.csv'),delimiter=',',names=True)
        sub=data[(data['sample']>=32768)&(data['sample']<=65536)]
        axs[1].plot(sub['sample'],sub['threshold_after'],label=label,alpha=.8)
    axs[1].set(xlabel='Muestra',ylabel='Umbral',title='Oscilación bajo ganancia y memoria altas')
    axs[1].legend(fontsize=8)
    fig.savefig(FIGURES/'overlap_stability.png',dpi=180)
    fig.savefig(FIGURES/'overlap_stability.svg')
    plt.close(fig)

    fig,axs=plt.subplots(2,1,figsize=(10,7),constrained_layout=True)
    t=np.arange(0,131072,256)
    axs[0].plot(t,.4*np.sin(2*np.pi*t/32768),'k--',label='Offset sintético')
    for name,label in [('drift_w256','W=U=256'),('drift_w2048','W=U=2048'),('drift_overlap16','W=4096, U=256')]:
        data=np.genfromtxt(RESULTS/(name+'_updates.csv'),delimiter=',',names=True)
        data=data[data['sample']<=131072]
        axs[0].plot(data['sample'],data['threshold_after'],label=label,alpha=.8)
        axs[1].plot(data['sample'],data['window_one_fraction'],label=label,alpha=.8)
    axs[0].set(ylabel='Umbral/offset',title='Ventana, cadencia y retardo frente a deriva')
    axs[1].set(xlabel='Muestra',ylabel='Fracción de unos en ventana')
    axs[0].legend(ncol=2,fontsize=8)
    fig.savefig(FIGURES/'drift_tracking.png',dpi=180)
    fig.savefig(FIGURES/'drift_tracking.svg')
    plt.close(fig)

if __name__=='__main__':
    main()
