# M1 acceptance: historical data through 2020

**Status: planned M1 tests, not a claim of completed historical validation.**
The retained 2,305 native matches across 100 slots are current-era evidence,
not the historical sample below.

| Check | Pass condition |
|---|---|
| Fetch | Retry/resume scripts fetch verified inputs and support multiple workers. |
| Replay | Transactions from 100 randomly selected slots through 2020 match reference results. |
| API | Historical state and replay inputs are queryable through the OpenAPI-documented API. |

Deliver one runnable check for each row, with commands and pass/fail results,
under `/test`. Save the replay sample and seed so it can be rerun; report failures
rather than replacing sampled slots. All three checks use data through 2020.

M2 scales the same pipeline to full history. Fixed worker-throughput targets,
full-year coverage audits and separate recovery/epoch-transition suites are not
additional M1 acceptance gates.

The existing `tools.sample_2020` selector and `tests/test_sample_2020.py` check
sample selection only; they do not execute historical transactions and are not
the promised M1 `/test` suite.
