# October 20 audit: current evidence

[Overview](../README.md) · [Earlier detailed tables](benchmarks.md) · [Numeric evidence](../data/audit-20261020.json) · [Reproduce](reproduction.md)

These results update the earlier research, not a production guarantee. The native cohort remains current-era; no full-history run is implied.

**Deployment update, October 24:** the [capacity plan](capacity-plan.md) now uses a full EU primary and full US replica, plus two geographic heads. The measurements below have not been rerun or relabelled as production results.

## STORAGE

One logical copy; same historical activity weights. Codec/frame substitutions change only measured, non-overlapping components. C + I remain unmeasured additions.

| Layout | Modeled TB, excluding C + I | Saving |
|---|---:|---:|
| Baseline | 333.635 | — |
| Zstd 6, unchanged frames | 327.126 | 6.509 TB (1.95%) |
| Zstd 9, unchanged frames | 325.286 | 8.349 TB (2.50%) |
| Zstd 15, unchanged frames | 323.296 | 10.339 TB (3.10%) |
| 4MiB wire frames, Zstd 3; other tested components Zstd 9 | 305.355 | 28.280 TB (8.48%) |
| 4MiB wire frames, Zstd 9; other tested components Zstd 9 | 300.828 | 32.807 TB (9.83%) |

Physical wire grouping does not change per-transaction account capture or require slot-prefix replay. Wire-frame savings replace the separate wire-codec saving; never add both. Directory/checksum bytes are included.

Wire sample: 832 blocks, 8,320 exact paired decode checks. The 2025 sample contains only 10 blocks. The 4MiB/Zstd9 candidate reads 2.48–5.05× more compressed wire bytes per sampled transaction, depending on year.

RAM decode/extract p50: 0.190 → 0.860 ms. This is not an HDD or whole-request measurement. Keep the conservative budget until integrated GET/SET tests qualify the candidate. Account-only queries do not fetch transaction wires.

### Capacity

Updated EU and selected US envelopes: 2 × (18 − 2) × 28 TB × 90% = **806.4 TB per copy**, using Dataforest and BudgetVM respectively. These are two complete copies, before filesystem overhead, not pooled storage. WebNX remains an unbudgeted fallback. The [2027 capacity plan](capacity-plan.md) replaces the former SX295/Artnet layout.

The recomputed central end-2027 scenario is about 525 TB per copy; the stress scenario is about 648 TB, including declared planning allowances. Neither is a measured full-history bound. Reforecast monthly and obtain approval before approaching 10% free capacity; no mid-year expansion server is assumed.

## GET

18,354 verified completed requests across 57 repeated real targets, not that many distinct transactions. Each run shares an 8-logical-CPU/8-GiB ceiling on the [shared test host](test-environment.md).

Arrival-to-completion includes queueing, HDD payload/decompression, input assembly, fresh native execution, verification and durable NVMe receipts. Metadata is resident. Caller network, public API overhead and global archive routing are excluded.

| Cache / readers | Offered req/s | Completed | Queue rejected | p50 s | p90 s |
|---|---:|---:|---:|---:|---:|
| Warm / 4 | 1 | 1,080 | 0 (0.0%) | 0.265 | 1.808 |
| Warm / 4 | 4 | 4,320 | 0 (0.0%) | 0.269 | 1.769 |
| Warm / 4 | 8 | 7,030 | 1,610 (18.6%) | 4.415 | 6.178 |
| Eviction stress / 4 | 1 | 600 | 0 (0.0%) | 1.917 | 4.708 |
| Eviction stress / 4 | 4 | 1,484 | 916 (38.2%) | 10.915 | 20.458 |
| Warm / 8 | 8 | 3,840 | 0 (0.0%) | 0.246 | 1.764 |

Warm four-reader runs lasted 18 minutes each; the eight-reader run lasted 8 minutes. Eviction stress lasted 10 minutes and evicted pages at each arrival, possibly disrupting in-flight requests: it is not normal cold-miss latency. OS cache advice does not flush physical-drive caches.

Fresh closed-batch controls evict only between completed batches:

| Readers | Verified requests | Service p50 s | Service p90 s |
|---|---:|---:|---:|
| 1 | 171 | 1.013 | 3.843 |
| 4 | 171 | 1.062 | 2.660 |

The old 0.324-second cold median was not stable. Reader counts are small request handlers, not full-Bank backfill workers. These cohorts do not establish a blanket subsecond historical-RPC SLA.

## SET

| Measure | Current interpretation |
|---|---|
| Compute-side model | 1658.7 stage-days |
| Serial model including fetch | 1782.5 stage-days |
| Worker allocations | Existing eight workers plus qualified spare storage/head compute; no fixed density promised |
| Parallel starts | Require verified range-start snapshots and matching boundary states |
| Next qualification | Source → replay/capture → compression/index → remote durable HDD write → replica acknowledgement |

The model combines different stage allocations and populations: **not fleet throughput** or interchangeable worker-days. Do not divide it by 24 to promise a calendar ETA. Measure initialization, peak RAM, scratch and integrated throughput on actual hosts. Two 40-GiB reservations do not fit a 64-GiB project allocation.

## Correctness and remaining gates

* Expanded native sample: 2,305/2,305 matches across 100 current-era slots; this is not historical runtime or epoch qualification.
* The local example now rejects unproven coverage gaps and demonstrates shard-aware version pointers. Parent assertions still require independently verified source data.
* Native capture remains research tooling: production streaming, fork identity, complete startup inventory and a clean lifecycle still need implementation.
* Qualify same-slot program upgrades, parent ProgramData use, epoch/reward transitions and the full native-runtime suite at matching source pins.
* Qualify the planned manual, rate-limited warm standby and failback; current recovery tests do not demonstrate hot failover or redundant head capture.
* Pointer database comparisons have different cache/protocol conditions and do not establish a universal minimum-size or fastest database.

The raw operational captures are not bundled. Evidence hashes identify retained receipts; they are not independently authenticated chain-state proofs.
