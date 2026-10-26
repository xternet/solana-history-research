"""Reconcile public evidence labels, budget arithmetic and demand scenarios."""
from decimal import Decimal, ROUND_CEILING
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
        pricing = json.loads((ROOT / 'data/planning-pricing-20261026.json').read_text())
        month = Decimal(pricing['dataforest_monthly_eur'])
        setup = Decimal(pricing['dataforest_setup_eur'])
        fx = Decimal(pricing['eur_usd'])
        for value in ((6*month+setup), (12*month+setup), (12*month*Decimal('.95'))):
            self.assertIn(f'{value:,.2f}', doc)
        for value in ((6*month+setup)*fx, (12*month+setup)*fx):
            self.assertIn(f'{value:,.2f}', doc)
        eu = int((((12*month+setup)*fx)/10).to_integral_value(rounding=ROUND_CEILING)*10)
        other_hosting = pricing['budgetvm_annual_usd'] + pricing['dual_head_annual_usd']
        hosting = eu + other_hosting
        july = int((6*month*fx).to_integral_value(rounding=ROUND_CEILING)) + other_hosting//2
        initial = hosting - july + pricing['m2_transfers_usd']
        acceptance = pricing['m2_total_usd'] - hosting - pricing['m2_transfers_usd']
        for amount in (eu, initial, acceptance, july):
            self.assertIn(f'${amount:,}', doc)
        self.assertIn(pricing['as_of'], doc)
        self.assertEqual(initial + acceptance + july, pricing['m2_total_usd'])
        self.assertEqual(hosting + acceptance + pricing['m2_transfers_usd'], pricing['m2_total_usd'])
        self.assertEqual(pricing['m1_total_usd'] + pricing['m2_total_usd']
                         + pricing['maintenance_usd'] + pricing['adoption_usd'],
                         pricing['grant_total_usd'])

    def test_demand_scenario_arithmetic(self):
        doc = (ROOT / 'docs/usage-plan.md').read_text()
        for reads, downloads, bulk in ((10000,1000,5),(100000,10000,25),(1000000,100000,100)):
            payload = (reads*20000 + downloads*5000000)*30/10**12
            self.assertIn(f'{payload:.3f} TB', doc)
            self.assertIn(f'{payload+bulk:.3f} TB', doc)
        sensitivity = (1000000*20000 + 100000*50000000)*30/10**12
        self.assertIn(f'{sensitivity:.1f} TB', doc)
        self.assertIn('not unique people or projects', doc)
