# Data contract and remaining work

[Back to overview](../README.md)

## Retain during ingestion

| Data | Why it is needed |
|---|---|
| Genesis/base, complete account roster and coverage | Distinguish a nonexistent account from an uncaptured one |
| All account fields, data, deletions and transaction positions | Exact pre/post state, programs, token and application state |
| Automatic phases, repeated-write order and required native causes | Rewards, rent, fees, loader activation and native continuation |
| Sysvar caches, blockhash queue, features and runtime identity | Correct original and modified execution |
| Required epoch/vote/stake/reward/fee/configuration facts | Native transitions, leader/stake queries and historical rules |
| Original signed transaction wires and resolved address facts | Lookup and execution; include readonly/ALT and failed landed references |
| Original results, rewards and block envelopes | Status, logs, CPI, CU, balances, return values and independent comparisons |
| Checksummed indexes, source/runtime identity and publication receipts | Coverage, integrity, provenance and recovery |

On-chain program/ProgramData, ALT, pool, mint and oracle bytes belong in account
history. Do not create a second global copy solely for a later query. Preserve
originally unavailable metadata as unavailable; replay-generated output is not an
independently recorded original result.

Original transaction results and supporting metadata are already included in the
storage model. A per-change account cache does **not** make original transactions
or execution context unnecessary for transaction lookup and simulation.

## Derive or index from retained facts

* Program membership and token mint/authority/delegate intervals.
* Address-to-transaction postings and temporal token-activity joins.
* SOL/token rankings from state scans, with bounded result caches if justified.
* Public parser/runtime artifacts and reusable native caches where reconstruction
  is proven for the requested era.

Some broad scans are slow. Avoiding a global ranking-history dataset is a storage
trade-off, not a promise that every ranking query will finish in milliseconds.

## Unresolved before irreversible bulk collection

| Gate | What remains |
|---|---|
| Native correction C | Measure irreducible native fields after crediting existing context/checkpoint/phase allowances |
| Bootstrap discovery index I | Size the complete starting inventory; a touched-account cohort is not the full network |
| Epoch/reward transitions | Test actual transitions, caches and reward partition progression |
| Runtime/loader eras | Validate features, deployment visibility and historical runtime configurations |
| Phase/write ordering | Preserve required repeated writes and automatic causes under a production streaming writer |
| Publication/routing/scale | Qualify cross-store atomicity, global fanout, compaction, concurrency and failure recovery |
| Source delivery | Confirm a supported bulk archive path and real source/egress costs |
| Coverage continuity | Verify canonical parent links/skipped slots and range-start inventories; never carry state across an unexplained hole |
| Historical sources | Qualify exceptional archive gaps, restart boundaries and snapshot availability before scaling workers |
| Worker lifecycle | Stream bounded data with fork identity; exit cleanly and never publish partial generations |

C and I are **unknown**, not zero. Some values may be derivable and need no extra
payload, but a source inventory alone does not prove that reconstruction.
Do not retire raw inputs or treat the storage projection as a purchasing ceiling
until these gates are satisfied.
I is the incremental directory/inventory cost after reuse, not a requirement to
retain every worker's full starting snapshot permanently. Complete genesis
capture can derive discovery membership from the retained creation/change facts.

Parent ProgramData must actually reach the execution adapter for loader visibility
tests. A retained parent image alone is insufficient. Validate the complete native
suite against the same source/build pins used by the worker.

Canonical history, modified single-transaction simulation and advancing a modified
fork are distinct targets. Canonical future deltas cannot simply be applied to an
edited fork to claim a correct counterfactual future.

## Integrity versus trustless proofs

Sealed frames, source/runtime hashes, coverage receipts, native checkpoint
comparisons and independent account/result checks make corruption and provenance
auditable. A block hash by itself does not prove every intermediate account state.

This repository does not provide a trustless consensus-authenticated proof for an
arbitrary historical account or an account's absence. Checksums in the fixture
bind its bytes; verifying them is not independent verification of mainnet state.

## Source references

* [Agave](https://github.com/anza-xyz/agave)
* [Solana RPC reference](https://solana.com/docs/rpc/http)
* [Old Faithful archive project](https://github.com/rpcpool/yellowstone-faithful)
* [SVM Replay](https://github.com/xternet/svm-replay)
