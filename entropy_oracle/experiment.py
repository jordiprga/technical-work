"""Chronological frozen-predictor evaluation and validation-only ensembling."""
from __future__ import annotations
import contextlib
import hashlib
import importlib.metadata
import json
import os
import platform
import threading
import time
from pathlib import Path
import numpy as np
import psutil
from scipy.optimize import minimize
from .baselines import BASELINE_NAMES, build_baseline
from .sources import make_source, SourceData
from .statistics import score_predictions, paired_comparison

ALL_MODELS = BASELINE_NAMES + ['gru', 'transformer', 'flow']


def temporal_windows(x, window=32):
    """Target t uses x[t-window:t]. Returned target indices refer to raw data."""
    x = np.asarray(x)
    if x.ndim != 1 or not np.issubdtype(x.dtype, np.integer):
        raise ValueError('Samples must be a one-dimensional integer array')
    if not isinstance(window, (int, np.integer)) or window < 1 or len(x) <= window:
        raise ValueError('Require integer 1 <= window < n')
    view = np.lib.stride_tricks.sliding_window_view(x, window+1)
    return view[:, :-1].copy(), view[:, -1].copy(), np.arange(window, len(x))


def build_model(name, alphabet_size, window, seed, epochs):
    if name in BASELINE_NAMES:
        return build_baseline(name, alphabet_size, window=window, seed=seed)
    if name in ('gru', 'transformer'):
        from .neural import build_neural
        return build_neural(name, alphabet_size, window=window, seed=seed, epochs=epochs)
    if name == 'flow':
        from .flows import build_flow
        return build_flow(alphabet_size, window=window, seed=seed, epochs=epochs)
    raise ValueError(f'Unknown model {name!r}; choose {ALL_MODELS}')


class MemoryMonitor:
    """Sample whole-process RSS; delta is incremental, not isolated model memory."""
    def __enter__(self):
        self.proc = psutil.Process()
        self.initial = self.proc.memory_info().rss
        self.peak = self.initial
        self.stop = threading.Event()
        def watch():
            while not self.stop.wait(.02):
                self.peak = max(self.peak, self.proc.memory_info().rss)
        self.thread = threading.Thread(target=watch, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.peak = max(self.peak, self.proc.memory_info().rss)
        self.stop.set()
        self.thread.join()


def validate_probabilities(p, n, a):
    p = np.asarray(p, dtype=np.float64)
    if p.shape != (n, a) or not np.isfinite(p).all() or (p < 0).any():
        raise ValueError('Invalid predictive probability matrix')
    if not np.allclose(p.sum(axis=1), 1, rtol=1e-6, atol=1e-8):
        raise ValueError('Predictive probabilities do not sum to one')
    return p


def fit_mixture(probabilities, labels):
    """Convex simplex mixture weights chosen exclusively on validation log-loss."""
    names = list(probabilities)
    likelihoods = np.stack([probabilities[k][np.arange(len(labels)), labels] for k in names], axis=1)
    def objective(w):
        return -np.log(np.maximum(likelihoods @ w, 1e-12)).mean()
    def gradient(w):
        return -(likelihoods / np.maximum(likelihoods @ w, 1e-12)[:, None]).mean(axis=0)
    result = minimize(objective, np.full(len(names), 1/len(names)), jac=gradient,
                      bounds=[(0,1)]*len(names), constraints={'type':'eq','fun':lambda w:w.sum()-1,
                      'jac':lambda w:np.ones_like(w)}, method='SLSQP', options={'maxiter':200,'ftol':1e-10})
    w = np.maximum(result.x if result.success else np.full(len(names),1/len(names)), 0)
    w /= w.sum()
    return dict(zip(names, w.tolist())), bool(result.success)


def _source_digest(x):
    return hashlib.sha256(np.asarray(x, dtype='<i8').tobytes()).hexdigest()


def _code_provenance():
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(Path(__file__).parent.glob('*.py'))}
    return {'module_sha256': files,
            'combined_sha256': hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()}


