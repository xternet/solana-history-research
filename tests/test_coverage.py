"""Missing slots must not silently authorize predecessor-state carryover."""

from copy import deepcopy
import hashlib
import json
import tempfile
from pathlib import Path
import unittest

from history_poc.store import CoverageError, History, build_history, validate_coverage
from test_audit import synthetic_fixture


class CoverageTests(unittest.TestCase):
    def test_missing_slot_requires_explicit_parent_link(self):
        fixture = synthetic_fixture()
        fixture["coverage"].pop("parent_slots", None)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            with self.assertRaisesRegex(ValueError, "parent"):
                build_history(fixture, target)
            self.assertFalse(target.exists())

    def test_parent_cannot_skip_an_existing_capture_or_point_elsewhere(self):
        base = synthetic_fixture()["coverage"]
        for parents in ({"12": 11}, {"12": 12}, {"12": True}, {"13": 10}, {"012": 10}):
            coverage = deepcopy(base)
            coverage["parent_slots"] = parents
            with self.subTest(parents=parents), self.assertRaises(ValueError):
                validate_coverage(coverage)
        coverage = deepcopy(base)
        coverage["slot_transaction_counts"]["11"] = 0
        coverage["parent_slots"] = {"12": 10}
        with self.assertRaises(ValueError):
            validate_coverage(coverage)

    def test_declared_skipped_slot_is_not_queryable(self):
        fixture = synthetic_fixture()
        fixture["coverage"]["parent_slots"] = {"12": 10}
        key = fixture["accounts"][1]["address"]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(fixture, target)
            reader = History(target)
            self.assertEqual(reader.get(key, 12, -2), reader.get(key, 10, 2))
            with self.assertRaises(CoverageError):
                reader.get(key, 11, 0)

    def test_reader_rejects_gap_even_if_manifest_checksum_is_recomputed(self):
        fixture = synthetic_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(fixture, target)
            manifest = json.loads((target / "manifest.json").read_text())
            del manifest["coverage"]["parent_slots"]
            raw = json.dumps(manifest).encode()
            (target / "manifest.json").write_bytes(raw)
            (target / "manifest.json.sha256").write_text(hashlib.sha256(raw).hexdigest())
            with self.assertRaisesRegex(ValueError, "parent"):
                History(target)
