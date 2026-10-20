# Planned historical RPC scope

[Back to overview](../README.md)

Count: **24 state-backed capabilities** from current standard HTTP RPC names. This is our defined scope, not an official missing-method count, a shipped endpoint count or proof that no other provider holds historical state.

State-backed historical equivalents of current standard HTTP RPC capabilities; excludes ledger-only queries/counters, constant configuration, telemetry, administrative controls, deprecated aliases and subscriptions.

The intention is to expose historical equivalents at a requested slot/transaction boundary. Standard commitment/minContextSlot parameters alone are not an arbitrary historical-state selector. Compatible native inputs and service adapters still need implementation.

| Capability group | Count | Methods |
|---|---:|---|
| Accounts, discovery and SOL supply | 6 | `getAccountInfo`, `getBalance`, `getLargestAccounts`, `getMultipleAccounts`, `getProgramAccounts`, `getSupply` |
| Token state and discovery | 5 | `getTokenAccountBalance`, `getTokenAccountsByDelegate`, `getTokenAccountsByOwner`, `getTokenLargestAccounts`, `getTokenSupply` |
| Fees, rent and blockhash validity | 4 | `getFeeForMessage`, `getMinimumBalanceForRentExemption`, `getLatestBlockhash`, `isBlockhashValid` |
| Stake, vote, leaders and production | 6 | `getVoteAccounts`, `getStakeMinimumDelegation`, `getLeaderSchedule`, `getSlotLeader`, `getSlotLeaders`, `getBlockProduction` |
| Inflation parameters | 2 | `getInflationGovernor`, `getInflationRate` |
| Historical execution | 1 | `simulateTransaction` |
| Total | 24 | Planned historical equivalents, not implemented APIs |

## Counting rules

* Count method names once, not parameter combinations or raw data fields.
* Exclude block/transaction-history lookups already backed by ledger archives.
* Exclude ledger-derived cursor/height/counter helpers and constant configuration.
* Exclude node-local telemetry, administrative controls and live broadcasting.
* Exclude deprecated aliases, subscriptions and Surfpool workspace operations.
* Simulation is one execution capability; it is not a read-only state query.

Some methods did not exist under their current names in older runtime eras. Their historical equivalents require explicit versioned policy, not blindly running today's rules.

## Source references

* [Standard Solana HTTP RPC reference](https://solana.com/docs/rpc/http)
* [Method dependency/source links](../data/rpc_methods.json)

The earlier audit inventoried more names, including legacy/admin/local services. That larger number is not the number of unsupported historical RPC methods.
