"""Recompute audit totals; never infer a projection from unrelated sample timings."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AuditReportTests(unittest.TestCase):
    def setUp(self):
        self.audit = json.loads((ROOT / "data/audit-20261020.json").read_text())

    def test_disjoint_storage_substitutions_reconcile(self):
        storage = self.audit["storage"]
        self.assertIsNone(storage["native_correction_tb"])
        self.assertIsNone(storage["bootstrap_index_tb"])
        for row in storage["frame_candidates"]:
            self.assertAlmostEqual(row["saved_tb"], sum(row["disjoint_savings_tb"].values()))
            self.assertAlmostEqual(
                row["known_modeled_tb_excluding_C_I"] + row["saved_tb"], storage["baseline_tb"]
            )
            self.assertAlmostEqual(
                row["saved_percent_total"], row["saved_tb"] / storage["baseline_tb"] * 100
            )

    def test_load_accounting_and_mean_factors(self):
        get = self.audit["get"]
        self.assertEqual(
            get["verified_requests"], sum(row["verified_completed"] for row in get["load"])
        )
        for row in get["load"]:
            self.assertEqual(row["offered"], row["verified_completed"] + row["queue_rejections"])
            self.assertEqual(row["arrival_to_completion_seconds"]["n"], row["verified_completed"])
            self.assertAlmostEqual(
                sum(factor["ms"] for factor in row["mean_factors"].values()),
                row["arrival_to_completion_seconds"]["mean"] * 1000,
            )

    def test_latest_report_has_no_blanket_subsecond_or_fleet_claim(self):
        text = (ROOT / "docs/audit-update.md").read_text()
        for required in ("queue", "C + I", "stage-days", "not fleet throughput", "not an HDD"):
            self.assertIn(required, text)
        for path in ("README.md", "docs/benchmarks.md"):
            self.assertIn("audit-update.md", (ROOT / path).read_text())
