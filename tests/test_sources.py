import numpy as np
import pytest
from entropy_oracle.sources import SOURCE_NAMES, make_source

@pytest.mark.parametrize('name', SOURCE_NAMES)
def test_reproducible_valid_sources(name):
    a = make_source(name, n=300, seed=47)
    b = make_source(name, n=300, seed=47)
    np.testing.assert_array_equal(a.x,b.x)
    assert a.x.shape == (300,)
    assert np.issubdtype(a.x.dtype,np.integer)
    assert a.x.min()>=0 and a.x.max()<a.alphabet_size
    if a.oracle_probs is not None:
        assert a.oracle_probs.shape == (300,a.alphabet_size)
        assert np.all(a.oracle_probs>=0)
        np.testing.assert_allclose(a.oracle_probs.sum(axis=1),1,atol=1e-12)


def test_nonlinear_observed_past_oracle():
    a = make_source('nonlinear',n=2000,seed=4,noise=.02)
    u = a.x//2
    v = np.where(u[17-13:-13],u[17-9:-9],u[:-17])
    p1 = np.where(v,.98,.02)
    np.testing.assert_allclose(a.oracle_probs[17:,1],p1/2)
    np.testing.assert_allclose(a.oracle_probs[17:,3],p1/2)
    np.testing.assert_allclose(a.oracle_probs[17:].max(axis=1),.49)
    np.testing.assert_allclose(a.oracle_probs[:17],.25)


def test_uniform_lag_source_is_predictable():
    a = make_source('long_range',n=50000,seed=1,lag=16,noise=.03)
    assert abs(a.x.mean()-.5)<.05
    assert np.mean(a.x[16:]==a.x[:-16])>.95
    np.testing.assert_allclose(a.oracle_probs[16:,1],np.where(a.x[:-16],.97,.03))


def test_hmm_oracle_filters_observations_not_hidden_state():
    a = make_source('hmm',n=100,seed=3,stay=.8,emission_noise=.2)
    state = np.array([.5,.5]); trans=np.array([[.8,.2],[.2,.8]])
    emit = np.array([[.8,.2],[.2,.8]])
    for t in range(100):
        np.testing.assert_allclose(a.oracle_probs[t],state@emit)
        state*=emit[:,a.x[t]]; state/=state.sum(); state=state@trans


def test_ar1_has_no_latent_oracle_mislabeled_as_observed():
    a=make_source('ar1',n=500,seed=0)
    assert a.oracle_probs is None
    assert 'privileged_latent_success_upper_bound_numeric' in a.metadata


def test_arcsine_probability_mass_integration():
    a=make_source('arcsine',n=100,seed=0)
    assert a.metadata['quadrature_256_vs_512_max_error']<1e-8
    np.testing.assert_allclose(a.oracle_probs[0],a.oracle_probs[0,::-1],atol=1e-12)

@pytest.mark.parametrize('kwargs',[dict(n=0),dict(n=10,noise=1.2),dict(n=10,lags=[1,1,2])])
def test_invalid_nonlinear_parameters(kwargs):
    with pytest.raises(ValueError):
        make_source('nonlinear',**kwargs)
