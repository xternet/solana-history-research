"""Regression cases for coverage, publication and independent state reconstruction."""

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from history_poc import store
from history_poc.store import CoverageError, History, address, build_history
from history_poc.zstd import MAX_FRAME_BYTES, Zstd

ROOT = Path(__file__).resolve().parents[1]


def record(key: bytes, lamports: int, data: bytes = b"") -> bytes:
    if lamports == 0:
        return key + bytes(57)
    return (
        key
        + lamports.to_bytes(8, "little")
        + bytes(8)
        + bytes([7]) * 32
        + bytes(1)
        + len(data).to_bytes(8, "little")
        + data
    )


def synthetic_fixture() -> dict:
    accounts = []
    timelines = [
        [
            (10, -2, 0, 1),
            (10, -1, 1, 2),
            (10, 0, 2, 3),
            (10, 0, 3, 4),
            (10, 1, 4, 0),
            (10, 2, 5, 5),
            (12, -1, 0, 6),
            (12, 2, 1, 7),
        ],
        [(10, -2, 0, 2), (10, 0, 1, 0), (12, 0, 0, 3)],
        [(12, 0, 0, 1), (12, 1, 1, 2)],
    ]
    for identity, timeline in enumerate(timelines, 1):
        key = bytes([identity]) * 32
        versions = []
        for slot, position, order, lamports in timeline:
            raw = record(key, lamports, bytes([lamports]) * (lamports + 1))
            versions.append(
                {
                    "slot": slot,
                    "position": position,
                    "order": order,
                    "raw_base64": base64.b64encode(raw).decode(),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
        accounts.append({"address": address(key), "versions": versions})
    return {
        "schema": "solana-account-history-fixture/v1",
        "coverage": {
            "first_slot": 10,
            "last_slot": 12,
            "slot_transaction_counts": {"10": 2, "12": 2},
            "parent_slots": {"12": 10},
        },
        "accounts": accounts,
    }


class AuditTests(unittest.TestCase):
    def test_manifest_coverage_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(synthetic_fixture(), target)
            path = target / "manifest.json"
            manifest = json.loads(path.read_bytes())
            manifest["coverage"]["slot_transaction_counts"]["11"] = 2
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "manifest checksum"):
                History(target)

    def test_missing_manifest_digest_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(synthetic_fixture(), target)
            (target / "manifest.json.sha256").unlink()
            with self.assertRaises(FileNotFoundError):
                History(target)

    def test_versions_and_coverage_are_validated_before_any_output(self):
        original = synthetic_fixture()
        mutations = [
            ("position", 99999),
            ("position", -3),
            ("slot", 11),
            ("order", -1),
            ("slot", True),
        ]
        for field, value in mutations:
            fixture = deepcopy(original)
            # One version avoids rejecting only because a later row becomes unsorted.
            fixture["accounts"] = [fixture["accounts"][0]]
            fixture["accounts"][0]["versions"] = [fixture["accounts"][0]["versions"][0]]
            fixture["accounts"][0]["versions"][0][field] = value
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "history"
                with self.assertRaises(ValueError):
                    build_history(fixture, target)
                self.assertFalse(target.exists())
        fixture = deepcopy(original)
        fixture["coverage"]["last_slot"] = 13
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            with self.assertRaises(ValueError):
                build_history(fixture, target)
            self.assertFalse(target.exists())

    def test_failed_verification_never_publishes_a_manifest(self):
        write = store.durable_write

        def corrupt_index(path, raw):
            write(path, raw)
            if path.name == "index.zst":
                altered = bytearray(raw)
                altered[len(altered) // 2] ^= 1
                path.write_bytes(altered)

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            with patch.object(store, "durable_write", side_effect=corrupt_index):
                with self.assertRaises(ValueError):
                    build_history(synthetic_fixture(), target)
            self.assertFalse((target / "manifest.json").exists())
            with self.assertRaises(FileNotFoundError):
                History(target)

    def test_fixture_parity_is_checked_before_manifest_publication(self):
        fixture = synthetic_fixture()
        get = History.get
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"

            def observed_get(reader, *args, **kwargs):
                self.assertFalse((target / "manifest.json").exists())
                calls.append(args)
                return get(reader, *args, **kwargs)

            with patch.object(History, "get", new=observed_get):
                build_history(fixture, target)
            self.assertEqual(len(calls), sum(len(a["versions"]) for a in fixture["accounts"]))
            self.assertTrue((target / "manifest.json").exists())

    def test_wrong_reconstruction_prevents_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            # Deliberately inject a decoder failure, not an expected test result.
            with patch.object(History, "get", return_value=b"wrong reconstruction"):
                with self.assertRaisesRegex(ValueError, "differs from original fixture"):
                    build_history(synthetic_fixture(), target)
            self.assertFalse((target / "manifest.json").exists())

    def test_parent_directory_is_synced(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            with patch.object(store, "sync_directory", wraps=store.sync_directory) as sync:
                build_history(synthetic_fixture(), target)
            self.assertIn(((target.parent,), {}), sync.call_args_list)
            self.assertIn(((target,), {}), sync.call_args_list)

    def test_nested_output_parents_are_synced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "nested" / "output" / "history"
            with patch.object(store, "sync_directory", wraps=store.sync_directory) as sync:
                build_history(synthetic_fixture(), target)
            for parent in (root, root / "nested", target.parent, target):
                self.assertIn(((parent,), {}), sync.call_args_list)

    def test_synthetic_edge_cases_match_a_brute_force_scan(self):
        fixture = synthetic_fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history"
            build_history(fixture, target)
            reader = History(target)
            for account in fixture["accounts"]:
                for slot in (10, 12):
                    for position in range(-2, 3):
                        for order in (0, 1, 2, 3, 4, 5, store.LAST_ORDER):
                            cursor = (slot, position, order)
                            prior = [
                                v
                                for v in account["versions"]
                                if (v["slot"], v["position"], v["order"]) <= cursor
                            ]
                            with self.subTest(key=account["address"], cursor=cursor):
                                if not prior:
                                    with self.assertRaises(CoverageError):
                                        reader.get(account["address"], *cursor)
                                else:
                                    latest = max(
                                        prior, key=lambda v: (v["slot"], v["position"], v["order"])
                                    )
                                    expected = base64.b64decode(latest["raw_base64"], validate=True)
                                    self.assertEqual(
                                        reader.get(account["address"], *cursor), expected
                                    )
                with self.assertRaises(CoverageError):
                    reader.get(account["address"], 11, 0)
            tombstone = reader.get(fixture["accounts"][0]["address"], 10, 1)
            self.assertEqual(tombstone[32:], bytes(57))

    def test_random_patch_roundtrips(self):
        rng = random.Random(0)
        for _ in range(10000):
            before = rng.randbytes(rng.randrange(256))
            offset = rng.randrange(len(before) + 1)
            after = (
                before[:offset]
                + rng.randbytes(rng.randrange(32))
                + before[offset + rng.randrange(32) :]
            )
            self.assertEqual(store.decode_patch(before, store.encode_patch(before, after)), after)

    def test_cli_overwrite_error_has_no_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "history_poc",
                    "--fixture",
                    "fixtures/account_changes.json",
                    "--output",
                    directory,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_report_patch_is_standard_and_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            for name in (
                "tools/render_report.py",
                "data/results.json",
                "data/rpc_methods.json",
                "data/audit-20261020.json",
                "docs/benchmarks.md",
                "docs/rpc-scope.md",
                "docs/audit-update.md",
            ):
                target = tree / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            report = tree / "docs/benchmarks.md"
            report.write_text(report.read_text() + "Deliberate test drift\n")
            result = subprocess.run(
                [sys.executable, "tools/render_report.py", "--patch"],
                cwd=tree,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(result.stdout.startswith("--- a/docs/benchmarks.md\n"))
            self.assertIn("+++ b/docs/benchmarks.md\n", result.stdout)
            self.assertIn("@@", result.stdout)
            self.assertNotIn("*** Begin Patch", result.stdout)
            self.assertNotIn(str(ROOT), result.stdout)
            self.assertNotIn(str(tree), result.stdout)

    def test_zstd_rejects_corrupt_truncated_concatenated_and_oversize_frames(self):
        codec = Zstd()
        packed = codec.compress(b"small bounded frame")
        for invalid in (b"invalid", packed[:-1], packed + packed, packed + b"garbage"):
            with self.subTest(size=len(invalid)), self.assertRaises(ValueError):
                codec.decompress(invalid)
        with self.assertRaises(ValueError):
            codec.compress(bytes(MAX_FRAME_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
