# Test hardware and resource limits

[Back to overview](../README.md) · [Benchmark tables](benchmarks.md)

These are the machines and limits behind the retained measurements, not a
proposed production fleet. Most tests ran on one shared host, not dedicated
benchmark hardware. Host capacity is not the allocation given to each worker.

## Primary measurement host

| Component | Observed specification |
|---|---|
| CPU | AMD EPYC 7502P; 1 socket, 32 physical cores, 64 logical CPUs with SMT |
| Frequency | OS reports 1.5–2.5 GHz scaling range; actual test frequencies were not pinned |
| Memory | 128 GB-class host; OS-visible total 134,910,410,752 bytes (125.65 GiB); no swap |
| HDD payload storage | 2 × approximately 16 TB WDC WUH721816AL rotating drives; approximately 32 TB logical LVM volume, ext4 |
| NVMe workspace | 2 × approximately 3.84 TB SAMSUNG MZQLB3T8HALS-00007; data partitions in software RAID0, then LVM/ext4 |
| Software, follow-up inventory | Ubuntu 24.04.4 LTS; Linux 6.8.0-106-generic, x86_64; Python 3.12.3; Zstandard CLI 1.5.5 |

CPU identity and storage classes were recorded during the October 16 experiments.
Exact disk model names, memory total and software versions were checked again
on October 18. They are follow-up observations, not a complete historical
inventory taken at the start of every earlier run. The earlier receipt does not
establish the HDD stripe layout; do not assume a particular RAID speedup.

Machine addresses, hostnames, usernames, device serials, filesystem identifiers
and operational paths are intentionally excluded. Model names are generic
hardware specifications, not machine identifiers.

## Recorded worker limits

| Experiment / evidence | CPU-time ceiling | Memory ceiling | Additional conditions |
|---|---:|---:|---|
| Native replay launcher, initialization and capture | 16 logical-CPU equivalents | 32 GiB | No swap; initialization is separate from steady replay |
| Full-shard account encoder and metadata-pack group | 16 logical-CPU equivalents | 8 GiB | Eight formatter subprocesses share the group ceilings; not eight full native workers |
| Earlier native GET trial | 4 logical-CPU equivalents | 4 GiB | Affinity restricted to 4 logical CPUs; Rayon threads 4 |
| Final complete replay GET cohort | 8 logical-CPU equivalents | 8 GiB | Affinity restricted to 8 logical CPUs; offline worker |
| Final result/context packing | 8 logical-CPU equivalents | 8 GiB | Affinity restricted to 8 logical CPUs; offline worker |
| October 20 sustained GET and cold controls | 8 logical-CPU equivalents | 8 GiB | Four/eight small request handlers; 57 repeated targets; not full-Bank backfill workers |
| Persistent historical discovery/index sample | 2 logical-CPU equivalents | 4 GiB | Affinity restricted to 2 logical CPUs; observed peak RSS 326,828 KiB (319.17 MiB) |
| Matched database account-set trials | 4 logical-CPU equivalents | 8 GiB | Affinity restricted to 4 logical CPUs; ClickHouse used loopback batching |

These are cgroup ceilings, not measured CPU utilization, dedicated physical-core
reservations or RAM consumption. A 400% CPU quota allows up to four logical
CPUs' worth of execution time; it does not mean four physical cores. Separate
children inherit their test worker's cgroup limits. Ordinary small-test workers
used lower scheduler priority; the HDD sample also used reduced I/O weight.

SET combines stages measured in different small experiments. Its stage-day
projection is not a single continuous full-history run on the full host, nor a
validated number of workers per production server. Limits alone do not predict
fleet throughput. The SET table lists known source ceilings and explicitly marks
stages whose individual allocations were not retained in the numeric export.

## Storage, cache and contention

* Reported HDD GETs read compressed payload from rotating storage and include
  decompression. They are not NVMe payload-read measurements.
* Routing metadata is resident where stated; database comparisons resolve
  version pointers, not complete payloads or VM execution.
* Advised-cold uses OS cache advice. It does not flush physical-drive caches or
  guarantee that every kernel/filesystem metadata page is cold.
* Other services share the host and disks. CPU frequency, exact competing I/O,
  disk fullness and request placement were not held constant for every run.
* Small-sample filesystem occupancy and fragment placement do not demonstrate
  performance at a nearly full, hundreds-of-terabytes production archive.
* Complete replay GET excludes provider calls, inter-host transfer, public API
  serialization and arbitrary global routing. It is not a network SLA.
* The included tiny offline PoC runs on the reviewer's machine. Its time and
  compression ratio are not the retained research benchmark results.
* The later eviction-stress test evicted pages at arrivals, potentially disrupting
  other requests. Separate closed-batch controls evicted only after a batch ended.
  Neither establishes a universal cold-storage latency.

No multi-host hardware results are used to claim the local GET timings above.
Any later published transfer/fleet results need their own anonymized source and
destination specifications, traffic/cache conditions and worker allocations.

## Retained evidence identifiers

These hashes identify private operational receipts; the receipts themselves are
not copied because they contain operational identifiers and paths. Hashes are
provenance identifiers, not independent proof of the original measurements.

| Evidence | SHA256 |
|---|---|
| Original host resource receipt | `d86eb0928ad2ca15dd448d1bf6bb61fb86b2899a75cda0dfed252859e8c81e24` |
| Final replay GET launch limits | `413a414d63a83d1752434d55c8a675741547bf71569a15e81738eef0c9e8c0cd` |
| Final packing launch limits | `12422ab558872a44ad6c249d7150445c5c2b2848cc346d01bf4f7ef2494ba834` |
| Discovery/index launch limits | `55dd108a6225d067376d143b2a7d118ed932b4c9d9b48f4b1079aec780643a59` |
| Matched database batch launch limits | `eaf444e58b0906776efa6013bbd36f1e95ada5091ca1e3303936d7aee439da13` |
| ClickHouse trial launch limits | `9a915d8793c06153bf1c117425be92ccd3abb2d35dd046901d951d6ee7b73230` |
