"""Synthetic selector tests; these are not historical replay results."""

from datetime import datetime, timezone
import unittest

from tools.sample_2020 import sample


class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"slot": q * 100 + i,
             "block_time": int(datetime(2020, 1 + 3 * q, 1, tzinfo=timezone.utc).timestamp())}
            for q in range(4) for i in range(40)
        ]

    def test_reproducible_order_independent_balanced(self):
        selected = sample(self.rows, "review-seed")
        self.assertEqual(selected, sample(list(reversed(self.rows)), "review-seed"))
        self.assertEqual(len(set(selected)), 100)
        self.assertEqual([sum(s // 100 == q for s in selected) for q in range(4)], [25]*4)
        self.assertNotEqual(selected, sample(self.rows, "another-seed"))

    def test_missing_quarter_duplicate_invalid_year_fail(self):
        for rows in (self.rows[:100], self.rows + [self.rows[0]],
                     [{"slot": 9999, "block_time": 0}] + self.rows):
            with self.assertRaises(ValueError):
                sample(rows, "review-seed")

    def test_invalid_identifiers_times_and_empty_seed_fail(self):
        for field, value in (("slot", True), ("slot", -1), ("block_time", None)):
            rows = [dict(r) for r in self.rows]
            rows[0][field] = value
            with self.assertRaises(ValueError):
                sample(rows, "review-seed")
        with self.assertRaises(ValueError):
            sample(self.rows, "")
