from hashlib import sha256
import json
import ipaddress
from pathlib import Path
import re
import struct
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree
import zlib

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOMAINS = {
    "github.com",
    "txlab.co",
    "solana.com",
    "www.apache.org",
    "www.w3.org",
    "app.diagrams.net",
    "draw.io",
}


def public_file_text(path: Path) -> str:
    if path.suffix != ".png":
        return path.read_text()
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Invalid PNG signature")
    position = 8
    kinds = []
    metadata = []
    while position < len(data):
        length = struct.unpack_from(">I", data, position)[0]
        end = position + 12 + length
        if end > len(data):
            raise ValueError("Truncated PNG chunk")
        kind = data[position + 4 : position + 8]
        if kind not in (b"IHDR", b"IDAT", b"IEND", b"tEXt"):
            raise ValueError("Diagram PNG contains unexpected metadata")
        checksum = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(data[position + 4 : end - 4]) != checksum:
            raise ValueError("Diagram PNG checksum differs")
        if kind == b"tEXt":
            key, separator, value = data[position + 8 : end - 4].partition(b"\0")
            if key != b"mxfile" or not separator:
                raise ValueError("Unexpected PNG text metadata")
            tree = ElementTree.fromstring(unquote(value.decode("utf-8")))
            pages = tree.findall("diagram")
            if (
                tree.tag != "mxfile"
                or not pages
                or any(page.find("mxGraphModel") is None for page in pages)
            ):
                raise ValueError("Unsupported draw.io metadata")
            # Browser versions resemble IPv4 literals; keep scanning all other metadata.
            if "agent" in tree.attrib:
                tree.set(
                    "agent",
                    re.sub(r"\bChrome/\d+(?:\.\d+)+", "Chrome/[version]", tree.get("agent")),
                )
            metadata.append(ElementTree.tostring(tree, encoding="unicode"))
        kinds.append(kind)
        position = end
        if kind == b"IEND":
            break
    if position != len(data) or kinds[0] != b"IHDR" or kinds[-1] != b"IEND":
        raise ValueError("Invalid PNG framing or trailing data")
    return "\n".join(metadata)


