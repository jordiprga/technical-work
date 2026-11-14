import copy
from fractions import Fraction as F
import unittest
from fixed_matrix_analysis import exact_output
import interval_markov as im

class IntervalTests(unittest.TestCase):
    def test_enclosures_contain_rational_grid(self):
        box=(im.Interval(F(1,10),F(3,10)),im.Interval(F(1,5),F(2,5)))
        bounds=im.probability_enclosures(133,8,2,box)
        for a in [F(1,10),F(1,5),F(3,10)]:
            for b in [F(1,5),F(3,10),F(2,5)]:
                probabilities=exact_output(133,8,2,[F(1,2)]*2,[[1-a,a],[b,1-b]])
                for y,p in probabilities.items():self.assertLessEqual(bounds[y].lo,p);self.assertGreaterEqual(bounds[y].hi,p)

    def test_point_intervals_equal_exact_probabilities(self):
        a,b=F(1,7),F(2,9)
        bounds=im.probability_enclosures(133,8,2,(im.Interval(a,a),im.Interval(b,b)))
        exact=exact_output(133,8,2,[F(1,2)]*2,[[1-a,a],[b,1-b]])
        for y,p in exact.items():self.assertEqual((bounds[y].lo,bounds[y].hi),(p,p))

    def test_rejects_inexact_endpoints_and_altered_display(self):
        with self.assertRaises(TypeError):im.Interval(.1,.2)
        with self.assertRaises(TypeError):im.as_interval(.1)
        cert=im.solve(max_leaves=4)
        cert['min_entropy_lower_bits_approx']=100
        with self.assertRaises(ValueError):im.verify(cert)

    def test_certificate_replays_and_rejects_gaps(self):
        cert=im.solve(max_leaves=8)
        self.assertTrue(im.verify(cert)['verified'])
        corrupt=copy.deepcopy(cert);corrupt['leaves'].pop()
        with self.assertRaises(ValueError):im.verify(corrupt)
        corrupt=copy.deepcopy(cert);corrupt['leaves'][0]['upper']='0'
        with self.assertRaises(ValueError):im.verify(corrupt)

if __name__=='__main__':unittest.main(verbosity=2)