def run_experiment(source='nonlinear', n=12000, seed=0, models=None, window=32,
                   epochs=15, source_params=None, bootstrap=300, train_size=None,
                   progress=None, alpha=.05, data: SourceData | None=None):
    """Fit all candidates, freeze validation policies, then open the final test.

    ``data`` admits an explicitly declared discrete external source. ``_audit``
    in the returned dict contains numpy arrays; ``save_result`` writes these to
    a compressed non-pickle NPZ and excludes private keys from JSON.
    """
    if data is not None:
        source = str(data.metadata.get('source', 'file'))
        n = len(data.x)
        if source_params:
            raise ValueError('source_params cannot be used together with supplied data')
    if not isinstance(n,(int,np.integer)) or not isinstance(window,(int,np.integer)):
        raise ValueError('n and window must be integers')
    if window < 1 or n < max(200, window*5):
        raise ValueError('window must be positive; n must be at least max(200,5*window)')
    if not 0 < alpha < 1 or not isinstance(bootstrap,(int,np.integer)) or bootstrap < 0:
        raise ValueError('Require 0 < alpha < 1 and nonnegative integer bootstrap')
    if models is None or models == 'all':
        models = ALL_MODELS.copy()
    elif isinstance(models, str):
        models = [v.strip() for v in models.split(',')]
    models = list(dict.fromkeys(models))
    if not models or set(models)-set(ALL_MODELS):
        raise ValueError(f'Models must be a nonempty subset of {ALL_MODELS}')
    source_params = source_params or {}
    if data is None:
        data = make_source(source, n=n, seed=seed, **source_params)
    x = np.asarray(data.x)
    a = data.alphabet_size
    if not isinstance(a,(int,np.integer)) or a<2 or x.ndim!=1 or not np.issubdtype(x.dtype,np.integer):
        raise ValueError('Source requires a one-dimensional integer sequence and alphabet_size>=2')
    if a > 4096:
        raise ValueError('Dense predictors support at most 4096 declared symbols; supply an explicit justified discretization before benchmarking')
    # A conservative allocation estimate, not an isolated-process memory guarantee.
    estimated_bytes = n*window*8 + n*a*len(models)*8 + (.6*n*window*a*4 if 'mlp' in models and a>2 else 0)
    if estimated_bytes > 2*1024**3:
        raise ValueError('Estimated dense arrays exceed 2 GiB; reduce sample count, window, alphabet or model set without silently remapping symbols')
    if np.any(x < 0) or np.any(x >= a):
        raise ValueError('Source symbols must lie in the declared alphabet')
    X, y, indices = temporal_windows(x, window)
    train_end, val_end = int(.6*n), int(.8*n)
    train_idx = np.flatnonzero(indices < train_end)
    val_idx = np.flatnonzero((indices >= train_end) & (indices < val_end))
    test_idx = np.flatnonzero(indices >= val_end)
    if train_size is not None:
        if not isinstance(train_size,(int,np.integer)) or not 1 <= train_size <= len(train_idx):
            raise ValueError(f'train_size must be an integer in [1,{len(train_idx)}]')
        train_idx = train_idx[:int(train_size)]
    # Unknown or explicitly nonstationary sources get only distribution-free bounds.
    stationary = data.metadata.get('stationary') is True
    effective_bootstrap = bootstrap if stationary else 0
    bootstrap_reason = ('Exploratory only: stationary source declared; score-process mixing and block length still require justification.'
                        if stationary else 'Disabled: source stationarity is false or unknown; martingale bounds remain available.')
    val_probs, test_probs, rows, histories, fitted, costs = {}, {}, [], {}, {}, {}
    for name in models:
        if progress:
            progress(f'Training {name}')
        model = build_model(name, a, window, seed, epochs)
        with MemoryMonitor() as memory:
            started = time.perf_counter()
            model.fit(X[train_idx], y[train_idx], X_val=X[val_idx], y_val=y[val_idx])
            fit_seconds = time.perf_counter()-started
            started = time.perf_counter()
            vp = validate_probabilities(model.predict_proba(X[val_idx]), len(val_idx), a)
            val_seconds = time.perf_counter()-started
        val_probs[name], fitted[name] = vp, model
        histories[name] = getattr(model, 'history', [])
        costs[name] = {'fit_seconds':fit_seconds,'validation_predict_seconds':val_seconds,
                       'process_peak_rss_mb':memory.peak/2**20,
                       'incremental_rss_mb':(memory.peak-memory.initial)/2**20,
                       'best_epoch':getattr(model,'best_epoch',getattr(model,'best_epoch_',None))}
        if progress:
            progress(f'{name}: training complete ({fit_seconds:.2f}s); validation accuracy={np.mean(vp.argmax(1)==y[val_idx]):.4f}')
    # No final-test inference, metrics, callbacks or labels have been used above.
    selection_started = time.perf_counter()
    selected = max(models, key=lambda name:(float(np.mean(val_probs[name].argmax(1)==y[val_idx])),
                float(np.log(np.maximum(val_probs[name][np.arange(len(val_idx)), y[val_idx]],1e-15)).mean())))
    weights, optimized = fit_mixture(val_probs, y[val_idx])
    selection_seconds = time.perf_counter()-selection_started
    if progress:
        progress(f'Validation policies frozen: selected={selected}; opening final test')
    def score(p):
        row=score_predictions(y[test_idx],p,alpha=alpha,block_length=max(window,32),seed=seed,bootstrap=effective_bootstrap)
        row['bootstrap_status']=bootstrap_reason
        return row
    for name in models:
        with MemoryMonitor() as memory:
            started=time.perf_counter()
            tp=validate_probabilities(fitted[name].predict_proba(X[test_idx]),len(test_idx),a)
            test_seconds=time.perf_counter()-started
        test_probs[name]=tp
        costs[name]['predict_seconds']=test_seconds
        costs[name]['process_peak_rss_mb']=max(costs[name]['process_peak_rss_mb'],memory.peak/2**20)
        vp=val_probs[name]
        row=score(tp)
        row.update(model=name,val_accuracy=float(np.mean(vp.argmax(1)==y[val_idx])),
                   val_log_loss_bits=float(-np.log2(np.maximum(vp[np.arange(len(val_idx)),y[val_idx]],1e-15)).mean()),
                   trained=True,evaluated_on_test=True,cost_scope='individual fit; test-only inference',**costs[name])
        rows.append(row)
        if progress:
            progress(f'{name}: test accuracy={row["accuracy"]:.4f}, log-loss={row["log_loss_bits"]:.4f} bits')
        del fitted[name]
    test_probs['selected'] = test_probs[selected]
    started=time.perf_counter()
    test_probs['ensemble'] = sum(weights[k]*test_probs[k] for k in models)
    combination_seconds=time.perf_counter()-started
    search_fit_seconds=sum(c['fit_seconds'] for c in costs.values())+selection_seconds
    for name in ('selected','ensemble'):
        row=score(test_probs[name])
        prediction_cost=(costs[selected]['predict_seconds'] if name=='selected'
                         else sum(c['predict_seconds'] for c in costs.values())+combination_seconds)
        row.update(model=name,fit_seconds=search_fit_seconds,predict_seconds=prediction_cost,
                   process_peak_rss_mb=None,incremental_rss_mb=None,trained=False,evaluated_on_test=True,
                   cost_scope='candidate search fit + policy selection; deployment inference components')
        rows.append(row)
    if data.oracle_probs is not None:
        oracle = np.asarray(data.oracle_probs)[indices[test_idx]]
        oracle = validate_probabilities(oracle,len(test_idx),a)
        test_probs['oracle'] = oracle
        row=score(oracle)
        row.update(model='oracle',oracle_expected_accuracy=float(oracle.max(1).mean()),
                   fit_seconds=0.,predict_seconds=0.,process_peak_rss_mb=None,
                   trained=False,evaluated_on_test=True)
        rows.append(row)
        for row in rows:
            p=test_probs[row['model']]
            row['oracle_conditional_predictor_success']=float(oracle[np.arange(len(test_idx)),p.argmax(1)].mean())
            row['oracle_reference_is_approximate']=bool(data.metadata.get('oracle_is_approximate',False))
    reference = 'markov5' if 'markov5' in models else 'marginal' if 'marginal' in models else models[0]
    candidates = ['selected','ensemble'] + (['transformer'] if 'transformer' in models else [])
    comparisons=[]
    for name in candidates:
        cmp=paired_comparison(y[test_idx],test_probs[name],test_probs[reference],alpha=alpha/len(candidates),
                              block_length=max(window,32),seed=seed,bootstrap=effective_bootstrap)
        cmp.update(model_a=name,model_b=reference,family_size=len(candidates),family_alpha=alpha,
                   bootstrap_status=bootstrap_reason)
        comparisons.append(cmp)
    versions={}
    for pkg in ('numpy','scipy','scikit-learn','torch','streamlit','plotly'):
        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            versions[pkg]=importlib.metadata.version(pkg)
    trace_count=min(1024,len(test_idx))
    return {'schema_version':2,'config':{'source':source,'n':int(n),'seed':seed,'models':models,'window':window,
             'epochs':epochs,'source_params':source_params,'bootstrap':bootstrap,'alpha':alpha,'train_size':train_size},
            'split':{'train_count':len(train_idx),'validation_count':len(val_idx),'test_count':len(test_idx),
                     'train_target_range':[int(indices[train_idx[0]]),int(indices[train_idx[-1]])],
                     'validation_target_range':[train_end,val_end-1],'test_target_range':[val_end,n-1],
                     'protocol':'chronological 60/20/20; all policies fixed before final-test inference; observed past test symbols allowed in later contexts'},
            'source_metadata':data.metadata,'empirical_marginal':(np.bincount(x,minlength=a)/n).tolist(),
            'source_sequence_sha256':_source_digest(x),'source_hash_encoding':'little-endian int64 symbols',
            'bootstrap_policy':{'requested':bootstrap,'effective':effective_bootstrap,'reason':bootstrap_reason},
            'metrics':rows,'selection':{'selected_model':selected,'ensemble_weights':weights,
                                      'mixture_optimizer_success':optimized,'selection_seconds':selection_seconds,
                                      'criterion':'validation accuracy; tie-break validation log-loss; mixture validation log-loss'},
            'histories':histories,'comparisons':comparisons,
            'trace':{'indices':indices[test_idx[:trace_count]].tolist(),'y':y[test_idx[:trace_count]].tolist(),
                     'probabilities':{k:v[:trace_count].tolist() for k,v in test_probs.items()}},
            '_audit':{'target_indices':indices[test_idx].copy(),'y':y[test_idx].copy(),'probabilities':test_probs},
            'provenance':_code_provenance(),
            'environment':{'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count(),'versions':versions},
            'limitations':['Predictor performance does not certify a lower bound on source min-entropy.',
                            'Martingale intervals target trajectory-average conditional success, not future stationary risk.',
                            'Block bootstrap needs stationarity and score-process mixing; disabled if source stationarity is false or unknown.',
                            'Memory is sampled whole-process RSS, not isolated model allocations.',
                            'Repeated exploration of final tests invalidates confirmatory interpretation.']}


def save_result(result, path):
    """Persist public JSON and full auditable predictions without modifying result."""
    from .artifacts import write_prediction_archive, verify_prediction_metrics
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    public={key:value for key,value in result.items() if not key.startswith('_')}
    if '_audit' in result:
        archive_path=path.with_suffix('.predictions.npz')
        public['prediction_archive']=write_prediction_archive(result['_audit'],archive_path)
        verify_prediction_metrics(public,archive_path)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(public,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)
    return path
