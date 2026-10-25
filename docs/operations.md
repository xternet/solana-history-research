# Health checks, API fallback and usage caps

Planned M2 operations design, not a deployed monitoring service. The offline PoC
does not demonstrate these production controls. Probe intervals, lag thresholds,
bucket sizes and recovery windows will be published with the qualified deployment.

## Detect faults and alert

Prometheus collects health and usage metrics; Grafana displays them and
Alertmanager sends deduplicated failure and recovery notifications to the operator.
Cross-site probes run from the existing EU/US hosts, so a surviving site can
detect the other site's failure without relying on the failed host to send alerts.

| Check | Detection | Response |
|---|---|---|
| Head sync | Finalized-slot lag against an independent reference, stalled heartbeat and capture gaps | Alert; exclude unverified or stale ranges from recent-state requests. Continue serving verified older history. |
| Database and API | Metadata query plus a bounded known-account read through the normal index, payload and checksum path | Remove an unhealthy endpoint from routing; alert and retry at the other eligible site. |
| Archive integrity | Manifest/checksum failures, replica lag and missing requested coverage | Reject affected ranges; use the other verified copy where available and alert for repair. |
| Capacity | Free disk, I/O errors, queue depth, concurrency and measured outgoing bytes | Alert before exhaustion; cap or queue external work while preserving operational reserves. |

Separate process liveness from readiness to serve a particular method and range.
A running process or successful database ping alone does not establish readiness.
If finality cannot be independently checked, report freshness as unknown rather
than healthy. Recent reads require verified coverage through the requested point.

## Select an endpoint and recover

1. Tools select and cache the nearer healthy EU/US API endpoint using approximate
   location and a short-lived health record. Expired health records are not trusted.
2. A timeout, unavailable service or explicit site-overload response permits one
   retry at the other site, only if it has the required verified coverage and capacity.
   An invalid request, missing history or exhausted client quota is not hidden by retries.
3. Consecutive failed probes open the endpoint's circuit breaker. Consecutive
   successful probes and a cooldown permit a controlled return to that region;
   the operator receives failure and recovery alerts.

Head lag does not automatically disable all historical reads. Clients must not
replace missing historical state with present-day state. If neither site can
answer correctly within its limits, return an explicit error or bounded queue
response. Server repair, archive recovery and write promotion remain manual.

## Enforce fair use

- **Request rate:** Per-client token buckets refill at a configured rate up to a
  bounded burst allowance. Charge method-specific costs so expensive scans cannot
  consume the same allocation as small account reads.
- **Identity:** Basic use needs no developer-supplied API key. Use temporary keyed
  network identifiers, consistent across both regions and rotated daily; publish
  aggregates only. NAT can share limits and changing IPs does not prove a new
  person. Authenticated higher quotas use an account identity.
- **Work bounds:** Enforce per-client and per-site concurrency, request-size,
  scan/page, time and response-size limits before expensive work. Keep queues
  bounded; count replay downloads and jobs by both count and bytes.
- **Byte budgets:** Reserve transfer capacity before admitting large downloads;
  reconcile reservations with actual delivery and measured host egress. Preserve
  at least the [usage plan's](usage-plan.md) 30% operations/safety reserve, raising
  it when required by replication or repair.
- **Cross-site accounting:** Both regions share each client's allowance; regional
  allocations sum to that allowance. If accounting connectivity fails, use only
  preallocated remaining regional budgets and stop when exhausted. Retrying in
  another region cannot reset or duplicate the allowance.
- **Responses:** Reject exhausted client allocations with HTTP 429 and Retry-After.
  Distinguish client-quota exhaustion from site overload, so tools cannot bypass
  a user's cap by switching regions. Both sites enforce their own traffic budget;
  when both are full, cap or queue instead of incurring automatic paid overages.

## M2 acceptance checks

Demonstrate stalled capture, unavailable metadata/database, failed payload reads,
unavailable or overloaded API, and recovery. Verify alerts, two-way request
fallback, cooldown/failback, and continued access to valid older history during
head lag. Test burst/concurrency/scan/byte caps and a cross-region accounting
partition: usage must stay within allocated budgets, including retries. Publish
the pinned configuration, fault-test results and recovery instructions with the
tagged production release.
