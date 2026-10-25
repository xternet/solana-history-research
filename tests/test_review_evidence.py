"""Reconcile public evidence labels, budget arithmetic and demand scenarios."""
from decimal import Decimal
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReviewEvidenceTests(unittest.TestCase):
    def test_fetch_scope_and_rendered_totals(self):
        receipt = json.loads((ROOT / 'data/fetch-20261022.json').read_text())
        doc = (ROOT / 'docs/fetch-evidence.md').read_text()
        self.assertIn(f"{receipt['accepted_bytes']/1e9:.2f} GB", doc)
        self.assertIn(f"{len(receipt['publisher_verified_epochs'])} complete epochs", doc)
        self.assertIn(f"{receipt['all_streams_active_MB_s']:.2f} MB/s", doc)
        self.assertIn('no native replay', receipt['scope'])
        self.assertFalse(receipt['raw_receipts_public'])
        self.assertEqual(len(receipt['publisher_verified_epochs']),
                         len(set(receipt['publisher_verified_epochs'])))
        self.assertTrue(all(len(v) == 64 for v in receipt['source_pins'].values()))

    def test_supplier_math_and_release_sum(self):
        doc = (ROOT / 'docs/supplier-commitments.md').read_text()
        month, setup, fx = Decimal('1531.48'), Decimal('399'), Decimal('1.1193')
        for value in ((6*month+setup), (12*month+setup), (12*month*Decimal('.95'))):
            self.assertIn(f'{value:,.2f}', doc)
        for value in ((6*month+setup)*fx, (12*month+setup)*fx):
            self.assertIn(f'{value:,.2f}', doc)
        self.assertEqual(50724 + 14336 + 34940, 100000)
        self.assertEqual(21020 + 27228 + 22080 + 28672 + 1000, 100000)
        self.assertEqual(20000 + 100000 + 45000 + 10000, 175000)

    def test_demand_scenario_arithmetic(self):
        doc = (ROOT / 'docs/usage-plan.md').read_text()
        for reads, downloads, bulk in ((10000,1000,5),(100000,10000,25),(1000000,100000,100)):
            payload = (reads*20000 + downloads*5000000)*30/10**12
            self.assertIn(f'{payload:.3f} TB', doc)
            self.assertIn(f'{payload+bulk:.3f} TB', doc)
        sensitivity = (1000000*20000 + 100000*50000000)*30/10**12
        self.assertIn(f'{sensitivity:.1f} TB', doc)
        self.assertIn('not unique people or projects', doc)
