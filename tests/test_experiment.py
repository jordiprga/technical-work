import json
import numpy as np
from entropy_oracle.experiment import temporal_windows,fit_mixture,run_experiment,save_result

def test_windows_never_include_target_or_future():
    x=np.arange(30)
    X,y,t=temporal_windows(x,7)
    assert np.array_equal(y,t)
    for row,target in zip(X,t):
        np.testing.assert_array_equal(row,np.arange(target-7,target))

def test_mixture_is_convex_and_uses_validation_likelihood():
    y=np.array([0,1]*30)
    good=np.where(np.eye(2)[y],.9,.1)
    bad=good[:,::-1]
    w,ok=fit_mixture({'good':good,'bad':bad},y)
    assert ok and w['good']>.999
    assert np.isclose(sum(w.values()),1)

def test_small_run_serializes_and_covers_identical_final_targets(tmp_path):
    result=run_experiment(source='nonlinear',n=500,seed=197,models=['marginal','markov5'],bootstrap=0)
    assert result['split']['train_target_range']==[32,299]
    assert result['split']['test_target_range']==[400,499]
    assert all(row['n_test']==100 for row in result['metrics'])
    assert result['selection']['selected_model'] in ['marginal','markov5']
    path=save_result(result,tmp_path/'result.json')
    stored=json.loads(path.read_text())
    assert stored['source_metadata']['marginal_uniform']
    assert len(stored['trace']['y'])==100

def test_test_labels_do_not_affect_model_selection(monkeypatch):
    from entropy_oracle import experiment
    from entropy_oracle.sources import make_source
    data=make_source('bernoulli',n=500,seed=391,p=.6)
    monkeypatch.setattr(experiment,'make_source',lambda *a,**kw:data)
    first=run_experiment(source='bernoulli',n=500,models=['marginal','markov1'],bootstrap=0)
    data.x[400:]=1-data.x[400:]
    second=run_experiment(source='bernoulli',n=500,models=['marginal','markov1'],bootstrap=0)
    assert first['selection']==second['selection']
