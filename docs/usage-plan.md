# Keyless use, demand scenarios and public reporting

This is a measurement plan, not observed demand or an already deployed service.
SVM Replay and the Txlab UI will use the basic free API without a developer key;
supported Surfpool/Anchor flows inherit it. Public history stays public. Rate,
scan, concurrency and transfer limits protect fair access; optional paid higher
usage, additional compute and bulk preparation/delivery do not gate basic use.

## Daily counters and monthly reports

Report successful calls by method, errors, throttled/queued requests, replay-input
downloads, delivered payload bytes, measured network egress by host, p50/p95
latency and approximate daily distinct network clients. Separate external demand
from health checks, internal replication, retries, repairs and load tests. Reconcile
application counters with provider billing; payload bytes are not wire bytes.

Estimate daily distinct IPs using an in-memory keyed hash with a rotating daily
secret; discard the secret and individual identifiers after aggregation. Publish
only aggregates, not raw IPs. NAT, shared gateways, IPv6 rotation and bots mean
these are **network-client estimates, not unique people or projects**. Do not sum
daily distinct counts and call the result monthly unique users. Any security logs
need a separate limited retention/access policy.

Keyless traffic counts toward operational impact, but cannot alone substantiate
verified-project adoption rewards. Retain the separate project-attested reward
rules and report active/returning verified projects alongside aggregate free use.

## Illustrative low / medium / high demand

Assumptions: 30-day month; average account response 20 kB and replay-input download
5 MB, both decimal compressed payload sizes. These are planning inputs to replace
with measured distributions, not a benchmark or promised free allowance.

| Scenario | Reads/day | Replay downloads/day | API payload/month | Shared bulk/month | Total external payload/month |
|---|---:|---:|---:|---:|---:|
| Low | 10,000 | 1,000 | 0.156 TB | 5 TB | 5.156 TB |
| Medium | 100,000 | 10,000 | 1.560 TB | 25 TB | 26.560 TB |
| High | 1,000,000 | 100,000 | 15.600 TB | 100 TB | 115.600 TB |

Formula: `(reads/day × 20,000 + downloads/day × 5,000,000) × 30 / 10^12`.
Ten-times larger replay inputs make high-scenario API traffic 150.6 TB/month;
with 100 TB bulk, that is 250.6 TB **before** protocol overhead or operations.
Do not promise a fixed download count independently of byte limits.

Initially reserve at least 30% of each host's outgoing allowance for operations
and safety, increasing it when measured replication/repair needs demand. User
traffic ceilings are therefore at most 175 TB EU and 210 TB US per month, not
a pooled allowance. Initial seeding may consume more than a month's allowance;
schedule it separately and reduce/queue user downloads as needed. Enforce limits
against measured host egress; obtain provider overage/cutoff terms before relying
on a strict cost cap. No automatic paid overage is charged to the grant.
