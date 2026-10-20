# Benchmarks and capacity model

[Back to overview](../README.md)

Evidence date: 2026-10-18. Research measurements and conditional projections; not production-qualified.

The tables below are generated from [data/results.json](../data/results.json). They are preserved research evidence, not timings from the included tiny example.

**Latest evidence:** [October 20 audit update](audit-update.md) adds sustained GET loads, fresh cold controls, compression candidates and capacity limits. The earlier latency table below is retained for comparison, not the current forecast.

See [test hardware and worker limits](test-environment.md) for the actual CPU, RAM, HDD/NVMe setup, shared-host conditions and per-experiment allocations.

## Earlier baseline summary

| Area | Retained result | Qualification |
|---|---:|---|
| Modeled compressed history | 333.635 TB + C + I | One logical copy, 2020–partial 2026; not measured full-history capture |
| 2025 reference-year storage | 88.878 TB + C | Activity-scaled scenario, not measured full-year capture |
| Compute-side ingestion | 1658.7 stage-days | Composed model with heterogeneous worker limits; not fleet throughput |
| Serial stages including source fetch | 1782.5 stage-days | Serial sum; pipelines/fleets may overlap stages |
| Fresh replay request p50 / p90 | 324.43 / 1775.86 ms | n=171; advised-cold, one caller; current-era sample |

C = unresolved native capture correction after existing allowances; I = unmeasured one-time full-bootstrap discovery-index seed. Neither is zero.

## STORAGE

Decimal TB; one compressed logical copy. Percentages use the modeled total, excluding C/I. Parity, replicas, scratch and private workspaces are extra.

| Component | TB/covered history (% modeled total) | TB/2025 (% modeled year total) | Basis |
|---|---:|---:|---|
| Genesis + one retained base snapshot | 0.114 (0.03%) | 0.000 (0.00%) | Reference snapshot |
| All account changes + deletions | 99.004 (29.67%) | 27.055 (30.44%) | Annual model from recent 100-slot density and historical activity proxies |
| Account-version indexes + routing | 35.545 (10.65%) | 9.713 (10.93%) | Annual model from recent 100-slot density and historical activity proxies |
| Bank context, sysvars + blockhash queue | 2.665 (0.80%) | 0.486 (0.55%) | Annual model from recent 100-slot density and historical activity proxies |
| Original transaction bytes | 96.083 (28.80%) | 23.892 (26.88%) | 832 sampled blocks across 2020–2026, with each year's sampled wire density and historical activity weights; only 10 sampled 2025 blocks |
| Signature locator + wire-frame directory | 9.788 (2.93%) | 2.231 (2.51%) | Small prototype + full-history projection |
| Original transaction results | 60.668 (18.18%) | 20.090 (22.60%) | 160-block extrapolation |
| Result offsets + block catalogue | 2.550 (0.76%) | 0.576 (0.65%) | Format allowance |
| Metadata-only native Bank checkpoints | 0.316 (0.09%) | 0.058 (0.06%) | Scenario |
| Replay-check receipts + state provenance | 0.087 (0.03%) | 0.016 (0.02%) | Format allowance |
| Automatic-write causes + phase/loader events | 1.000 (0.30%) | 0.182 (0.21%) | Unmeasured allowance |
| Versioned source, IDL, debug + toolchain artifacts | 0.550 (0.16%) | 0.100 (0.11%) | Scenario |
| Block envelopes, entries, rewards + proof fields | 15.058 (4.51%) | 2.149 (2.42%) | 160-block extrapolation |
| Address-to-transaction postings | 8.336 (2.50%) | 1.901 (2.14%) | 24055TX /363495postings;2048addresses/frame; recent bytes/TX projection, not historical density census |
| Program / mint / token-authority / delegate intervals | 0.657 (0.20%) | 0.150 (0.17%) | 3054new intervals +9552B net seed closures /24055TX; first-known cohort seed not repeated; full bootstrap index I unmeasured |
| Incremental shared address dictionary | 0.287 (0.09%) | 0.065 (0.07%) | 323new role-only IDs /24055TX,11305B; existing IDs reused; global uniqueness may differ |
| Additional query-index routing and framing | 0.928 (0.28%) | 0.212 (0.24%) | 10% allowance retained beyond local compressed frame directories; global fanout/compaction not benchmarked |
| Modeled total (excludes C, I) | 333.635 (100%) | 88.878 (100%) | Sum of conditional projections and allowances; not a measured bound |

The extra query indexes are built from 24,055 transactions and 363,495 address references across 20 recent slots. Recent bytes/TX are projected over historical activity; that is not a measured historical density distribution.

