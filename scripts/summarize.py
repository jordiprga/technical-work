#!/usr/bin/env python3
"""Generate measured tables, simultaneous contrasts and self-contained charts."""
import argparse
import json
import math
from pathlib import Path
import pandas as pd
import plotly.express as px

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,default=ROOT/'results'/'v2')
    args=parser.parse_args()
    base=args.results.resolve()
    records=[]; paired=[]; configurations=[]
    for group in ['main','iid','ar1']:
        for path in sorted((base/group).glob('*.json')):
            r=json.loads(path.read_text())
            configurations.append(r['config'])
            for m in r['metrics']:
                records.append(dict(source=r['config']['source'],seed=r['config']['seed'],artifact=str(path.relative_to(base)),**m))
            if group=='main':
                paired += [dict(seed=r['config']['seed'],**p) for p in r['comparisons']]
    if not records:
        raise SystemExit('No measured result files found; run scripts/run_suite.sh first.')
    df=pd.DataFrame(records)
    df.to_csv(base/'metrics.csv',index=False)
    summary=df.groupby(['source','model'],sort=False).agg(
        runs=('seed','count'),accuracy_mean=('accuracy','mean'),accuracy_sd=('accuracy','std'),
        log_loss_bits_mean=('log_loss_bits','mean'),fit_seconds_mean=('fit_seconds','mean'),
        peak_rss_mb_max=('process_peak_rss_mb','max')).reset_index()
    summary.to_csv(base/'summary.csv',index=False)
    for p in paired:
        rad=math.sqrt(2*math.log(2*len(paired)/.05)/p['n_test'])
        p['global_family_ci_low']=max(-1,p['delta_accuracy']-rad)
        p['global_family_ci_high']=min(1,p['delta_accuracy']+rad)
    (base/'simultaneous_comparisons.json').write_text(json.dumps({'family_alpha':.05,'family_size':len(paired),'comparisons':paired},indent=2)+'\n')
    seeds=sorted({c['seed'] for c in configurations})
    status=[]
    for name,group in df.groupby('model',sort=False):
        status.append({'model':name,'trained_runs':int(group.trained.sum()),'test_evaluated_runs':int(group.evaluated_on_test.sum()),
                       'sources':sorted(group.source.unique().tolist())})
    (base/'model_status.json').write_text(json.dumps(status,indent=2)+'\n')
    lines=['# Measured results — v0.2','',
        f'Generated directly from {len(configurations)} saved benchmark JSON files. Seeds: {seeds}. Accuracy SD describes seed variability, not a confidence interval. CPU timings can vary with concurrent load.','',
        'All 14 base predictors were trained and evaluated. The MLP now restores the checkpoint with minimum temporal validation log-loss. Previous v0.1 data remain separately archived; version comparisons using different seeds are descriptive, not paired causal claims.','',
        '| Source | Predictor | Accuracy mean | Seed SD | Log-loss bits | Fit seconds mean |',
        '|---|---|---:|---:|---:|---:|']
    for row in summary.itertuples():
        lines.append(f'| {row.source} | {row.model} | {row.accuracy_mean:.5f} | {row.accuracy_sd:.5f} | {row.log_loss_bits_mean:.5f} | {row.fit_seconds_mean:.3f} |')
    lines += ['', '## Simultaneous nonlinear contrasts', '',
        f'Two-sided paired conditional Hoeffding bounds, Bonferroni over all {len(paired)} contrasts across the recorded seeds; family coverage at least 95%. Target: realized trajectory-average conditional success difference. These are not future-population guarantees.','',
        '| Seed | A vs Markov-5 | Accuracy difference | Simultaneous lower | Simultaneous upper |',
        '|---:|---|---:|---:|---:|---:|']
    for p in paired:
        lines.append(f'| {p["seed"]} | {p["model_a"]} | {p["delta_accuracy"]:.5f} | {p["global_family_ci_low"]:.5f} | {p["global_family_ci_high"]:.5f} |')
    positive=sum(p['global_family_ci_low']>0 for p in paired)
    lines += ['',f'{positive} of {len(paired)} family-adjusted lower bounds are positive. RF and boosting also exploit the nonlinear source; these data do not establish superiority of attention or flows over all shallow ML.','',
        'Nonlinear source: exact marginal min-entropy 2 bits; full-history optimal success 0.485; average conditional min-entropy and block min-entropy rate 1.043943 bits; Shannon entropy rate 1.194392 bits. These identities follow from this specified source, not from trained models.','',
        'AR(1): the metadata numerical bound uses the latent previous continuous state. No exact observed-quantized-history oracle is claimed.','',
        'Every run includes a complete compressed NPZ with labels, target indices and all test probabilities. SHA-256 and metrics are independently checked with `python scripts/verify_results.py results/v2 --require-audit`. This detects inconsistency or corruption; a hash does not prove the absence of methodological error.','',
        'Policy costs include the candidate search and selected/ensemble inference components; original model rows report their individual fit and test-only inference. RSS is whole-process sampled memory.','',
        'Exploratory block bootstrap is suppressed when the declared source is nonstationary or of unknown stationarity. Martingale intervals remain available. Learning curves use a separate seed 201 with fixed validation/test segments and are exploratory.']
    (base/'REPORT.md').write_text('\n'.join(lines)+'\n')
    visible=summary[summary.model.isin(['marginal','markov2','markov5','gb','rf','mlp','gru','transformer','flow','ensemble'])]
    for metric,label in [('accuracy_mean','Test accuracy (mean over source realizations)'),('log_loss_bits_mean','Test log-loss (bits per symbol)')]:
        fig=px.bar(visible,x='model',y=metric,color='model',facet_col='source',title=label,
                   color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(template='plotly_dark',showlegend=False)
        fig.write_html(base/f'{metric}.html',include_plotlyjs=True)
    print(f'Summarized {len(records)} predictor evaluations into {base}/REPORT.md, CSV and HTML charts.')


if __name__=='__main__': main()
