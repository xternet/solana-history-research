# Research tools and reproducibility

[Overview](../README.md) · [Run commands](reproduction.md) · [Latest results](audit-update.md)

| Included tool | Work it actually performs | Limit |
|---|---|---|
| [Fixture extractor](../tools/extract_fixture.py) | Reads compatible native capture files, selects account versions and records source hashes | Requires locally supplied captures; does not replay or download |
| [History store](../history_poc/store.py) | Builds immutable anchors/patches, verifies every version, publishes a checksummed manifest last | Small account subset; not native execution |
| [Version-pointer codec](../history_poc/version_index.py) | Delta-varint predecessor lookup with shard-homogeneous blocks and full cursor ordering | In-memory experiment, not production routing |
| [Codec/frame benchmark](../tools/benchmark.py) | Recompresses supplied records, verifies bytes, counts both directories and payload | Bounded RAM codec work; no annual model or HDD latency |
| [Report renderer](../tools/render_report.py) | Generates tables from sanitized evidence and checks Markdown drift | Renders retained evidence; does not execute native benchmarks |
| [Regression tests](../tests/test_audit.py) | State, corruption and publication checks; adjacent test files cover pointers, arithmetic, privacy and links | Synthetic edge cases supplement a small real account fixture |

## Relationship to the original experiments

The pointer codec is a portable version of the original 32-row delta-varint
experiment. It fixes a demonstrated first-shard-only block assumption and uses
the full three-field cursor in the block directory. Its new checks do not
retroactively change the original database performance measurements.

The codec/frame tool ports the original Zstandard level and contiguous-frame
methods to explicit, checksummed local input manifests. It rotates level order,
verifies decoded bytes and includes compressed directories. It is not a verbatim
copy of the original operational harness: paths and artifact discovery have been
removed, inputs are opaque records rather than private CBOR/native captures, and
read amplification is record-weighted rather than transaction-weighted.
The bundled account fixture cannot reproduce the larger wire-sample ratio.

The original compression, anchor, wire and frame harness hashes are retained in
[the audit evidence](../data/audit-20261020.json). They identify the exact private
scripts used, not a claim that those scripts or their large inputs are bundled.
The existing baseline evidence likewise retains source artifact identifiers.

## Native replay reproduction remains separate

The larger experiments used version-matched Agave/SVM tooling, Rust native workers,
local snapshot/ledger captures and bounded Linux workers. This repository does
not include a qualified native capture patch or matching complete build recipe.
The audit found an unfinished writer lifecycle, incomplete fork/startup handling,
parent-ProgramData adapter work and a full-suite/source-pin mismatch.

Before publishing a native rerun recipe: pin all runtime commits and local
patches; document prerequisites and bounded launch arguments; verify a clean
build and the full suite at those pins; then run an independent fixture through
capture, encoding, retrieval and execution. A hash alone is not reproducibility.
Do not mistake the currently runnable byte-history and codec examples for that
end-to-end pipeline.

## Database comparison

The old thin-pointer comparison used 383,524 versions. Its immutable prototype
retained a RAM key directory; RocksDB disabled its block cache; ClickHouse used
loopback SQL. Their cache/transport conditions were not equivalent.
The immutable JSON directory also added size overhead. The results justify
further bounded comparisons, not a universal fastest/smallest database claim.
