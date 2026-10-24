# Architecture & how it works

Planned production design, updated October 24, 2026; not the offline demo's current capabilities.

## 3.1. Historical backfill

- **Fetch:** Genesis, verified snapshots and free-access Old Faithful ledger inputs.
- **Reconstruct:** Our eight workers, both storage hosts and temporarily the head servers replay size-balanced ranges.
- **Store:** Workers write the same verified output directly to both complete EU/US copies.

<p align="center">
  <img src="solana-historical-backfill.drawio.png" alt="GET fetches inputs for workers on our cluster, heads and storage hosts; SET writes both full copies" />
  <br />
  <sub>Figure 1 — Historical backfill</sub>
</p>

<p align="center"><sub>Verified writes to both copies. Worker counts are indicative.</sub></p>

[Editable draw.io PNG](solana-historical-backfill.drawio.png)

## 3.2. Continuous sync & historical access

- **Capture:** TeraSwitch Frankfurt and Newark run independent non-voting heads after their temporary worker phase.
- **Append:** Reconcile finalized boundaries, verify updates and write sealed history directly to both copies.
- **Serve:** Dataforest Frankfurt is the primary; WebNX Ogden holds a full copy and provides limited standby/API reads.

<p align="center">
  <img src="solana-historical-live.drawio.png" alt="EU and US heads capture finalized updates; SET writes both full copies and user GET goes through the API or download service" />
  <br />
  <sub>Figure 2 — Continuous sync and historical access</sub>
</p>

<p align="center"><sub>Independent heads update both copies; GET uses the API or download service.</sub></p>

[Editable draw.io PNG](solana-historical-live.drawio.png)

## Diagram notes

Both heads share TeraSwitch, so geographic diversity is not head-provider diversity.
Standby is manual and rate-limited at the last verified checkpoint, not instant
or equal-throughput failover. Capture starts before the final backfill/live join.
Archive-to-archive transfers are for repair or catch-up, not the normal write path.

GET/SET labels describe logical access, not a specific network protocol. The API
and verification software run on the existing hosts, not an extra server.
The displayed PNGs retain their editable draw.io data and are used unchanged.

Earlier generated alternatives are retained:
[Backfill Mermaid](backfill-2027.mmd) · [SVG](backfill-2027.svg) · [PNG](backfill-2027.png);
[Continuous sync Mermaid](capture-access-2027.mmd) · [SVG](capture-access-2027.svg) · [PNG](capture-access-2027.png).
The original numbered draw.io exports are also preserved as design history.

[Technical design](../architecture.md) · [Capacity and access](../capacity-plan.md)
