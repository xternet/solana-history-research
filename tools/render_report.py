"""Generate readable research tables from sanitized numeric evidence."""

import argparse
import difflib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def share(number: float, total: float, digits: int = 2) -> str:
    return f"{number:.{digits}f} ({100 * number / total:.2f}%)"


def benchmarks(data: dict) -> str:
    storage, ingest, get = data["storage"], data["set"], data["get"]
    sample = data["sample"]
    request = next(
        row
        for row in get["requests"]
        if row["condition"] == "advised-cold" and row["concurrency"] == 1
    )
    lines = [
        "# Benchmarks and capacity model",
        "",
        "[Back to overview](../README.md)",
        "",
        f"Evidence date: {data['as_of']}. {data['status']}.",
        "",
        "The tables below are generated from [data/results.json](../data/results.json). "
        "They are preserved research evidence, not timings from the included tiny example.",
        "",
        "**Latest evidence:** [October 20 audit update](audit-update.md) adds sustained "
        "GET loads, fresh cold controls, compression candidates and capacity limits. "
        "The earlier latency table below is retained for comparison, not the current forecast.",
        "",
        "See [test hardware and worker limits](test-environment.md) for the actual "
        "CPU, RAM, HDD/NVMe setup, shared-host conditions and per-experiment allocations.",
        "",
        "## Earlier baseline summary",
        "",
        "| Area | Retained result | Qualification |",
        "|---|---:|---|",
        f"| Modeled compressed history | {storage['modeled_history_tb']:.3f} TB + C + I | One logical copy, 2020–partial 2026; not measured full-history capture |",
        f"| 2025 reference-year storage | {storage['modeled_reference_year_tb']:.3f} TB + C | Activity-scaled scenario, not measured full-year capture |",
        f"| Compute-side ingestion | {ingest['compute_side_stage_days']:.1f} stage-days | Composed model with heterogeneous worker limits; not fleet throughput |",
        f"| Serial stages including source fetch | {ingest['serial_stage_days']:.1f} stage-days | Serial sum; pipelines/fleets may overlap stages |",
        f"| Fresh replay request p50 / p90 | {request['p50_ms']:.2f} / {request['p90_ms']:.2f} ms | n={request['count']}; advised-cold, one caller; current-era sample |",
        "",
        "C = unresolved native capture correction after existing allowances; "
        "I = unmeasured one-time full-bootstrap discovery-index seed. Neither is zero.",
        "",
        "## STORAGE",
        "",
        "Decimal TB; one compressed logical copy. Percentages use the modeled "
        "total, excluding C/I. Parity, replicas, scratch and private workspaces are extra.",
        "",
        "| Component | TB/covered history (% modeled total) | TB/2025 (% modeled year total) | Basis |",
        "|---|---:|---:|---|",
    ]
    for row in storage["components"]:
        lines.append(
            f"| {row['data']} | {share(row['history_tb'], storage['modeled_history_tb'], 3)} | "
            f"{share(row['year_tb'], storage['modeled_reference_year_tb'], 3)} | {row['basis']} |"
        )
    lines += [
        f"| Modeled total (excludes C, I) | {storage['modeled_history_tb']:.3f} (100%) | {storage['modeled_reference_year_tb']:.3f} (100%) | Sum of conditional projections and allowances; not a measured bound |",
        "",
        "The extra query indexes are built from "
        f"{sample['counts']['transactions']:,} transactions and {sample['counts']['postings']:,} address references "
        f"across {len(sample['slots'])} recent slots. Recent bytes/TX are projected over historical activity; "
        "that is not a measured historical density distribution.",
        "",
        f"The initial cohort seed is {sample['cohort_seed_bytes']:,} B, not a complete network seed. "
        f"Its {sample['net_seed_closure_bytes']:,} B net encoded closure growth is counted. "
        "The initial seed is not charged again every sample window.",
        "",
        "### Baseline by year",
        "",
        "These rows preserve the pre-query-index baseline. "
        "They exclude the new index package and C/I; they are not the revised complete annual totals.",
        "",
        "| Period | Baseline compressed TB |",
        "|---|---:|",
    ]
    for row in storage["annual_baseline"]:
        label = str(row["year"]) + (" partial" if row["year"] == 2026 else "")
        lines.append(f"| {label} | {row['baseline_tb']:.3f} |")
    lines += [
        f"| One-time retained base, separate | {storage['one_time_baseline_seed_tb']:.3f} |",
        "",
        "## GET",
        "",
        "### Complete replay requests",
        "",
        "Original-input lookup, HDD account/context loading, fresh VM execution, "
        "verification and receipt. Metadata is resident. No provider/network/global routing. "
        "Cold is OS-advised, not a physical-drive cache flush; samples are small and current-era.",
        "",
        "| Condition / callers | n | p10 ms | p50 ms | p90 ms | Sample max ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in get["requests"]:
        lines.append(
            f"| {row['condition']} / {row['concurrency']} | {row['count']} | "
            + " | ".join(
                f"{row[key]:.2f}" for key in ("p10_ms", "p50_ms", "p90_ms", "sample_max_ms")
            )
            + " |"
        )
    lines += [
        "",
        "### Whole-request mean factors",
        "",
        f"Cohort: {get['factor_cohort']['condition']}, {get['factor_cohort']['concurrency']} caller, "
        f"n={get['factor_cohort']['count']}. These component means share one denominator. "
        "Do not subtract or add percentile values from different request cohorts.",
        "",
        "| Factor | Mean ms (% whole-request mean) |",
        "|---|---:|",
    ]
    for row in get["factors"]:
        lines.append(f"| {row['name']} | {share(row['ms'], get['factor_total_ms'])} |")
    lines += [
        f"| Total mean | {get['factor_total_ms']:.2f} (100%) |",
        "",
        "### Historical discovery queries",
        "",
        "Full compressed HDD payload and decode included; "
        "no VM execution, network or JSON response. Each row is a separate small query cohort, "
        "not a factor in the replay table above. With n≤6, show minimum/median/maximum, not tail percentiles.",
        "",
        "| Query / condition | n | Returned accounts | Min ms | Median ms | Max ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in get["historical_queries"]:
        amounts = row["returned_accounts"]
        lines.append(
            f"| {row['name']} / {row['condition']} | {row['count']} | {min(amounts)}–{max(amounts)} | "
            f"{row['min_ms']:.2f} | {row['p50_ms']:.2f} | {row['max_ms']:.2f} |"
        )
    rank = get["cohort_ranking_ms"]
    lines += [
        "",
        f"Cohort top-20 token-ranking checks (n={rank['count']}) took min/median/max "
        f"{rank['min_ms']:.2f}/{rank['p50_ms']:.2f}/{rank['max_ms']:.2f} ms, "
        "including a full candidate scan and Python reference decoder. "
        "Rankings are not universally sub-second. The cohort is not the full network.",
        "",
        "## SET",
        "",
        "Composed ms/produced block, not skipped slot. Percentages use the serial "
        "stage sum. Stage-days are projected wall time under heterogeneous source-worker limits, "
        "not CPU-days, homogeneous worker-days or calendar completion by a fleet. "
        "Unretained allocations stay explicit rather than being invented.",
        "",
        "| Ingestion factor | ms/block (% serial stages) | Stage-days | Source worker limit (logical CPU quota / GiB) |",
        "|---|---:|---:|---|",
    ]
    for row in ingest["factors"]:
        limits = row["worker_limits"]
        allocation = (
            f"{limits['logical_cpu_quota']} / {limits['memory_gib']}"
            if limits["logical_cpu_quota"] is not None
            else "Not retained for this stage"
        )
        lines.append(
            f"| {row['name']} | {share(row['ms'], ingest['factor_total_ms'])} | {row['stage_days']:.2f} | {allocation} |"
        )
    lines += [
        f"| Total serial stages | {ingest['factor_total_ms']:.2f} (100%) | {ingest['serial_stage_days']:.2f} | Heterogeneous ceilings; not one worker profile |",
        "",
        f"The added query-index sample used {ingest['new_index_sample_compute_seconds']:.3f} s "
        f"compute/repack and {ingest['new_index_sample_durable_seconds']:.3f} s grouped durability. "
        "It includes conservative cohort-seed re-encoding and excludes repeated base58/oracle "
        "preparation because native resolved IDs already exist. This is not a fused production callback "
        "or integrated multi-host benchmark.",
        "",
        "## Database index comparison",
        "",
        "Matched account-version pointers; not complete payload reads or replay. "
        "Four account sets, three repeats per cache condition. ClickHouse used a single batched SQL query per set.",
        "",
        "| Candidate | Cold n | Cold p50 ms | Cold p90 ms | Warm n | Primed warm p50 ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in data["database_comparison"]["account_sets"]:
        cold, warm = row["timings"]["cold-advised"], row["timings"]["warm-primed"]
        lines.append(
            f"| {row['name']} | {cold['count']} | {cold['p50_ms']:.2f} | {cold['p90_ms']:.2f} | {warm['count']} | {warm['p50_ms']:.2f} |"
        )
    lines += [
        "",
        data["database_comparison"]["scope"] + ".",
        "",
        "Cache/protocol conditions differ: the immutable key directory was RAM-resident, "
        "RocksDB's block cache was disabled, and ClickHouse used loopback SQL. "
        "The current JSON-directory prototype was not the smallest index on disk. "
        "These results do not establish a universal fastest/smallest database.",
        "",
        "## Assumptions and remaining uncertainty",
        "",
    ]
    lines.extend("* " + line for line in storage["assumptions"])
    lines += [
        "",
        "Full native state, epoch/era behavior, bootstrap inventory, global routing, "
        "source access and production publication/merge semantics remain qualification gates. "
        "See [the data contract](data-contract.md).",
        "",
        "## Evidence provenance",
        "",
        "Hashes identify original local research artifacts, "
        "not a public attestation or a rerun of the experiments. The raw operational bundles are "
        "not included; the allowlisted numeric export contains no operational paths or credentials.",
        "",
        "| Source artifact | SHA256 |",
        "|---|---|",
    ]
    lines.extend(
        f"| {row['artifact']} | `{row['sha256']}` |"
        for row in data["integrity"]["source_artifacts"]
    )
    return "\n".join(lines) + "\n"


def rpc_scope(data: dict) -> str:
    lines = [
        "# Planned historical RPC scope",
        "",
        "[Back to overview](../README.md)",
        "",
        f"Count: **{data['count']} state-backed capabilities** from current standard HTTP RPC names. "
        "This is our defined scope, not an official missing-method count, a shipped endpoint count "
        "or proof that no other provider holds historical state.",
        "",
        data["definition"],
        "",
        "The intention is to expose historical equivalents at a requested slot/transaction "
        "boundary. Standard commitment/minContextSlot parameters alone are not an arbitrary "
        "historical-state selector. Compatible native inputs and service adapters still need implementation.",
        "",
        "| Capability group | Count | Methods |",
        "|---|---:|---|",
    ]
    for group in data["groups"]:
        lines.append(
            f"| {group['group']} | {len(group['methods'])} | "
            + ", ".join(f"`{name}`" for name in group["methods"])
            + " |"
        )
    lines += [
        f"| Total | {data['count']} | Planned historical equivalents, not implemented APIs |",
        "",
        "## Counting rules",
        "",
        "* Count method names once, not parameter combinations or raw data fields.",
        "* Exclude block/transaction-history lookups already backed by ledger archives.",
        "* Exclude ledger-derived cursor/height/counter helpers and constant configuration.",
        "* Exclude node-local telemetry, administrative controls and live broadcasting.",
        "* Exclude deprecated aliases, subscriptions and Surfpool workspace operations.",
        "* Simulation is one execution capability; it is not a read-only state query.",
        "",
        "Some methods did not exist under their current names in older runtime eras. Their "
        "historical equivalents require explicit versioned policy, not blindly running today's rules.",
        "",
        "## Source references",
        "",
        f"* [Standard Solana HTTP RPC reference]({data['source']})",
        "* [Method dependency/source links](../data/rpc_methods.json)",
        "",
        "The earlier audit inventoried more names, including legacy/admin/local services. "
        "That larger number is not the number of unsupported historical RPC methods.",
    ]
    return "\n".join(lines) + "\n"


def audit_update(audit: dict, baseline: dict) -> str:
    storage, get = audit["storage"], audit["get"]
    lines = [
        "# October 20 audit: current evidence",
        "",
        "[Overview](../README.md) · [Earlier detailed tables](benchmarks.md) · "
        "[Numeric evidence](../data/audit-20261020.json) · [Reproduce](reproduction.md)",
        "",
        "These results update the earlier research, not a production guarantee. "
        "The native cohort remains current-era; no full-history run is implied.",
        "",
        "**Deployment update, October 24:** the [capacity plan](capacity-plan.md) now uses "
        "a full EU primary and full US replica, plus two geographic heads. "
        "The measurements below have not been rerun or relabelled as production results.",
        "",
        "## STORAGE",
        "",
        "One logical copy; same historical activity weights. Codec/frame substitutions "
        "change only measured, non-overlapping components. C + I remain unmeasured additions.",
        "",
        "| Layout | Modeled TB, excluding C + I | Saving |",
        "|---|---:|---:|",
        f"| Baseline | {storage['baseline_tb']:.3f} | — |",
    ]
    for row in storage["codec_candidates"]:
        if row["level"] in (6, 9, 15):
            lines.append(
                f"| Zstd {row['level']}, unchanged frames | "
                f"{row['same_model_total_tb_excluding_C_I']:.3f} | "
                f"{row['saved_tb']:.3f} TB ({row['saved_percent_total']:.2f}%) |"
            )
    for row in storage["frame_candidates"]:
        if row["wire_raw_frame_target_bytes"] == 4194304:
            lines.append(
                f"| 4MiB wire frames, Zstd {row['wire_zstd_level']}; other tested components Zstd 9 | "
                f"{row['known_modeled_tb_excluding_C_I']:.3f} | "
                f"{row['saved_tb']:.3f} TB ({row['saved_percent_total']:.2f}%) |"
            )
    checks = storage["decode_checks"]
    decode = checks["decode_extract_cpu_ms"]
    lines += [
        "",
        "Physical wire grouping does not change per-transaction account capture or require "
        "slot-prefix replay. Wire-frame savings replace the separate wire-codec saving; "
        "never add both. Directory/checksum bytes are included.",
        "",
        f"Wire sample: {checks['counts']['blocks']} blocks, "
        f"{checks['counts']['queries']:,} exact paired decode checks. "
        "The 2025 sample contains only 10 blocks. The 4MiB/Zstd9 candidate reads "
        "2.48–5.05× more compressed wire bytes per sampled transaction, depending on year.",
        "",
        f"RAM decode/extract p50: {decode['original_block']['p50']:.3f} → "
        f"{decode['frame_4m_level9']['p50']:.3f} ms. This is not an HDD or whole-request "
        "measurement. Keep the conservative budget until integrated GET/SET tests qualify "
        "the candidate. Account-only queries do not fetch transaction wires.",
        "",
        "### Capacity",
        "",
        "Updated EU envelope: 2 × (18 − 2) × 28 TB × 90% = **806.4 TB**. "
        "Updated US envelope: 5 × (12 − 2) × 18 TB × 90% = **810 TB**. "
        "These are two complete copies, before filesystem overhead, not pooled storage. "
        "The [2027 capacity plan](capacity-plan.md) replaces the former SX295/Artnet layout.",
        "",
    ]
    lines += [
        "The recomputed central end-2027 scenario is about 525 TB per copy; the stress "
        "scenario is about 648 TB, including declared planning allowances. Neither is a "
        "measured full-history bound. Reforecast monthly and obtain approval before "
        "approaching 10% free capacity; no mid-year expansion server is assumed.",
        "",
        "## GET",
        "",
        f"{get['verified_requests']:,} verified completed requests across "
        f"{get['distinct_targets']} repeated real targets, not that many distinct transactions. "
        f"Each run shares an {get['logical_cpu_ceiling']}-logical-CPU/"
        f"{get['memory_gib_ceiling']}-GiB ceiling on the "
        "[shared test host](test-environment.md).",
        "",
        "Arrival-to-completion includes queueing, HDD payload/decompression, input assembly, "
        "fresh native execution, verification and durable NVMe receipts. Metadata is resident. "
        "Caller network, public API overhead and global archive routing are excluded.",
        "",
        "| Cache / readers | Offered req/s | Completed | Queue rejected | p50 s | p90 s |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in get["load"]:
        label = "Warm" if row["cache_condition"] == "warm" else "Eviction stress"
        times = row["arrival_to_completion_seconds"]
        lines.append(
            f"| {label} / {row['readers']} | {row['offered_rps']} | "
            f"{row['verified_completed']:,} | {row['queue_rejections']:,} "
            f"({row['queue_rejections'] / row['offered'] * 100:.1f}%) | "
            f"{times['p50']:.3f} | {times['p90']:.3f} |"
        )
    lines += [
        "",
        "Warm four-reader runs lasted 18 minutes each; the eight-reader run lasted "
        "8 minutes. Eviction stress lasted 10 minutes and evicted pages at each arrival, "
        "possibly disrupting in-flight requests: it is not normal cold-miss latency. "
        "OS cache advice does not flush physical-drive caches.",
        "",
        "Fresh closed-batch controls evict only between completed batches:",
        "",
        "| Readers | Verified requests | Service p50 s | Service p90 s |",
        "|---|---:|---:|---:|",
    ]
    for row in get["closed_batch_control"]:
        times = row["service_seconds"]
        lines.append(
            f"| {row['readers']} | {row['verified_requests']} | "
            f"{times['p50']:.3f} | {times['p90']:.3f} |"
        )
    lines += [
        "",
        "The old 0.324-second cold median was not stable. Reader counts are small request "
        "handlers, not full-Bank backfill workers. These cohorts do not establish a "
        "blanket subsecond historical-RPC SLA.",
        "",
        "## SET",
        "",
        "| Measure | Current interpretation |",
        "|---|---|",
        f"| Compute-side model | {baseline['set']['compute_side_stage_days']:.1f} stage-days |",
        f"| Serial model including fetch | {baseline['set']['serial_stage_days']:.1f} stage-days |",
        "| Worker allocations | Existing eight workers plus qualified spare storage/head compute; no fixed density promised |",
        "| Parallel starts | Require verified range-start snapshots and matching boundary states |",
        "| Next qualification | Source → replay/capture → compression/index → remote durable HDD write → replica acknowledgement |",
        "",
        "The model combines different stage allocations and populations: **not fleet throughput** "
        "or interchangeable worker-days. Do not divide it by 24 to promise a calendar ETA. "
        "Measure initialization, peak RAM, scratch and integrated throughput on actual hosts. "
        "Two 40-GiB reservations do not fit a 64-GiB project allocation.",
        "",
        "## Correctness and remaining gates",
        "",
        f"* Expanded native sample: {audit['native_correctness']['exact']:,}/"
        f"{audit['native_correctness']['attempted']:,} matches across 100 current-era slots; "
        "this is not historical runtime or epoch qualification.",
        "* The local example now rejects unproven coverage gaps and demonstrates shard-aware "
        "version pointers. Parent assertions still require independently verified source data.",
        "* Native capture remains research tooling: production streaming, fork identity, "
        "complete startup inventory and a clean lifecycle still need implementation.",
        "* Qualify same-slot program upgrades, parent ProgramData use, epoch/reward transitions "
        "and the full native-runtime suite at matching source pins.",
        "* Qualify the planned manual, rate-limited warm standby and failback; current recovery "
        "tests do not demonstrate hot failover or redundant head capture.",
        "* Pointer database comparisons have different cache/protocol conditions and do not "
        "establish a universal minimum-size or fastest database.",
        "",
        "The raw operational captures are not bundled. Evidence hashes identify retained "
        "receipts; they are not independently authenticated chain-state proofs.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--patch", action="store_true")
    args = parser.parse_args()
    if args.check == args.patch:
        parser.error("Choose exactly one of --check or --patch")
    data = json.loads((ROOT / "data/results.json").read_text())
    rpc = json.loads((ROOT / "data/rpc_methods.json").read_text())
    audit = json.loads((ROOT / "data/audit-20261020.json").read_text())
    outputs = {
        "docs/benchmarks.md": benchmarks(data),
        "docs/rpc-scope.md": rpc_scope(rpc),
        "docs/audit-update.md": audit_update(audit, data),
    }
    if args.check:
        for name, content in outputs.items():
            if (ROOT / name).read_text() != content:
                raise ValueError("Generated report drift: " + name)
        print("STORAGE/GET/SET and RPC Markdown match their evidence sources")
    else:
        for name, content in outputs.items():
            path = ROOT / name
            before = path.read_text() if path.exists() else ""
            print(
                "".join(
                    difflib.unified_diff(
                        before.splitlines(keepends=True),
                        content.splitlines(keepends=True),
                        fromfile="a/" + name,
                        tofile="b/" + name,
                    )
                ),
                end="",
            )


if __name__ == "__main__":
    main()
