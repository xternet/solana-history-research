# Capacity through December 2027

Planning scenarios, not measured full-history storage or upper bounds.
The [baseline model](benchmarks.md#storage) includes account/version/query
indexes. Do not add those indexes again.

## Calendar forecast

Reconstructing the annual components gives **268.251 TB through 2025** and a
2025 reference rate of **88.878 TB/year**, including the query indexes.
Start from that calendar boundary rather than assigning an unverified date to
the older partial-2026 total.

| Scenario | Known modeled data at end 2027 | Including planning allowances |
|---|---:|---:|
| Both later years at the 2025 rate | 446.007 TB | 500.608 TB |
| 2026 flat; 2027 adds 25% to the reference rate | 468.227 TB | 525.049 TB |
| 2026 adds 25%; 2027 adds a further 50% | 545.995 TB | 647.894 TB |

The first two add 10% for unmeasured native/bootstrap, filesystem and checkpoint
effects, plus 10 TB working space. The stress case adds 15% plus 20 TB.
These allowances do not establish bounds on C + I. New compression candidates
are not credited before integrated qualification.

## Two complete storage sites

| Site | Raw HDD | Double-parity layout | After parity | Data envelope with 10% free |
|---|---:|---|---:|---:|
| EU primary: Dataforest, Frankfurt | 36x28 TB = 1,008 TB | 2x18-drive RAIDZ2/RAID6 groups | 896 TB | 806.4 TB |
| US replica: BudgetVM, Detroit | 36x28 TB = 1,008 TB | 2x18-drive RAIDZ2 groups | 896 TB | 806.4 TB |

These are **two full copies**, not 1,612.8 TB available to one copy. Filesystem
overhead further reduces each envelope. The group layouts are planning choices,
not deployed arrays or supplier guarantees. ZFS HBA/passthrough support, rebuild
behaviour and exact drive geometry must be confirmed before ordering.

At the **525.049 TB** central year-end scenario, the envelopes leave approximately
281 TB at each site. Even the **647.894 TB** stress scenario leaves about
159 TB at each site, before any filesystem adjustment. No mid-2027 additional
storage server is included in the updated plan. Reforecast monthly and arrange
approval/funding before approaching 10% free post-parity capacity.

The [recomputed October 24 data](../data/capacity-20261024.json) retains annual
components, explicit scenario assumptions, disk arithmetic and input hashes.
It replaces the earlier SX295/Artnet expansion plan, not the retained measurements.

## Compute reuse and timeline

| Stage | Target period | Resources |
|---|---|---|
| M1: genesis–2020 beta | By November 30, 2026; 2–3 months | Existing eight-worker cluster and temporary storage; self-funded R&D already underway |
| M2: full history and dual capture | January–March 2027 | Same workers plus spare storage/head compute; transition heads before final catch-up |
| Operations and compatibility upgrades | April–December 2027 | Two full storage sites and two heads; temporary worker allocations end |

All four rented machines are funded once for January–December 2027. Planned
heads are TeraSwitch Frankfurt and Newark; both share a provider. Spare CPU/RAM,
scratch, source access, network and sustained HDD writes limit useful concurrency.
The BudgetVM dual-Xeon storage host is not equivalent to the Dataforest EPYC host;
no fixed eight-worker allowance is assumed for every rented machine.

The current planning range is 4–8 replay workers per head, 6–8 on Dataforest and
4–5 on BudgetVM, plus our eight workers: 26–37 allocations, not equal-speed
throughput units. WebNX is an unbudgeted fallback, with no scheduled replay
workers because it has no quoted NVMe scratch. See the
[host table](architecture.md#planned-machines).

The [planned-machine table](architecture.md#planned-machines) specifies the two
EPYC 9354 heads with 512 GB RAM and separate accounts/ledger NVMe drives.
Each head is budgeted at $920/month; the matching Newark price and availability
are not yet confirmed. A 9354 has 32 physical cores / 64 threads, not 64 cores.

## Traffic and access

| Site | Included monthly outgoing | Planned handling |
|---|---:|---|
| Dataforest | 250 TB; incoming free | Paid EU exports cover excess outgoing delivery; quote currently specifies €1/additional TB |
| BudgetVM | Selected 300 TB tier; incoming unlimited | Reserve operations first; cap/queue free API and shared downloads before allowance exhaustion |

These are per-server monthly volumes, not guaranteed throughput or shared quotas.
Initial replica seeding, continuous capture and repairs consume traffic too. Queue
large jobs, account for retries and reserve a safety margin; a provider-approved
hard cutoff/no-overage agreement is required before relying on a strict bill cap.
Port speed alone does not establish end-to-end transfer speed.
BudgetVM's workload/distribution permission and overage terms must be confirmed;
the checkout label does not waive its acceptable-use policy. Its monthly billing
is budgeted for twelve months, not assumed to require annual prepayment.
Dataforest's supplier reply offers a six-month minimum with €399 setup, rather
than its standard 24-month minimum, and 5% off twelve months prepaid. The selected
contract, renewal terms and combination of discount/setup need written confirmation.
See [supplier commitments](supplier-commitments.md), including the setup allowance.

WebNX Ogden remains a secondary US option: 810 TB modeled envelope and 500 TB/month
outgoing at $1,851/month. It is not an additional funded machine.

Shared downloads remain free within published limits. Paid exports recover actual
compressed delivery/preparation costs; they do not make public data proprietary.
Larger Txlab quotas and compute may be paid, while grant-funded code stays public.

## Continuation

Review renewal or handover by December 1, 2027; funded hosting ends December 31.
If further maintenance is not agreed, offer the Foundation or a nominated operator
the code, data, deployment instructions and provider-account/server transition.
Recipient acceptance and provider approval are required; the recipient pays future
operations. No indefinite free support or future-year funding is assumed.

## Qualification

See the [100-slot correctness and integrated qualification plan](validation-plan.md)
and [keyless usage/demand scenarios](usage-plan.md). The
[four-host/eight-stream download result](fetch-evidence.md) qualifies source
access only, not eight-worker native replay throughput.

Reforecast measured complete inventory, native context, checkpoints and actual
growth before scaling. Confirm the replica's disk/RAID layout, the source of
every retained component, scratch limits and restore throughput. Any earlier
start or scope/funding change requires an agreed plan; do not wait for disks
to cross the trigger before arranging capacity.
