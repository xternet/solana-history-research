# Reproduction and evidence scope

[Back to overview](../README.md)

For the hardware and per-experiment CPU/RAM ceilings behind the retained
measurements, see [test environment](test-environment.md). These are shared-host
small-sample results, not production-server capacity measurements.

## Small offline example

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m history_poc --fixture fixtures/account_changes.json --output out/demo
```

Use a new output directory for each run. The program refuses to overwrite prior
results. Inspect `out/demo/manifest.json`, `manifest.json.sha256`, `index.zst` and
`payload.zst` afterward. The CLI reports existing-output and malformed-input
errors without a Python traceback.
The checksummed example format is v2; rebuild outputs from the earlier v1 demo
rather than bypassing the new manifest-digest checks.

The fixture was exported from a private local mainnet capture across two slots.
Its source, counts and cursor encoding are described in
[fixtures/README.md](../fixtures/README.md).

The program:

1. Validates coverage continuity and every input account's identity, cursor, length and checksum.
2. Stores one full anchor per account and patches that reference that anchor.
3. Zstandard-compresses the bounded payload and version index.
4. Writes durable payload, index and checksummed pending manifest files.
5. Resolves every recorded cursor and compares it with an independent fixture scan.
6. Publishes the verified manifest last and fsyncs the directory; the output's
   newly created parent directories are also synced through their parents.

Tests cover intermediate transaction boundaries, avoiding future-state leakage,
unknown accounts/slots/positions, manifest/payload/index corruption, failed
pre-publication verification and overwrite rejection. Synthetic brute-force tests
also cover deletion/recreation, automatic phases, repeated same-position writes,
missing slots and cursors before an account's first known state.
A missing capture is an error, never a current-state or zero-value fallback.
Noncontiguous slots require explicit `coverage.parent_slots` links to the preceding
captured slot. These are source assertions, not cryptographic proofs; an importer
must verify them against canonical input. Omitted slots remain unqueryable.
The example does not support merging independent coverage islands without a base.
Records with zero lamports remain explicit tombstones rather than unknown coverage.
The manifest digest detects accidental corruption; it is not a signature or a
trustless proof against an attacker replacing the manifest and digest together.
The file-protocol tests are not physical power-loss or production recovery tests.
The suite also sends real SIGKILL signals at seven write/rename/sync boundaries:
unpublished outputs are refused and published outputs are reverified.

**No SVM execution, snapshot restoration, provider calls or native Bank rebuild
takes place.** This example demonstrates the byte-history mechanism, not the
complete backend. Its readable compressed JSON directory is not the production
binary index. Its small timings and compression ratios are not annual forecasts.

## Regenerate the analytic report

```bash
python3 tools/render_report.py --check
```

`data/results.json` and `data/audit-20261020.json` are sanitized numeric evidence. The renderer
recomputes percentages and checks the committed Markdown for drift. To review a
changed report without overwriting it automatically:

```bash
python3 tools/render_report.py --patch
```

The emitted standard unified diff uses relative paths for `docs/benchmarks.md`
and the RPC/audit reports; it contains no machine-specific absolute paths.
**Rendering tables does not rerun the original benchmarks.**

## Portable codec and physical-frame experiment

```bash
python3 -m tools.benchmark --fixture fixtures/account_changes.json \
  --levels 1 3 6 9 15 --frame-bytes 0 1048576 4194304
```

This reruns actual compression/decompression on the included account records.
It reports payload plus serialized directory bytes, exact record round trips,
payload-codec timing and compressed read amplification. All records are equally
weighted; this is not the original transaction-weighted wire projection.
Timing excludes loading, directory packing, disk, network and execution.
Frame target zero means one record per frame; nonzero targets group adjacent-slot
records, without splitting an oversized record. The hard frame limit is 8MiB.

To use your own decoded blocks or other opaque inputs, provide a local manifest:

```json
{
  "records": [
    {"path": "block.bin", "slot": 100, "sha256": "REPLACE_WITH_FILE_SHA256"}
  ]
}
```

```bash
python3 -m tools.benchmark --manifest inputs/manifest.json
```

Paths must remain inside the manifest directory; checksums are mandatory.
Input is capped at 128MiB/100,000 records. Results go to standard output.
No download, external database, native runtime or annual extrapolation occurs.
See [research-tool provenance and differences](research-tools.md).

## Cross-archive pointer checks

```bash
python3 -m unittest discover -s tests -p test_version_index.py -v
```

The compact delta-varint codec splits blocks at shard boundaries and indexes
the complete slot/position/order cursor. Tests include a later request whose
latest version is still on the older shard, same-position block boundaries,
corruption, duplicate cursors and 5,000 seeded brute-force comparisons.
An unknown key raises an error; a cursor before the first supplied version is
unknown, not proven account absence. The example has no persistent global
directory, source-coverage verification or remote payload fetch.

## Original experiment layers

| Layer | Evidence represented here | What is not reproduced by the small example |
|---|---|---|
| Native replay/capture | Current-runtime samples and recorded query/results comparisons | Validator initialization, full epoch or multi-era history |
| Storage | Existing account/context/input/result model plus new compact indexes | Full-year account/index density |
| GET | Account discovery, full HDD payload reads and a separate fresh-VM cohort | Network, arbitrary global routing or a production SLA |
| SET | Composed stage costs and measured small index-building additions | Integrated multi-host throughput or worker density |
| Database selection | Same pointer dataset in immutable/RocksDB/ClickHouse trials | Matched cache budgets, universal ranking or complete payload latency |

The full research used larger local native captures that are not included here.
Source-artifact SHA256 identifiers preserve provenance, but do not make those
experiments independently rerunnable from this repository. A complete rerun needs
source snapshots/ledger, compatible runtime builds and separately qualified native
capture tooling. The repository does not claim to ship that production toolchain.
The immutable directory was RAM-resident, RocksDB's block cache was disabled,
and ClickHouse used loopback SQL. These are not equivalent production cache policies.

## Optional fixture extraction

If you already have compatible local native capture files:

```bash
python3 tools/extract_fixture.py CAPTURE_DIRECTORY \
  --slots FIRST_SLOT NEXT_SLOT --accounts 12 --output NEW_FIXTURE.json
```

This utility reads two cached slots and selects a small repeated-change account
cohort. It does not fetch provider data or execute the ledger. It refuses an
incompatible source layout, malformed records or conflicting contiguous state.

## Review checklist

* Separate measured values, projections and unmeasured fields.
* Include metadata/index bytes, not only compressed account payload.
* Compare whole requests from the same cohort; never add unrelated medians.
* Record the cache condition and number/size of returned accounts.
* Keep C/I, era/epoch coverage, source delivery and global routing gates visible.
* Validate recovery and corruption behavior before source retirement.