The initial cohort seed is 122,743 B, not a complete network seed. Its 9,552 B net encoded closure growth is counted. The initial seed is not charged again every sample window.

### Baseline by year

These rows preserve the pre-query-index baseline. They exclude the new index package and C/I; they are not the revised complete annual totals.

| Period | Baseline compressed TB |
|---|---:|
| 2020 | 4.325 |
| 2021 | 18.907 |
| 2022 | 41.090 |
| 2023 | 52.082 |
| 2024 | 56.349 |
| 2025 | 86.550 |
| 2026 partial | 64.010 |
| One-time retained base, separate | 0.114 |

## GET

### Complete replay requests

Original-input lookup, HDD account/context loading, fresh VM execution, verification and receipt. Metadata is resident. No provider/network/global routing. Cold is OS-advised, not a physical-drive cache flush; samples are small and current-era.

| Condition / callers | n | p10 ms | p50 ms | p90 ms | Sample max ms |
|---|---:|---:|---:|---:|---:|
| advised-cold / 1 | 171 | 248.47 | 324.43 | 1775.86 | 3211.11 |
| advised-cold / 4 | 171 | 273.31 | 690.28 | 2568.83 | 6071.47 |
| warm / 1 | 36 | 193.10 | 281.06 | 1320.98 | 2502.96 |

### Whole-request mean factors

Cohort: advised-cold, 1 caller, n=171. These component means share one denominator. Do not subtract or add percentile values from different request cohorts.

| Factor | Mean ms (% whole-request mean) |
|---|---:|
| signature wire | 9.72 (1.36%) |
| input assembly and identity | 143.88 (20.16%) |
| original results and expected state | 26.51 (3.72%) |
| native input serialize | 66.96 (9.38%) |
| fresh native process and output | 458.03 (64.19%) |
| original and full state verification | 0.14 (0.02%) |
| durable receipt | 6.18 (0.87%) |
| Other request overhead | 2.14 (0.30%) |
| Total mean | 713.56 (100%) |

### Historical discovery queries

Full compressed HDD payload and decode included; no VM execution, network or JSON response. Each row is a separate small query cohort, not a factor in the replay table above. With n≤6, show minimum/median/maximum, not tail percentiles.

| Query / condition | n | Returned accounts | Min ms | Median ms | Max ms |
|---|---:|---:|---:|---:|---:|
| Program accounts, dataSize165 / advised-cold | 3 | 51–1568 | 386.93 | 507.79 | 1176.44 |
| Program accounts, dataSize165 / warm | 3 | 51–1568 | 84.72 | 147.02 | 207.53 |
| Mint accounts / advised-cold | 6 | 23–607 | 18.33 | 79.27 | 216.43 |
| Mint accounts / warm | 6 | 23–607 | 9.60 | 29.96 | 69.75 |
| Token authority accounts / advised-cold | 3 | 14–26 | 16.96 | 18.54 | 21.94 |
| Token authority accounts / warm | 3 | 14–26 | 9.64 | 10.55 | 11.64 |
| Token delegate accounts / advised-cold | 3 | 1–1 | 0.83 | 1.17 | 1.20 |
| Token delegate accounts / warm | 3 | 1–1 | 0.27 | 0.31 | 0.38 |

Cohort top-20 token-ranking checks (n=3) took min/median/max 1139.74/4199.71/6798.44 ms, including a full candidate scan and Python reference decoder. Rankings are not universally sub-second. The cohort is not the full network.

## SET

Composed ms/produced block, not skipped slot. Percentages use the serial stage sum. Stage-days are projected wall time under heterogeneous source-worker limits, not CPU-days, homogeneous worker-days or calendar completion by a fleet. Unretained allocations stay explicit rather than being invented.

| Ingestion factor | ms/block (% serial stages) | Stage-days | Source worker limit (logical CPU quota / GiB) |
|---|---:|---:|---|
| Archive download | 24.68 (6.95%) | 123.80 | Not retained for this stage |
| CAR extraction and checks | 24.40 (6.87%) | 122.39 | 8 / 8 |
| Native input import | 15.17 (4.27%) | 76.10 | Not retained for this stage |
| Native execution and account capture | 140.99 (39.67%) | 707.17 | 16 / 32 |
| Account encoding, indexes and durability | 52.60 (14.80%) | 263.82 | 16 / 8 |
| Account metadata packaging | 4.45 (1.25%) | 22.32 | 16 / 8 |
| Transaction packaging and locator | 11.40 (3.21%) | 57.17 | Not retained for this stage |
| Native context packaging | 2.57 (0.72%) | 12.87 | Not retained for this stage |
| Original results/envelope encoding | 6.46 (1.82%) | 32.40 | 8 / 8 |
| Result indexes and grouped durability | 5.37 (1.51%) | 26.92 | 8 / 8 |
| Additional query-index update, encode/repack and durability | 67.30 (18.94%) | 337.55 | 2 / 4 |
| Total serial stages | 355.37 (100%) | 1782.50 | Heterogeneous ceilings; not one worker profile |

