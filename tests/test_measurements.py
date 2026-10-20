"""Portable measurements must verify actual compressed bytes."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from history_poc.zstd import Zstd
from tools.benchmark import load_manifest, measure


class MeasurementTests(unittest.TestCase):
    def test_every_record_roundtrips_and_directories_are_counted(self):
        records = [(10, b"a" * 100), (11, b"a" * 100), (13, b"b" * 100)]
        result = measure(records, levels=[1, 3], frame_bytes=[0, 1024])
        self.assertEqual(result["verified_record_roundtrips"], 12)
        for row in result["variants"]:
            self.assertEqual(row["record_count"], 3)
            self.assertEqual(row["total_bytes"], row["payload_bytes"] + row["directory_bytes"])
            self.assertEqual(row["frame_count"], 3 if row["frame_bytes"] == 0 else 2)
            self.assertGreaterEqual(row["compressed_read_amplification"], 1)

    def test_manifest_identity_and_containment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b"verified source bytes"
            (root / "source.bin").write_bytes(raw)
            item = {"path": "source.bin", "sha256": hashlib.sha256(raw).hexdigest(), "slot": 10}
            manifest = root / "inputs.json"
            manifest.write_text(json.dumps({"records": [item]}))
            self.assertEqual(load_manifest(manifest), [(10, raw)])
            for change in ({"sha256": "0" * 64}, {"path": "../outside.bin"}, {"slot": True}):
                manifest.write_text(json.dumps({"records": [item | change]}))
                with self.assertRaises(ValueError):
                    load_manifest(manifest)

    def test_invalid_configuration_is_not_silently_defaulted(self):
        for levels, sizes in (([0], [0]), ([3], [-1]), ([3], [9 * 1024**2]), ([], [0])):
            with self.assertRaises(ValueError):
                measure([(10, b"test")], levels, sizes)
        with self.assertRaises(ValueError):
            Zstd().compress(b"test", level=True)
