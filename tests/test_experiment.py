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
    for key in ['selected_model','ensemble_weights','mixture_optimizer_success','criterion']:
        assert first['selection'][key]==second['selection'][key]


def test_bootstrap_disabled_for_drift_and_unknown_real_source():
    from entropy_oracle.data import load_discrete_bytes
    real=load_discrete_bytes(bytes([0,1])*250,'samples.bin',2)
    for kwargs in [dict(source='drift',n=500),dict(data=real)]:
        result=run_experiment(models=['marginal'],bootstrap=20,**kwargs)
        assert result['bootstrap_policy']['effective']==0
        assert all(row['bootstrap_ci_low'] is None for row in result['metrics'])
        assert all(row['success_ci_low'] is not None for row in result['metrics'])


def test_full_test_archive_verifies_beyond_ui_trace(tmp_path):
    from entropy_oracle.artifacts import load_prediction_archive,verify_prediction_metrics
    result=run_experiment(source='bernoulli',n=6000,models=['marginal'],bootstrap=0)
    assert len(result['trace']['y'])==1024
    assert len(result['_audit']['y'])==1200
    path=save_result(result,tmp_path/'audit.json')
    stored=json.loads(path.read_text())
    assert '_audit' not in stored
    archive=path.parent/stored['prediction_archive']['filename']
    loaded=load_prediction_archive(archive)
    assert len(loaded['y'])==1200
    verify_prediction_metrics(stored,archive)
    assert '_audit' in result  # persistence must not mutate caller data


def test_policy_freezes_before_any_test_inference(monkeypatch):
    from entropy_oracle import experiment
    events=[]
    real_builder=experiment.build_model
    def builder(*args,**kwargs):
        model=real_builder(*args,**kwargs)
        original=model.predict_proba
        def predict(X):
            # Final test differs from validation only in this crafted source.
            if np.any(X == 1):
                assert 'frozen' in events
                events.append('test')
            return original(X)
        model.predict_proba=predict
        return model
    from entropy_oracle.sources import SourceData
    x=np.zeros(500,dtype=np.int64);x[401:]=1
    data=SourceData(x=x,alphabet_size=2,oracle_probs=None,metadata={'source':'file'})
    monkeypatch.setattr(experiment,'build_model',builder)
    def progress(message):
        if 'policies frozen' in message:events.append('frozen')
    run_experiment(data=data,models=['marginal','markov1'],bootstrap=0,progress=progress)
    assert events==['frozen','test','test']


def test_external_alphabet_and_allocation_limits_fail_before_training():
    import pytest
    from entropy_oracle.sources import SourceData
    huge_alphabet=SourceData(np.zeros(500,dtype=np.int64),5000,None,{'source':'file'})
    with pytest.raises(ValueError,match='4096'):
        run_experiment(data=huge_alphabet,models=['marginal'])
    large_features=SourceData(np.zeros(100000,dtype=np.int64),256,None,{'source':'file'})
    with pytest.raises(ValueError,match='2 GiB'):
        run_experiment(data=large_features,models=['mlp'],window=128)


def test_fractional_targets_are_not_silently_quantized():
    import pytest
    with pytest.raises(ValueError,match='integer'):
        temporal_windows(np.arange(500)/10,32)
