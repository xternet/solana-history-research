"""Independent input scans are the reference, not stored-index output."""

import base64
import json
from pathlib import Path
import tempfile
import unittest

from history_poc.store import CoverageError, History, build_history, decode_patch, encode_patch

ROOT = Path(__file__).resolve().parents[1]


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixtures/account_changes.json").read_text())

    def test_patch_reference_cases(self):
        for before, after in [
            (b"abc", b"abc"),
            (b"abc", b"axc"),
            (b"ab", b"abcdef"),
            (b"abcdef", b"ab"),
            (b"", b"new"),
            (b"old", b""),
        ]:
            self.assertEqual(decode_patch(before, encode_patch(before, after)), after)

    def test_every_real_fixture_version_matches_independent_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(self.fixture, target)
            reader = History(target)
            for account in self.fixture["accounts"]:
                for event in account["versions"]:
                    cursor = (event["slot"], event["position"], event["order"])
                    candidates = [
                        row
                        for row in account["versions"]
                        if (row["slot"], row["position"], row["order"]) <= cursor
                    ]
                    expected = base64.b64decode(candidates[-1]["raw_base64"], validate=True)
                    self.assertEqual(reader.get(account["address"], *cursor), expected)

    def test_unknown_keys_and_outside_coverage_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(self.fixture, target)
            reader = History(target)
            account = self.fixture["accounts"][0]
            first = account["versions"][0]
            with self.assertRaises(CoverageError):
                reader.get("uncaptured-address", first["slot"], first["position"])
            with self.assertRaises(CoverageError):
                reader.get(account["address"], first["slot"] - 1, 0)
            with self.assertRaises(CoverageError):
                reader.get(account["address"], self.fixture["coverage"]["last_slot"] + 1, 0)

    def test_corruption_and_overwrite_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(self.fixture, target)
            with self.assertRaises(FileExistsError):
                build_history(self.fixture, target)
            payload = target / "payload.zst"
            data = bytearray(payload.read_bytes())
            data[len(data) // 2] ^= 1
            payload.write_bytes(data)
            with self.assertRaises(ValueError):
                History(target)

    def test_all_boundaries_include_no_future_account_state(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(self.fixture, target)
            reader = History(target)
            boundaries = sorted(
                {
                    (row["slot"], row["position"])
                    for account in self.fixture["accounts"]
                    for row in account["versions"]
                }
            )
            for slot, position in boundaries:
                for account in self.fixture["accounts"]:
                    prior = [
                        row
                        for row in account["versions"]
                        if (row["slot"], row["position"]) <= (slot, position)
                    ]
                    expected = base64.b64decode(prior[-1]["raw_base64"], validate=True)
                    self.assertEqual(reader.get(account["address"], slot, position), expected)

    def test_index_corruption_and_invalid_transaction_position_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(self.fixture, target)
            reader = History(target)
            with self.assertRaises(CoverageError):
                reader.get(
                    self.fixture["accounts"][0]["address"],
                    self.fixture["coverage"]["first_slot"],
                    1000000,
                )
            index = target / "index.zst"
            raw = bytearray(index.read_bytes())
            raw[len(raw) // 2] ^= 1
            index.write_bytes(raw)
            with self.assertRaises(ValueError):
                History(target)


if __name__ == "__main__":
    unittest.main()
