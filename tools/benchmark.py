"""Bounded offline codec/frame experiments; prints measurements, not TB estimates.

Ports the audited level-rotation and contiguous-frame methods to explicit local
inputs. The bundled account fixture is NOT a transaction-wire benchmark.
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import time

from history_poc.store import validate_account, validate_coverage
from history_poc.zstd import MAX_FRAME_BYTES, Zstd

MAX_INPUT_BYTES = 128 * 1024**2
MAX_RECORDS = 100000
FRAME = struct.Struct("<QII32s")
RECORD = struct.Struct("<QQII")


def validate_records(records: list[tuple[int, bytes]]) -> None:
    if not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError("Input must contain 1–100000 records")
    total = 0
    for slot, raw in records:
        if type(slot) is not int or not 0 <= slot < 2**64:
            raise ValueError("Record slots must be unsigned 64-bit integers")
        if not 0 < len(raw) <= MAX_FRAME_BYTES:
            raise ValueError("Record is empty or exceeds the 8MiB frame bound")
        total += len(raw)
        if total > MAX_INPUT_BYTES:
            raise ValueError("Input exceeds the 128MiB experiment bound")


def load_manifest(path: Path) -> list[tuple[int, bytes]]:
    if path.stat().st_size > 32 * 1024**2:
        raise ValueError("Manifest exceeds the 32MiB metadata bound")
    root = path.resolve().parent
    manifest = json.loads(path.read_text())
    records = []
    total = 0
    for item in manifest["records"]:
        source = (root / item["path"]).resolve()
        if Path(item["path"]).is_absolute() or not source.is_relative_to(root):
            raise ValueError("Input paths must stay inside the manifest directory")
        size = source.stat().st_size
        total += size
        if not 0 < size <= MAX_FRAME_BYTES or total > MAX_INPUT_BYTES:
            raise ValueError("Input size exceeds experiment bounds")
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Input checksum differs from manifest")
        records.append((item["slot"], raw))
        if len(records) > MAX_RECORDS:
            raise ValueError("Too many input records")
    validate_records(records)
    return records


def load_fixture(path: Path) -> list[tuple[int, bytes]]:
    if path.stat().st_size > 256 * 1024**2:
        raise ValueError("Fixture exceeds the 256MiB encoded-input bound")
    fixture = json.loads(path.read_text())
    if fixture["schema"] != "solana-account-history-fixture/v1":
        raise ValueError("Unsupported fixture schema")
    validate_coverage(fixture["coverage"])
    records = []
    for account in fixture["accounts"]:
        for version in account["versions"]:
            raw = base64.b64decode(version["raw_base64"], validate=True)
            validate_account(raw, account["address"])
            if hashlib.sha256(raw).hexdigest() != version["sha256"]:
                raise ValueError("Fixture checksum differs")
            records.append((version["slot"], raw))
    validate_records(records)
    return sorted(records, key=lambda row: row[0])


def measure(records: list[tuple[int, bytes]], levels: list[int], frame_bytes: list[int]) -> dict:
    validate_records(records)
    if (
        not levels
        or len(levels) != len(set(levels))
        or any(type(level) is not int or not 1 <= level <= 15 for level in levels)
        or not frame_bytes
        or len(frame_bytes) != len(set(frame_bytes))
        or any(type(size) is not int or not 0 <= size <= MAX_FRAME_BYTES for size in frame_bytes)
    ):
        raise ValueError("Invalid or duplicate level/frame configuration")
    if any(records[index][0] < records[index - 1][0] for index in range(1, len(records))):
        raise ValueError("Input slots must be ordered")
    codec = Zstd()
    variants = []
    verified = 0
    for target in frame_bytes:
        groups = []
        group = []
        group_size = 0
        for slot, raw in records:
            if group and (target == 0 or group_size + len(raw) > target or slot > group[-1][0] + 1):
                groups.append(group)
                group, group_size = [], 0
            group.append((slot, raw))
            group_size += len(raw)
        groups.append(group)
        # Rotate level order across layouts to reduce fixed-order timing bias.
        rotation = len(variants) // len(levels) % len(levels)
        for level in levels[rotation:] + levels[:rotation]:
            payload_bytes = 0
            payloads = []
            frame_directory, record_directory = bytearray(), bytearray()
            compression_s = decompression_s = 0.0
            read_bytes = standalone_bytes = 0
            for frame_id, group in enumerate(groups):
                raw = b"".join(value for _, value in group)
                start = time.perf_counter()
                packed = codec.compress(raw, level=level)
                compression_s += time.perf_counter() - start
                start = time.perf_counter()
                decoded = codec.decompress(packed)
                decompression_s += time.perf_counter() - start
                if decoded != raw:
                    raise ValueError("Frame round trip differs")
                frame_directory.extend(
                    FRAME.pack(
                        payload_bytes, len(packed), len(raw), hashlib.sha256(packed).digest()
                    )
                )
                payloads.append(packed)
                offset = 0
                for slot, value in group:
                    if decoded[offset : offset + len(value)] != value:
                        raise ValueError("Record directory round trip differs")
                    record_directory.extend(RECORD.pack(slot, frame_id, offset, len(value)))
                    offset += len(value)
                    read_bytes += len(packed)
                    standalone_bytes += len(codec.compress(value, level=level))
                    verified += 1
                payload_bytes += len(packed)
            packed_frames = codec.compress(bytes(frame_directory), level=3)
            packed_records = codec.compress(bytes(record_directory), level=3)
            directory_bytes = len(packed_frames) + len(packed_records)
            frame_rows = list(FRAME.iter_unpack(codec.decompress(packed_frames)))
            record_rows = list(RECORD.iter_unpack(codec.decompress(packed_records)))
            if len(frame_rows) != len(groups) or len(record_rows) != len(records):
                raise ValueError("Serialized directory count differs")
            expected_offset = 0
            for frame_id, (offset, size, raw_size, digest) in enumerate(frame_rows):
                payload = payloads[frame_id]
                if (
                    offset != expected_offset
                    or size != len(payload)
                    or digest != hashlib.sha256(payload).digest()
                    or raw_size != sum(len(raw) for _, raw in groups[frame_id])
                ):
                    raise ValueError("Serialized frame directory differs")
                expected_offset += size
            previous_frame = None
            for (slot, frame_id, offset, size), (expected_slot, expected) in zip(
                record_rows, records
            ):
                if frame_id != previous_frame:
                    decoded = codec.decompress(payloads[frame_id])
                    previous_frame = frame_id
                if slot != expected_slot or decoded[offset : offset + size] != expected:
                    raise ValueError("Serialized record lookup differs")
            variants.append(
                {
                    "level": level,
                    "frame_bytes": target,
                    "frame_count": len(groups),
                    "record_count": len(records),
                    "payload_bytes": payload_bytes,
                    "directory_bytes": directory_bytes,
                    "total_bytes": payload_bytes + directory_bytes,
                    "compression_ms": compression_s * 1000,
                    "decompression_ms": decompression_s * 1000,
                    "compressed_read_amplification": read_bytes / standalone_bytes,
                }
            )
    return {
        "schema": "bounded-codec-experiment/v1",
        "scope": "RAM codec measurements; no disk, VM, network or annual projection",
        "input_bytes": sum(len(raw) for _, raw in records),
        "input_sha256": hashlib.sha256(
            b"".join(struct.pack("<QQ", slot, len(raw)) + raw for slot, raw in records)
        ).hexdigest(),
        "verified_record_roundtrips": verified,
        "variants": sorted(variants, key=lambda row: (row["frame_bytes"], row["level"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--fixture", type=Path)
    inputs.add_argument("--manifest", type=Path)
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 3, 6, 9, 15])
    parser.add_argument("--frame-bytes", type=int, nargs="+", default=[0, 1048576, 4194304])
    args = parser.parse_args()
    records = load_fixture(args.fixture) if args.fixture else load_manifest(args.manifest)
    print(json.dumps(measure(records, args.levels, args.frame_bytes), indent=2))


if __name__ == "__main__":
    main()
