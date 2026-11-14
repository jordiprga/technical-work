import math
from fractions import Fraction
import unittest
import extractor_lab as lab

class ToeplitzTests(unittest.TestCase):
    def test_exact_universality(self):
        for n in range(1,6):
            for m in range(1,4):
                with self.subTest(n=n,m=m):
                    self.assertTrue(lab.universal_check(n,m)['all_exact'])

    def test_linearity_and_rank_fibers(self):
        n,m=4,3
        for s in range(1 << (n+m-1)):
            h=lambda x:lab.toeplitz_hash(s,x,n,m)
            for a in range(1<<n):
                self.assertEqual(h(a)^h(7),h(a^7))
            kernel=[x for x in range(1<<n) if h(x)==0]
            self.assertEqual(len(kernel),2**(n-lab.toeplitz_rank(s,n,m)))

    def test_lhl_and_second_moment(self):
        result=lab.biased_source()
        self.assertLessEqual(float(result['average_tv']),result['lhl_min_entropy_bound'])
        self.assertLessEqual(result['average_squared_tv'],result['second_moment_collision_bound'])

    def test_repetition_is_not_joint_uniformity(self):
        result=lab.exact_reuse()
        self.assertLess(result['tv_seed_and_single'],Fraction(1,32))
        self.assertGreaterEqual(result['tv_seed_and_two_repeated_blocks'],Fraction(3,4))
        self.assertLessEqual(result['tv_seed_and_two_independent_blocks'],2*result['tv_seed_and_single'])

    def test_adaptive_kernel(self):
        n,m=6,2
        for s in range(1 << (n+m-1)):
            kernel=[x for x in range(1 << n) if lab.toeplitz_hash(s,x,n,m)==0]
            self.assertGreaterEqual(len(kernel),1 << (n-m))
            out=lab.output_distribution(s,{x:Fraction(1,len(kernel)) for x in kernel},n,m)
            self.assertEqual(out,{0:Fraction(1)})
            self.assertEqual(lab.tv_uniform(out,1 << m),Fraction(3,4))

    def test_dependency_sweep(self):
        results=[lab.correlated_blocks(rho=r) for r in [Fraction(0),Fraction(1,2),Fraction(1)]]
        self.assertEqual(len(set(r['tv_seed_and_each_marginal'] for r in results)),1)
        self.assertLess(results[0]['tv_seed_and_pair'],results[1]['tv_seed_and_pair'])
        self.assertLess(results[1]['tv_seed_and_pair'],results[2]['tv_seed_and_pair'])
        self.assertEqual(results[0]['conditional_min_entropy_X2_given_X1'],6)
        self.assertEqual(results[-1]['conditional_min_entropy_X2_given_X1'],0)

    def test_invalid_inputs(self):
        for args in [(-1,0,4,2),(0,16,4,2),(0,0,0,2)]:
            with self.assertRaises(ValueError): lab.toeplitz_hash(*args)
        with self.assertRaises(ValueError): lab.tv_uniform({0:Fraction(1,2)},2)

    def test_budget_cost_and_cap(self):
        r=lab.lifetime_budget(1024,768,10**12)
        self.assertTrue(math.isclose(r['per_block_lhl_error'],2**-129))
        self.assertEqual(lab.lifetime_budget(1,2,100)['total_tv_bound_capped'],1)

if __name__=='__main__': unittest.main(verbosity=2)
