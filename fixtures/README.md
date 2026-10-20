# Fixture provenance

[Back to overview](../README.md)

`account_changes.json` was **exported from a private local mainnet replay capture**,
not generated as synthetic benchmark output. It contains captured account bytes
from two contiguous slots. Source hashes preserve local provenance only: the raw
capture and a public transaction-to-version verification recipe are not included,
so an outside reviewer cannot independently establish its on-chain provenance.

Only a small cohort of legacy SPL Token accounts is retained. It is not a full
snapshot, a complete program/mint roster, a native Bank image or a transaction
execution fixture. The data does not demonstrate Token-2022 or epoch transitions.
Exact slots, source reference hashes, runtime identity, account count and versions
are inspectable in the JSON itself and the example's output.

## Native byte encoding

Each base64 value contains, in order:

| Field | Bytes |
|---|---:|
| Account address | 32 |
| Lamports | 8 |
| Rent epoch | 8 |
| Program owner | 32 |
| Executable flag | 1 |
| Account data length | 8 |
| Account data | Variable |

Integer fields are little-endian. This is the capture's native account-record
encoding, not a complete Solana snapshot archive format or RPC response.
Zero-lamport deletions are encoded as the 32-byte account key followed by 57 zero
bytes: an explicit known deletion marker, not missing coverage. The included
capture extract contains no deletions; synthetic tests cover them separately.

## Cursor semantics

* `slot`: the source mainnet slot.
* `position = -2`: the known account baseline before slot initialization.
* `position = -1`: captured automatic initialization updates.
* `position = 0..n-1`: state after that transaction's captured stores.
* `position = n`: the slot-final phase, where present.
* `order`: per-slot callback number from one capture run; only meaningful between
  writes to the same account at the same position. It is not a canonical ordering
  between independent accounts or different replay runs.

The query defaults to the last retained update at a transaction boundary.
Explicit ordering can inspect individual captured records. Before transaction
`i`, query the previous transaction boundary; initialization and final phases
must be accounted for separately in a full native replay. For transaction zero,
the immediately preceding boundary is initialization (`position = -1`), not the
pre-initialization baseline (`position = -2`).

The extract contains only baselines and transaction writes for legacy wrapped-SOL
token accounts, with no automatic phases or repeated same-position writes. The
tests construct those edge cases and compare every query with a brute-force scan;
that validates the byte-store logic, not native automatic-phase capture.

The subset's initial account baselines are known. An unlisted account has unknown
coverage, not proven nonexistence. SHA256 hashes bind fixture records but are not
consensus proofs. No credentials, off-chain private data or signing material are
included. Code/documentation licensing does not claim exclusive rights to public
blockchain facts.
