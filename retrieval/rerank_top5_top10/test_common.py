"""Check corruption rejection and the unchanged tail requirement."""
import unittest
from common import ordered_ids, apply_order

class PermutationTests(unittest.TestCase):
    def test_rejects_invented_duplicate_missing_and_wrong_types(self):
        for ids in [['a','a'], ['a'], ['a','x'], 'ab', [1,2]]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                ordered_ids({'ordered_ids': ids}, ['a','b'])

    def test_rr5_keeps_tail_and_membership(self):
        old = list('abcdefghij')
        new = apply_order(old, list('edcba'), 5)
        self.assertEqual(new[5:], old[5:])
        self.assertEqual(set(new), set(old))

    def test_short_and_empty_lists(self):
        self.assertEqual(apply_order(['a','b'], ['b','a'], 5), ['b','a'])
        self.assertEqual(apply_order([], [], 10), [])

if __name__ == '__main__':
    unittest.main()