def privacy_issues(text: str) -> list[str]:
    issues = []
    urls = re.findall(r"https?://[^\s<>\"'`()]+", text)
    for url in urls:
        if urlsplit(url).hostname not in PUBLIC_DOMAINS:
            issues.append("unapproved URL host")
    # Inspect literal identifiers outside URLs too; URLs are checked above, not blindly exempted.
    residual = re.sub(r"https?://[^\s<>\"'`()]+", "", text)
    patterns = {
        "IP address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b|(?<!\w)(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4}(?!\w)",
        "absolute path": r"(?<![:/\w.])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+",
        "email": r"\b[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "secret": r"-----BEGIN (?:RSA )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, residual):
            issues.append(label)
    hosts = re.findall(
        r"\b(?:[A-Za-z0-9-]+\.)+(?:internal|local|lan|corp|invalid|dev|com|net|org|io|pl|co|cloud)\b",
        residual,
    )
    if any(host not in PUBLIC_DOMAINS for host in hosts):
        issues.append("hostname")
    return issues


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/results.json").read_text())

    def test_readme_has_no_internal_publication_workflow_notes(self):
        text = (ROOT / "README.md").read_text()
        self.assertIsNone(
            re.search(r"local review draft|owner approval|publication awaits", text, re.I)
        )

    def test_planned_hosts_distinguish_cores_threads_and_worker_capacity(self):
        text = (ROOT / "docs/architecture.md").read_text()
        self.assertEqual(text.count("EPYC 9354: 32C/64T"), 2)
        self.assertEqual(text.count("512 GB DDR5"), 2)
        for phrase in ("EPYC 7713: 64C/128T", "16C/16T total", "Own cluster: **8 workers**",
                       "Estimates, not benchmarks", "$920/month each",
                       "Newark price/stock require confirmation", "2x960 GB RAID1 boot",
                       "2x3.84 TB NVMe", "150 TB/month outgoing"):
            self.assertIn(phrase, text)
        for phrase in ("4–8", "6–8", "0–1", "$11,040", "≈$20,570", "$22,212",
                       "22–32", "no quoted NVMe scratch"):
            self.assertIn(phrase, text)

    def test_storage_sum_and_unknowns_are_explicit(self):
        data = self.data["storage"]
        self.assertAlmostEqual(
            sum(row["history_tb"] for row in data["components"]), data["modeled_history_tb"]
        )
        self.assertIsNone(data["native_correction_tb"])
        self.assertIsNone(data["bootstrap_index_tb"])
        self.assertFalse(data["complete_bound"])

    def test_storage_basis_and_latency_sample_sizes_are_preserved(self):
        self.assertTrue(all(row["basis"] for row in self.data["storage"]["components"]))
        self.assertTrue(all(row["count"] > 0 for row in self.data["get"]["requests"]))
        self.assertTrue(all(row["count"] > 0 for row in self.data["get"]["historical_queries"]))
        self.assertTrue(all("worker_limits" in row for row in self.data["set"]["factors"]))
        text = (ROOT / "docs/benchmarks.md").read_text()
        self.assertNotIn("Known total", text)
        self.assertIn("Modeled total", text)
        self.assertIn("Unmeasured allowance", text)

    def test_set_and_get_factor_percentages_have_consistent_totals(self):
        for name in ("set", "get"):
            section = self.data[name]
            self.assertAlmostEqual(
                sum(row["ms"] for row in section["factors"]), section["factor_total_ms"]
            )

    def test_stage_days_and_get_cohort_match_their_denominators(self):
        ingest = self.data["set"]
        for row in ingest["factors"]:
            self.assertAlmostEqual(
                row["ms"] * ingest["produced_blocks_model"] / (1000 * 86400), row["stage_days"]
            )
        get = self.data["get"]
        cohort = get["factor_cohort"]
        row = next(
            r
            for r in get["requests"]
            if r["condition"] == cohort["condition"] and r["concurrency"] == cohort["concurrency"]
        )
        self.assertEqual(row["count"], cohort["count"])
        self.assertEqual(row["mean_ms"], get["factor_total_ms"])

    def test_rpc_scope_counts_names_not_gap_categories(self):
        data = json.loads((ROOT / "data/rpc_methods.json").read_text())
        names = [name for group in data["groups"] for name in group["methods"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), data["count"])
        self.assertTrue(data["planned_not_implemented"])

    def test_public_files_have_no_infrastructure_identifiers(self):
        ignored = {".git", ".ruff_cache", ".pytest_cache", "__pycache__", "out"}
        for path in sorted(ROOT.rglob("*")):
            if path.is_file() and not ignored.intersection(path.relative_to(ROOT).parts):
                self.assertEqual(
                    privacy_issues(public_file_text(path)), [], str(path.relative_to(ROOT))
                )

    def test_architecture_preserves_original_owner_drawio_exports(self):
        for page, phase in ((2, "Backfill"), (1, "After backfill")):
            name = f"solana-historical-research-Page-{page}.drawio.png"
            png = ROOT / "docs/diagrams" / name
            source = ElementTree.fromstring(public_file_text(png))
            diagram = next(
                node for node in source.findall("diagram") if node.get("name") == f"Page-{page}"
            )
            labels = " ".join(cell.get("value", "") for cell in diagram.iter("mxCell"))
            for label in ("Historical Archive", "Active Archive", "Full-History Replica"):
                self.assertIn(label, labels)
            self.assertIn("24x workers" if page == 2 else "Head Capture", labels)
            if page == 2:
                self.assertIn("Old Faithful", labels)
            width, height = struct.unpack_from(">II", png.read_bytes(), 16)
            self.assertGreaterEqual(width, 400)
            self.assertGreaterEqual(height, 300)
        self.assertIn("Architecture & how it works", (ROOT / "docs/diagrams/README.md").read_text())

    def test_preserved_mermaid_exports_remain_source_bound(self):
        for name in ("backfill-2027", "capture-access-2027"):
            folder = ROOT / "docs/diagrams"
            source = (folder / (name + ".mmd")).read_bytes()
            svg = ElementTree.fromstring((folder / (name + ".svg")).read_bytes())
            self.assertEqual(svg.get("data-source-sha256"), sha256(source).hexdigest())
            self.assertIn("Dataforest", source.decode())
            self.assertIn("WebNX", source.decode())
            width, height = struct.unpack_from(">II", (folder / (name + ".png")).read_bytes(), 16)
            self.assertGreaterEqual(width, 400)
            self.assertGreaterEqual(height, 300)
            self.assertIn(name + ".svg", (folder / "README.md").read_text())

    def test_active_owner_drawio_exports_keep_read_write_labels(self):
        folder = ROOT / "docs/diagrams"
        for name, required in (
            ("solana-historical-backfill.drawio.png", ("Workers", "Ledger", "Snapshots")),
            ("solana-historical-live.drawio.png", ("Finalized", "Head", "Storage")),
        ):
            path = folder / name
            tree = ElementTree.fromstring(public_file_text(path))
            labels = " ".join(cell.get("value", "") for cell in tree.iter("mxCell"))
            for label in ("GET", "SET", *required):
                self.assertIn(label, labels)
            width, height = struct.unpack_from(">II", path.read_bytes(), 16)
            self.assertGreaterEqual(width, 700)
            self.assertGreaterEqual(height, 90)
            for doc in (ROOT / "README.md", ROOT / "docs/architecture.md", folder / "README.md"):
                self.assertIn(name, doc.read_text())
        for doc in (ROOT / "README.md", ROOT / "docs/architecture.md", folder / "README.md"):
            text = doc.read_text()
            self.assertIn("Worker counts are indicative", text)
            self.assertIn("API or download service", text)

    def test_new_capacity_plan_keeps_two_independent_full_copies(self):
        data = json.loads((ROOT / "data/capacity-20261024.json").read_text())
        for row in data["layouts"].values():
            self.assertEqual(row["raw_tb"], row["raid_groups"] * row["disks_per_group"] * row["disk_tb"])
            post = row["raid_groups"] * (row["disks_per_group"] - 2) * row["disk_tb"]
            self.assertEqual(row["post_parity_tb"], post)
            self.assertEqual(row["data_envelope_10pct_free_tb"], post * .9)
            self.assertGreater(row["data_envelope_10pct_free_tb"],
                               data["scenarios"]["stress"]["end2027_with_allowances_tb"])
        for row in data["scenarios"].values():
            known = data["history_through_2025_tb"] + data["reference_2025_tb"] * (
                row["rate_2026"] + row["rate_2027"])
            self.assertEqual(known, row["known_end2027_tb"])
            self.assertEqual(known * (1 + row["extra_fraction"]) + row["working_tb"],
                             row["end2027_with_allowances_tb"])

    def test_diagrams_show_storage_workers_and_direct_dual_writes(self):
        folder = ROOT / "docs/diagrams"
        backfill = (folder / "backfill-2027.mmd").read_text()
        self.assertIn('storage("Storage hosts")', backfill)
        for destination in ("eu", "us"):
            self.assertIn("workers --> " + destination, backfill)
        self.assertNotIn("eu --> us", backfill)
        capture = (folder / "capture-access-2027.mmd").read_text()
        for destination in ("eu", "us"):
            self.assertIn("verify --> " + destination, capture)
        self.assertNotIn("eu --> us", capture)

    def test_drawio_metadata_is_scanned_for_private_identifiers(self):
        original = (
            ROOT / "docs/diagrams/solana-historical-research-Page-1.drawio.png"
        ).read_bytes()
        position = 8
        while original[position + 4 : position + 8] != b"tEXt":
            position += 12 + struct.unpack_from(">I", original, position)[0]
        end = position + 12 + struct.unpack_from(">I", original, position)[0]
        value = str(ipaddress.IPv4Address(1))
        body = (
            b"mxfile\0"
            + f'<mxfile><diagram><mxGraphModel secret="{value}"/></diagram></mxfile>'.encode()
        )
        payload = b"tEXt" + body
        chunk = struct.pack(">I", len(body)) + payload + struct.pack(">I", zlib.crc32(payload))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.drawio.png"
            path.write_bytes(original[:position] + chunk + original[end:])
            self.assertIn("IP address", privacy_issues(public_file_text(path)))

    def test_diagrams_and_captions_are_centered_without_wrapping_prose(self):
        for doc in (
            ROOT / "README.md",
            ROOT / "docs/diagrams/README.md",
            ROOT / "docs/architecture.md",
        ):
            blocks = re.findall(
                r'<p align="center">\s*<img src="([^"]+)"[^>]*>\s*'
                r"<br\s*/>\s*<sub>([^<]+)</sub>\s*</p>",
                doc.read_text(),
            )
            self.assertEqual(len(blocks), 2, doc.name)
            for (source, caption), (name, title) in zip(
                blocks,
                (
                    ("solana-historical-backfill.drawio.png", "Figure 1 — Historical backfill"),
                    ("solana-historical-live.drawio.png", "Figure 2 — Continuous sync and historical access"),
                ),
            ):
                self.assertEqual(
                    Path(source).name, name
                )
                self.assertEqual(caption, title)

    def test_privacy_gate_detects_short_paths_emails_hosts_and_url_ips(self):
        # Construct synthetic negative cases, not real infrastructure identifiers.
        host = ".".join(("synthetic-worker", "invalid"))
        samples = [
            str(Path("/") / "alpha" / "beta"),
            "@".join(("reviewer", host)),
            host,
            str(ipaddress.IPv4Address(1)),
            str(ipaddress.IPv6Address(1)),
            "https://" + str(ipaddress.IPv4Address(1)) + "/report",
        ]
        for sample in samples:
            self.assertTrue(privacy_issues(sample), repr(sample))
        self.assertEqual(privacy_issues("https://github.com/xternet/svm-replay"), [])

    def test_hardware_and_limits_are_documented(self):
        text = (ROOT / "docs/test-environment.md").read_text()
        for item in (
            "AMD EPYC 7502P",
            "32 physical cores",
            "64 logical CPUs",
            "125.65 GiB",
            "WDC WUH721816AL",
            "SAMSUNG MZQLB3T8HALS-00007",
            "4 GiB",
            "8 GiB",
            "32 GiB",
            "not dedicated",
        ):
            self.assertIn(item, text)

    def test_documentation_entry_points_and_relative_links_exist(self):
        expected = [
            "architecture.md",
            "benchmarks.md",
            "data-contract.md",
            "reproduction.md",
            "rpc-scope.md",
            "test-environment.md",
        ]
        self.assertTrue(all((ROOT / "docs" / name).is_file() for name in expected))
        for path in [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]:
            contents = path.read_text()
            targets = re.findall(r"\]\(([^)]+)\)", contents)
            targets += re.findall(r'\b(?:src|href)="([^"]+)"', contents)
            for target in targets:
                if "://" in target or target.startswith("#"):
                    continue
                self.assertTrue(
                    (path.parent / target.split("#", 1)[0]).is_file(),
                    f"Broken link {target} in {path.name}",
                )

    def test_annual_baseline_and_seed_match_baseline_total(self):
        data = self.data["storage"]
        self.assertAlmostEqual(
            sum(row["baseline_tb"] for row in data["annual_baseline"])
            + data["one_time_baseline_seed_tb"],
            data["baseline_history_tb"],
        )


if __name__ == "__main__":
    unittest.main()
