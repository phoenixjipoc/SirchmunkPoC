"""Checks for retrieval scoring edge cases; no remote requests."""
import unittest
from analyze import hit,reciprocal,measure


class MetricChecks(unittest.TestCase):
    def test_unknown_before_positive_changes_bounds_not_known_hit(self):
        self.assertIsNone(hit([None,True],1))
        self.assertIs(hit([None,True],5),True)
        self.assertEqual(reciprocal([None,True]),(.5,1.0))

    def test_empty_and_error_stay_in_denominator(self):
        self.assertEqual(reciprocal([]),(0,0))
        self.assertEqual(measure([True,False,None]),dict(n=3,hits=1,unknown=1,lower_pct=33.33,upper_pct=66.67))

    def test_first_hit_at_cutoff(self):
        self.assertFalse(hit([False]*9+[True],5))
        self.assertTrue(hit([False]*9+[True],10))
        self.assertEqual(reciprocal([False]*9+[True]),(.1,.1))


if __name__=='__main__': unittest.main()
