# Architecture & how it works

SVM Replay already supports historical transaction replay, simulation and
execution inspection. In our 1,198-transaction test, missing historical inputs
blocked 59.8% of replays using the Alchemy-backed data available to us, whose
coverage began in July 2025. This grant funds an independent, self-hosted backend
covering Solana from genesis to the latest finalized block, retaining complete
historical account state and execution context.

## Historical backfill

Temporary workers replay Old Faithful ledger data from genesis or verified
starting snapshots using version-matched runtimes. They capture per-transaction
account changes and required execution context, then compress, index and verify
the results. Two Hetzner archives split historical coverage; both copy verified
data and restart checkpoints to the independent Artnet replica.

<p align="center">
  <img src="solana-historical-research-Page-2.drawio.png" alt="Historical backfill architecture" />
  <br />
  <sub>Figure 1 — Historical backfill</sub>
</p>

[Open / download Figure 1](solana-historical-research-Page-2.drawio.png)

## Continuous sync and historical access

After catch-up, temporary workers are retired. Our non-voting Latitude.sh node
captures finalized changes; the Active Archive stores and verifies them before
setting the replica. The open API serves historical state and complete replay
inputs from both archives to SVM Replay, Txlab and external tools, without
third-party historical-state calls. Coverage checks, corruption detection,
monitoring and recovery protect continuity.

<p align="center">
  <img src="solana-historical-research-Page-1.drawio.png" alt="Continuous sync and historical access architecture" />
  <br />
  <sub>Figure 2 — Continuous sync and historical access</sub>
</p>

[Open / download Figure 2](solana-historical-research-Page-1.drawio.png)

## Diagram notes

Planned production architecture, not the repository's small offline demo. The
2025 boundary is illustrative; the actual storage cutoff follows verified
capacity. Requests can require versions from both shards. Verified ranges can
serve requests during backfill, and head capture begins before final catch-up.
Both PNGs retain editable draw.io source. [Technical design](../architecture.md).
