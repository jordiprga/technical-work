from fractions import Fraction
import unittest
import fixed_matrix_analysis as fixed
from extractor_lab import output_distribution,bernoulli_distribution

class FixedMatrixTests(unittest.TestCase):
    def test_transfer_matches_full_enumeration(self):
        initial=[Fraction(2,3),Fraction(1,3)]
        transition=[[Fraction(4,5),Fraction(1,5)],[Fraction(1,4),Fraction(3,4)]]
        for n,m in [(3,2),(5,3)]:
            for seed in range(1<<(n+m-1)):
                self.assertEqual(fixed.exact_output(seed,n,m,initial,transition),fixed.enumerate_output(seed,n,m,initial,transition))

    def test_iid_matches_direct_distribution(self):
        n,m,seed=7,3,123
        p=Fraction(3,5)
        expected=output_distribution(seed,bernoulli_distribution(n,p),n,m)
        expected={y:expected.get(y,Fraction()) for y in range(1<<m)}
        self.assertEqual(fixed.exact_output(seed,n,m,[1-p,p],[[1-p,p]]*2),expected)

    def test_max_path_fair_and_persistent(self):
        for n in [1,2,8]:
            self.assertEqual(fixed.maximum_path_probability(n,[Fraction(1,2)]*2,[[Fraction(1,2)]*2]*2),Fraction(1,1<<n))
            transition=[[Fraction(9,10),Fraction(1,10)],[Fraction(1,10),Fraction(9,10)]]
            self.assertEqual(fixed.maximum_path_probability(n,[Fraction(1,2)]*2,transition),Fraction(1,2)*Fraction(9,10)**(n-1))

    def test_nonidentical_independent_bias_bounds(self):
        n,m,seed=5,3,73
        probabilities=[Fraction(1,3),Fraction(2,5),Fraction(1,2),Fraction(3,5),Fraction(3,4)]
        from itertools import product
        from extractor_lab import toeplitz_hash,tv_uniform
        dist={y:Fraction() for y in range(1<<m)}
        for bits in product([0,1],repeat=n):
            probability=Fraction(1)
            for bit,p in zip(bits,probabilities):probability*=p if bit else 1-p
            dist[toeplitz_hash(seed,sum(b<<j for j,b in enumerate(bits)),n,m)]+=probability
        bounds=fixed.independent_bias_bounds(seed,n,m,[abs(1-2*p) for p in probabilities])
        self.assertLessEqual(max(dist.values()),bounds['maximum_probability_upper_bound'])
        self.assertLessEqual(tv_uniform(dist,1<<m)**2,bounds['tv_squared_upper_bound'])

    def test_iid_max_probability_bound_is_tight(self):
        n,m,seed=7,3,123
        p=Fraction(3,5)
        dist=fixed.exact_output(seed,n,m,[1-p,p],[[1-p,p]]*2)
        bounds=fixed.independent_bias_bounds(seed,n,m,[abs(1-2*p)]*n)
        self.assertEqual(max(dist.values()),bounds['maximum_probability_upper_bound'])

    def test_zero_map_and_bad_model(self):
        dist=fixed.exact_output(0,4,2,[Fraction(1,2)]*2,[[Fraction(1,2)]*2]*2)
        self.assertEqual(dist,{0:Fraction(1),1:Fraction(0),2:Fraction(0),3:Fraction(0)})
        with self.assertRaises(ValueError):fixed.markov_walsh(0,3,[Fraction(1,2)]*2,[[Fraction(1),Fraction(1)]]*2)

if __name__=='__main__':unittest.main(verbosity=2)
