"""Chronological frozen-predictor evaluation and validation-only ensembling."""
from __future__ import annotations
import contextlib
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
from .sources import make_source
from .statistics import score_predictions, paired_comparison

ALL_MODELS = BASELINE_NAMES + ['gru', 'transformer', 'flow']

def temporal_windows(x, window=32):
    """Target t uses x[t-window:t]. Returned target indices refer to raw data."""
    x = np.asarray(x, dtype=np.int64)
    if window < 1 or len(x) <= window:
        raise ValueError('Require 1 <= window < n')
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
    if not np.allclose(p.sum(axis=1), 1, atol=1e-5):
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


def run_experiment(source='nonlinear', n=12000, seed=0, models=None, window=32,
                   epochs=15, source_params=None, bootstrap=300, train_size=None,
                   progress=None, alpha=.05):
    if n < max(200, window*5):
        raise ValueError('n must be at least max(200,5*window)')
    if models is None or models == 'all':
        models = ALL_MODELS.copy()
    elif isinstance(models, str):
        models = models.split(',')
    models = list(dict.fromkeys(models))
    if not models or set(models)-set(ALL_MODELS):
        raise ValueError(f'Models must be a nonempty subset of {ALL_MODELS}')
    source_params = source_params or {}
    data = make_source(source, n=n, seed=seed, **source_params)
    X, y, indices = temporal_windows(data.x, window)
    train_end, val_end = int(.6*n), int(.8*n)
    train_idx = np.flatnonzero(indices < train_end)
    val_idx = np.flatnonzero((indices >= train_end) & (indices < val_end))
    test_idx = np.flatnonzero(indices >= val_end)
    if train_size is not None:
        if not 1 <= train_size <= len(train_idx):
            raise ValueError(f'train_size must be in [1,{len(train_idx)}]')
        train_idx = train_idx[:int(train_size)]
    a = data.alphabet_size
    val_probs, test_probs, rows, histories = {}, {}, [], {}
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
            tp = validate_probabilities(model.predict_proba(X[test_idx]), len(test_idx), a)
            predict_seconds = time.perf_counter()-started
        val_probs[name], test_probs[name] = vp, tp
        row = score_predictions(y[test_idx], tp, alpha=alpha, block_length=max(window,32),seed=seed,bootstrap=bootstrap)
        row.update(model=name, val_accuracy=float(np.mean(vp.argmax(1)==y[val_idx])),
                   val_log_loss_bits=float(-np.log2(np.clip(vp[np.arange(len(val_idx)),y[val_idx]],1e-15,1)).mean()),
                   fit_seconds=fit_seconds, predict_seconds=predict_seconds,
                   process_peak_rss_mb=memory.peak/2**20, incremental_rss_mb=(memory.peak-memory.initial)/2**20,
                   trained=True, evaluated_on_test=True)
        rows.append(row)
        histories[name] = getattr(model, 'history', [])
        if progress:
            progress(f'{name}: test accuracy={row["accuracy"]:.4f}, log-loss={row["log_loss_bits"]:.4f} bits, fit={fit_seconds:.2f}s')
        del model
    # Both policies are finalized without using test labels or test metrics.
    selected = max(models, key=lambda name:(float(np.mean(val_probs[name].argmax(1)==y[val_idx])),
                float(np.log(np.maximum(val_probs[name][np.arange(len(val_idx)), y[val_idx]],1e-15)).mean())))
    weights, optimized = fit_mixture(val_probs, y[val_idx])
    test_probs['selected'] = test_probs[selected]
    test_probs['ensemble'] = sum(weights[k]*test_probs[k] for k in models)
    for name in ('selected','ensemble'):
        row = score_predictions(y[test_idx],test_probs[name],alpha=alpha,block_length=max(window,32),seed=seed,bootstrap=bootstrap)
        row.update(model=name,fit_seconds=0.,predict_seconds=0.,process_peak_rss_mb=None,
                   incremental_rss_mb=None,trained=False,evaluated_on_test=True)
        rows.append(row)
    if data.oracle_probs is not None:
        oracle = np.asarray(data.oracle_probs)[indices[test_idx]]
        if np.isfinite(oracle).all():
            oracle = validate_probabilities(oracle,len(test_idx),a)
            test_probs['oracle'] = oracle
            row = score_predictions(y[test_idx],oracle,alpha=alpha,block_length=max(window,32),seed=seed,bootstrap=bootstrap)
            row.update(model='oracle',oracle_expected_accuracy=float(oracle.max(1).mean()),
                       fit_seconds=0.,predict_seconds=0.,process_peak_rss_mb=None,
                       trained=False,evaluated_on_test=True)
            rows.append(row)
    # Prespecified paired contrasts, Bonferroni within this run; no test-best selection.
    reference = 'markov5' if 'markov5' in models else 'marginal' if 'marginal' in models else models[0]
    candidates = ['selected','ensemble'] + (['transformer'] if 'transformer' in models else [])
    comparisons = []
    for name in candidates:
        cmp = paired_comparison(y[test_idx],test_probs[name],test_probs[reference],
                                 alpha=alpha/len(candidates),block_length=max(window,32),seed=seed,bootstrap=bootstrap)
        cmp.update(model_a=name,model_b=reference,family_size=len(candidates),family_alpha=alpha)
        comparisons.append(cmp)
    trace_count=min(1024,len(test_idx))
    versions={}
    for pkg in ('numpy','scipy','scikit-learn','torch','streamlit','plotly'):
        with contextlib.suppress(importlib.metadata.PackageNotFoundError):
            versions[pkg]=importlib.metadata.version(pkg)
    return {'schema_version':1,'config':{'source':source,'n':n,'seed':seed,'models':models,'window':window,
             'epochs':epochs,'source_params':source_params,'bootstrap':bootstrap,'alpha':alpha,'train_size':train_size},
            'split':{'train_count':len(train_idx),'validation_count':len(val_idx),'test_count':len(test_idx),
                     'train_target_range':[int(indices[train_idx[0]]),int(indices[train_idx[-1]])],
                     'validation_target_range':[train_end,val_end-1],'test_target_range':[val_end,n-1],
                     'protocol':'chronological 60/20/20; observed past test symbols may appear in later contexts; frozen weights'},
            'source_metadata':data.metadata,'empirical_marginal':(np.bincount(data.x,minlength=a)/n).tolist(),
            'metrics':rows,'selection':{'selected_model':selected,'ensemble_weights':weights,
                                      'mixture_optimizer_success':optimized,'criterion':'validation accuracy; tie-break validation log-loss; mixture validation log-loss'},
            'histories':histories,'comparisons':comparisons,
            'trace':{'indices':indices[test_idx[:trace_count]].tolist(),'y':y[test_idx[:trace_count]].tolist(),
                     'probabilities':{k:v[:trace_count].tolist() for k,v in test_probs.items()}},
            'environment':{'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count(),'versions':versions},
            'limitations':['Predictor performance does not certify a lower bound on source min-entropy.',
                            'Martingale intervals target trajectory-average conditional success, not future stationary risk.',
                            'Block bootstrap is exploratory under stationarity and suitable mixing, invalid generally for drift.',
                            'Memory is sampled whole-process RSS, not isolated model allocations.',
                            'Repeated exploration of final tests invalidates confirmatory interpretation.']}


def save_result(result, path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return path
