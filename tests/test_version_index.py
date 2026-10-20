"""Compare shard-aware compact pointers with an independent linear scan."""

import random
import unittest

from history_poc.version_index import Version, VersionIndex, decode_block, encode_block


class VersionIndexTests(unittest.TestCase):
    def test_shard_transition_inside_one_block(self):
        rows = [Version(10, 0, 0, 7, 0, 0), Version(12, 0, 0, 8, 1, 1)]
        index = VersionIndex({"account": rows})
        self.assertEqual(index.lookup("account", (12, 0, 0)), rows[1])
        self.assertEqual(index.lookup("account", (11, 2, 0)), rows[0])
        self.assertEqual(len(index.blocks["account"]), 2)

    def test_order_at_block_boundary_and_old_shard_predecessor(self):
        rows = [Version(10, 0, order, order, 0, 0) for order in range(70)]
        index = VersionIndex({"account": rows})
        for order in range(70):
            self.assertEqual(index.lookup("account", (10, 0, order)), rows[order])
        self.assertEqual(index.lookup("account", (999, 0, 0)), rows[-1])
        self.assertIsNone(index.lookup("account", (9, 0, 0)))
        with self.assertRaises(KeyError):
            index.lookup("uncaptured", (10, 0, 0))

    def test_bruteforce_queries_and_block_codec(self):
        rng = random.Random(42)
        rows = []
        for slot in range(10, 25):
            for order in range(rng.randrange(1, 60)):
                rows.append(
                    Version(
                        slot, order // 4 - 2, order, rng.randrange(100000), order % 2, slot // 3
                    )
                )
        index = VersionIndex({"account": rows})
        for block in index.blocks["account"]:
            decoded = decode_block(block.raw, block.count, block.shard)
            self.assertEqual(encode_block(decoded), block.raw)
        for _ in range(5000):
            cursor = (rng.randrange(9, 28), rng.randrange(-2, 16), rng.randrange(70))
            prior = [row for row in rows if row.cursor <= cursor]
            expected = prior[-1] if prior else None
            self.assertEqual(index.lookup("account", cursor), expected)

    def test_duplicates_unsorted_invalid_and_corrupt_blocks_rejected(self):
        row = Version(10, 0, 0, 1, 0, 0)
        for rows in ([row, row], [Version(11, 0, 0, 2, 0, 0), row]):
            with self.assertRaises(ValueError):
                VersionIndex({"account": rows})
        with self.assertRaises(ValueError):
            VersionIndex({"account": [Version(10, -3, 0, 1, 0, 0)]})
        raw = encode_block([row])
        for invalid in (raw[:-1], raw + b"\0", b"\x80" * 11):
            with self.assertRaises(ValueError):
                decode_block(invalid, 1, 0)
        with self.assertRaises(ValueError):
            encode_block([row, Version(11, 0, 0, 2, 0, 1)])
