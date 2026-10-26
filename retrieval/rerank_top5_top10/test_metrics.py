"""Check empty results and unresolved-support bounds."""
import unittest
from analyze import hit, rank, measure

class MetricTests(unittest.TestCase):
    def test_empty_is_a_miss(self):
        self.assertFalse(hit([],10))
        self.assertEqual(rank([]),0)

    def test_later_support_and_unknown_first(self):
        values=[None,False,True]
        self.assertIsNone(hit(values,1))
        self.assertTrue(hit(values,5))
        self.assertEqual(rank(values),3)
        self.assertEqual(rank(values,True),1)

    def test_unknown_is_never_dropped(self):
        result=measure([True,False,None])
        self.assertEqual(result,dict(n=3,hits=1,unknown=1,lower_pct=33.33,upper_pct=66.67))

if __name__=='__main__': unittest.main()
