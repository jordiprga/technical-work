import unittest
from dataclasses import replace
import math
import numpy as np
from qrng_sim import (Config, simulate, iid_phase_probability, diffusion_probability,
                      distribution_pdf, linear_roots, enumerate_feedback, metrics)

class ModelTests(unittest.TestCase):
    def test_probability_boundaries_and_symmetry(self):
        z = np.array([-2.,-1.,-.5,0,.5,1,2])
        p = iid_phase_probability(z,0)
        np.testing.assert_allclose(p+p[::-1],1,atol=1e-14)
        np.testing.assert_allclose(p[[0,1,3,5,6]],[1,1,.5,0,0])
        self.assertAlmostEqual(float(p[4]),1/3)

    def test_reproducibility_and_no_future_feedback(self):
        c = Config(n=8192,burn_in=0,window=64,update_period=64)
        a, b = simulate(c), simulate(c)
        np.testing.assert_array_equal(a['bits'],b['bits'])
        np.testing.assert_array_equal(a['threshold'][:64],np.zeros(64))
        expected = c.gain*(a['bits'][:64].mean()-.5)
        self.assertAlmostEqual(float(a['threshold'][64]),expected)

    def test_overlap_count_and_partial_block(self):
        c = Config(n=1003,burn_in=0,window=160,update_period=32)
        r = simulate(c)
        for stop,_,observed,_,_,_ in r['updates']:
            stop = int(stop)
            self.assertEqual(observed,float(r['bits'][stop-c.window:stop].mean()))
        self.assertEqual(len(r['bits']),1003)

    def test_rails_deadband_and_zero_gain(self):
        base = Config(n=8192,burn_in=0,window=1,update_period=1, gain=100, threshold_limit=.1)
        r = simulate(base)
        self.assertLessEqual(float(np.max(abs(r['threshold']))),.1)
        fixed = simulate(replace(base,gain=0,initial_threshold=.07))
        np.testing.assert_allclose(fixed['threshold'],.07)
        quiet = simulate(replace(base,window=8192,update_period=8192,deadband=.49))
        self.assertEqual(float(quiet['updates'][0,-1]),0)

    def test_arcsine_moments(self):
        c = Config(n=300000,burn_in=0,gaussian_sigma=0,gain=0)
        x = simulate(c)['analog']
        self.assertLess(abs(float(x.mean())),.005)
        self.assertLess(abs(float(np.mean(x*x))-.5),.005)

    def test_stationary_ar_noise_marginal(self):
        c = Config(n=200000,burn_in=0,gaussian_sigma=.3,gaussian_rho=.8,gain=0)
        x = simulate(c)['classical']
        self.assertLess(abs(float(x.var())-.09),.004)
        self.assertLess(abs(float(np.corrcoef(x[:-1],x[1:])[0,1])-.8),.01)

    def test_diffusion_probability_against_monte_carlo(self):
        rng = np.random.default_rng(73)
        delta = rng.normal(0,.4,400000)
        for mu,threshold in [(1.2,.3),(0.,.9),(-2.,-.4)]:
            actual = np.mean(np.cos(mu+delta)>threshold)
            model = float(diffusion_probability(threshold,0.,mu,.4))
            self.assertLess(abs(float(actual)-model),.004)

    def test_diffusion_uniform_limit(self):
        p = diffusion_probability(np.array([-.5,0,.5]),0,1.,7.)
        np.testing.assert_allclose(p,iid_phase_probability(np.array([-.5,0,.5]),0),atol=1e-9)

    def test_convolution_normalization_and_symmetry(self):
        x = np.linspace(-2.5,2.5,1001)
        p = distribution_pdf(x,sigma=.2,phase_nodes=2048)
        self.assertLess(abs(float(np.trapezoid(p,x))-1),1e-6)
        np.testing.assert_allclose(p,p[::-1],atol=1e-12)

    def test_linear_roots_and_delay_destabilization(self):
        self.assertAlmostEqual(float(linear_roots(.5,1.,1)[0]),.5)
        self.assertLess(max(abs(linear_roots(1.,1.,4))),1)
        self.assertGreater(max(abs(linear_roots(1.5,1.,4))),1)

    def test_exact_balanced_but_predictable_pairs(self):
        result = enumerate_feedback(n=12,gain=2.)
        self.assertAlmostEqual(result['probability_sum'],1.)
        self.assertEqual(result['paths_nonzero'],64)
        np.testing.assert_allclose(result['bit_marginals'],.5)
        self.assertAlmostEqual(result['joint_min_entropy'],6.)

    def test_finite_state_rates_and_dynamic_program(self):
        from finite_state_analysis import analyze
        for g in [.5,1.,2.]:
            r=analyze(g,max_length=16)
            enum=enumerate_feedback(n=16,gain=g)
            self.assertAlmostEqual(r['finite_lengths'][-1]['joint_min_entropy'],enum['joint_min_entropy'],places=12)
            self.assertLess(r['stationarity_residual_max'],1e-12)
            self.assertLessEqual(r['asymptotic_min_entropy_rate'],r['shannon_entropy_rate']+1e-12)
        self.assertAlmostEqual(analyze(2.)['asymptotic_min_entropy_rate'],.5)

    def test_short_data_and_theory_applicability(self):
        short=metrics(simulate(Config(n=2,burn_in=1)))
        self.assertEqual(short['diagnostics_status'],'insufficient_data_for_some_diagnostics')
        self.assertIsNone(short['context6_test_accuracy'])
        for kwargs in [{'offset':.1},{'target':.4},{'phase_mode':'diffusion'},
                       {'gaussian_rho':.5},{'deadband':.01},{'drift_amplitude':.1}]:
            m=metrics(simulate(Config(n=1024,burn_in=0,**kwargs)))
            self.assertFalse(m['linear_theory_applicable'])
            self.assertNotIn('threshold_variance_linear',m)

    def test_nonlinear_coexisting_cycles(self):
        from nonlinear_bifurcation import MeanMap
        m=MeanMap(nodes=2048)
        cycles=m.cycles(5.)
        self.assertEqual(len(cycles),2)
        self.assertFalse(cycles[0]['locally_stable'])
        self.assertTrue(cycles[1]['locally_stable'])
        self.assertLess(5*m.density(0.),2)
        for r in cycles:
            theta=r['amplitude']
            self.assertAlmostEqual(theta+5*(m.p(theta)-.5),-theta,places=10)

    def test_center_density_small_noise(self):
        from qrng_sim import center_density
        self.assertAlmostEqual(center_density(sigma=0),1/math.pi)
        self.assertAlmostEqual(center_density(sigma=1e-20),1/math.pi)
        self.assertAlmostEqual(center_density(sigma=.15),float(distribution_pdf([0.],sigma=.15)[0]),places=13)

    def test_invalid_parameter_rejection(self):
        for kwargs in [{'n':0},{'gaussian_rho':1},{'gain':-1}, {'gain':float('nan')},
                       {'burn_in':262144},{'window':0},{'threshold_limit':0}]:
            with self.assertRaises(ValueError):
                simulate(Config(**kwargs))

if __name__ == '__main__':
    unittest.main(verbosity=2)