The added query-index sample used 0.971 s compute/repack and 0.179 s grouped durability. It includes conservative cohort-seed re-encoding and excludes repeated base58/oracle preparation because native resolved IDs already exist. This is not a fused production callback or integrated multi-host benchmark.

## Database index comparison

Matched account-version pointers; not complete payload reads or replay. Four account sets, three repeats per cache condition. ClickHouse used a single batched SQL query per set.

| Candidate | Cold n | Cold p50 ms | Cold p90 ms | Warm n | Primed warm p50 ms |
|---|---:|---:|---:|---:|---:|
| immutable-variable-index | 12 | 25.27 | 33.68 | 12 | 3.51 |
| rocksdb-zstd-thin-index | 12 | 93.57 | 113.19 | 12 | 8.42 |
| clickhouse-mergetree-batched | 12 | 56.11 | 60.77 | 12 | 29.19 |

Pointer lookup only; embedded immutable/RocksDB vs batched loopback ClickHouse; not full payload/VM or universal database ranking.

Cache/protocol conditions differ: the immutable key directory was RAM-resident, RocksDB's block cache was disabled, and ClickHouse used loopback SQL. The current JSON-directory prototype was not the smallest index on disk. These results do not establish a universal fastest/smallest database.

## Assumptions and remaining uncertainty

* Recent20-slot bytes/TX applied to published annual and historical activity counts; not historical index-density measurement.
* Initial cohort seed is NOT repeated every20slots. Its net encoded closure-byte increase IS counted.
* Full-network bootstrap discovery-index seed I remains unmeasured; modeled total excludes I, and native correction C remains separate.
* A10% global routing reserve is retained; actual global fanout, bloom filters, compaction and cache residency are not proved.
* Dictionary rate assumes recent within-sample unique-role discovery continues; true globally unique growth may differ.
* SET adds actual member-update, compact-posting, membership encode/repack and grouped durability. Base58/oracle source preparation is excluded because native resolved IDs already exist.
* SET is composed, not integrated benchmark: closure append/merge and streaming global ingestion remain implementation gates.
* Query data is a known captured-key cohort with resident metadata and HDD payload, no network/JSON/target execution; no full-network discovery or latency SLA.

Full native state, epoch/era behavior, bootstrap inventory, global routing, source access and production publication/merge semantics remain qualification gates. See [the data contract](data-contract.md).

## Evidence provenance

Hashes identify original local research artifacts, not a public attestation or a rerun of the experiments. The raw operational bundles are not included; the allowlisted numeric export contains no operational paths or credentials.

| Source artifact | SHA256 |
|---|---|
| tracker.json | `c78e00ec0e95276d3ebb91359eebc16a46796aa771245dd54d517cef963c3e5e` |
| final-model-v2.json | `335e5d5fe757f85e9b0d0d5624d36c3c5beec3091bde43a56b96e20b9ca21c4f` |
| measure-persistent.json | `b1cf239d657e973d01367981ddd8bbcfb92b93ca6819ca71ef587b1f5373021b` |
| native-audit.json | `9b34df6561f83e31d063cbbe0261cad7f6902a53f8bf72a3f6020fcebc0a8f4b` |
| reconciled.json | `ce3db3d4e41fcb63baefd9df3ce1ba396e27e7e0dbb5564baa0caeab05ed1136` |
| database-batch.json | `24080f7c628d5945fc42f098c247749d8bc57425f8ff829e907d9ec7ffaf4718` |
| database-bench.json | `3059e1b531fbad8af708b77649ed00104cf8959832f929dd2533ea13feebe226` |
| method-matrix-v2.json | `4f032122c81e8e2e019bb7b39b1dfb0e44394b5b59a9a72d976c9c3418923a7d` |
| measure.py | `43db8c1e9af1ab2fa39f5d578b74b70facab0957d9046520a041f13668bfd94e` |
| measure_persistent-launch.json | `55dd108a6225d067376d143b2a7d118ed932b4c9d9b48f4b1079aec780643a59` |
| pack-sample-v2-launch.json | `12422ab558872a44ad6c249d7150445c5c2b2848cc346d01bf4f7ef2494ba834` |
