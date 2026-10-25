# 2020-source ledger download PoC

On October 22, 2026, **four VPS with eight download streams** delivered
**771.95 GB of unique ledger data**. An independent readback verified all accepted
bytes; **23 complete epochs** also matched publisher checksums. The experiment
sampled epoch ranges covering 2020; the full assigned catalogue includes an
early-2021 tail, so it is not an exact calendar-year corpus.

Useful aggregate throughput was **41.88 MB/s while all eight streams were active**,
and **35.85 MB/s across the full resumed window** (approximately six hours).
Streams were capped at 8 MiB/s each. These are measured bounded-test rates, not
provider maximums or a guarantee of future free-source access.

The accepted set contains 384 ranges. Fourteen interrupted/cancelled prefixes
(13.48 GB) were verified against replacements and excluded from accepted totals.
An initial independent-audit closure race failed visibly; a supplemental readback
verified the missing tail and reconciled all final files. No paid source access
was used. Source/client failures and retries were retained, not removed from the
experiment history.

**This was downloading, not native transaction replay, state reconstruction or
database ingestion. Eight streams are not eight replay-worker benchmarks.**
Use byte-weighted jobs: equal epoch counts were badly imbalanced. No fleet
backfill ETA is established by this test.

The [sanitized numeric receipt](../data/fetch-20261022.json) is recomputed from
the original verified metrics/audit/closure receipts, with their SHA-256 IDs.
Operational host identifiers and paths are omitted. Original receipts and raw
ledger payloads are not shipped here; their hashes alone are not independent
reproduction. See the [2020 native validation plan](validation-plan.md) for the
separate correctness gate and the [test environment](test-environment.md) for
other experiments, whose hardware/worker limits must not be conflated with this one.
