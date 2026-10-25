# 2020 correctness and M1 qualification

**Status: acceptance protocol and tested cohort selector; historical execution pending.**
The included offline fixture tests are not 2020 native execution. The retained
2,305 native matches across 100 slots belong to a current-era sample, not 2020.

## Public, reproducible 100-slot test

1. Publish the complete produced-slot inventory for 2020, source/checkpoint
   digests, date mapping and runtime/build/feature pins. Distinguish skipped slots
   from missing data. Freeze this inventory before choosing the seed; a reviewer
   supplies the seed to avoid cherry-picking available or easy cases.
2. Select 25 slots per calendar quarter (100 total) using the committed selector:

   ```bash
   python3 -m tools.sample_2020 inventory.json --seed REVIEWER_SEED
   python3 -m unittest discover -s tests -p test_sample_2020.py -v
   ```

   The inventory is a JSON list of `{ "slot": 123, "block_time": 1585699200 }`
   records, with independently checked UTC timestamps. That record is a schema
   illustration, not an asserted historical slot/date pair. The selector emits
   the input digest, seed and selected slots; it neither downloads nor replays.
3. Restore the preceding qualified snapshot/genesis state and execute the full
   prefix to each selected slot with its matching native runtime. Replay **every
   transaction in each selected slot**, not 100 convenient transactions. Publish
   transaction counts, successful and failed transaction results, and all gaps.
4. Compare status/errors, fees, committed account bytes and pre/post transaction
   positions with separately generated reference execution; compare canonical
   checkpoint state where independently available. Automatic writes and skipped
   slots need separate coverage. A ledger checksum or bank hash alone does not
   establish every intermediate account state. Document reference independence,
   shared-code limitations and any fields unavailable from the original archive.
5. Require zero unexplained mismatches and zero missing selected inputs/results.
   Publish failure receipts too; never replace failing sampled slots. Changed
   transactions are separate functional tests, not expected to match mainnet.
   Publish source instructions, pinned commands, machine limits and result digests
   so another operator can rerun; do not describe hashes alone as reproducibility.

Add targeted epoch/runtime transitions, account deletion/recreation and automatic
updates separately. A 100-slot sample is a correctness check, **not proof of the
entire year**; full coverage/manifests and checkpoint checks remain required.

## Before committing M2 rentals

Publish an integrated trial on representative 2020 and recent-era ranges,
including 1/2/4/8-worker measurements where actual hardware permits. Record host
specifications, elapsed time, transactions/slots, source bytes, retained bytes,
peak RAM/scratch, durable dual-copy writes and source throttling. Do not equate
eight download streams or eight small query handlers with eight replay workers.

M1 acceptance requires the above sampled checks, complete 2020 coverage inventory,
API/replay tests and recovery checks. M2 rental approval additionally requires a
measured, costed plan that fits the remaining schedule and quoted resources;
otherwise agree a revised plan before committing funds. Heterogeneous stage-days
must not be divided by a nominal worker count to manufacture a completion ETA.
