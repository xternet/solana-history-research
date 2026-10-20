"""Small immutable anchor/patch store with exact transaction-boundary lookup."""

import base64
import bisect
import hashlib
import json
import os
from pathlib import Path
import struct

from .zstd import Zstd

PATCH_HEADER = struct.Struct("<III")
LAST_ORDER = 2**63 - 1
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class CoverageError(ValueError):
    """The requested account/cursor is outside the example's proven coverage."""


def address(raw: bytes) -> str:
    number = int.from_bytes(raw, "big")
    digits = ""
    while number:
        number, remainder = divmod(number, 58)
        digits = ALPHABET[remainder] + digits
    return "1" * (len(raw) - len(raw.lstrip(b"\0"))) + digits


def validate_account(raw: bytes, key: str) -> None:
    if len(raw) < 89 or raw[80] not in (0, 1):
        raise ValueError("Malformed native account header")
    if len(raw) != 89 + int.from_bytes(raw[81:89], "little") or address(raw[:32]) != key:
        raise ValueError("Account length/address differs from fixture identity")


def encode_patch(before: bytes, after: bytes) -> bytes:
    prefix = 0
    while prefix < min(len(before), len(after)) and before[prefix] == after[prefix]:
        prefix += 1
    suffix = 0
    while (
        suffix < min(len(before), len(after)) - prefix
        and before[len(before) - suffix - 1] == after[len(after) - suffix - 1]
    ):
        suffix += 1
    middle = after[prefix : len(after) - suffix] if suffix else after[prefix:]
    return PATCH_HEADER.pack(len(after), prefix, suffix) + middle


def decode_patch(before: bytes, patch: bytes) -> bytes:
    if len(patch) < PATCH_HEADER.size:
        raise ValueError("Truncated patch header")
    size, prefix, suffix = PATCH_HEADER.unpack_from(patch)
    if prefix + suffix > len(before):
        raise ValueError("Patch copy ranges overlap or exceed anchor")
    tail = before[len(before) - suffix :] if suffix else b""
    result = before[:prefix] + patch[PATCH_HEADER.size :] + tail
    if len(result) != size:
        raise ValueError("Patch result length differs")
    return result


def durable_write(path: Path, raw: bytes) -> None:
    with path.open("xb") as stream:
        if stream.write(raw) != len(raw):
            raise OSError("Short immutable-segment write")
        stream.flush()
        os.fsync(stream.fileno())


def sync_directory(path: Path) -> None:
    directory = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def create_output_directory(path: Path) -> None:
    if not path.parent.exists():
        create_output_directory(path.parent)
    path.mkdir()
    sync_directory(path.parent)


def validate_coverage(coverage: dict) -> dict[str, int]:
    counts = coverage["slot_transaction_counts"]
    if not isinstance(counts, dict) or not counts:
        raise ValueError("Coverage must enumerate captured slots")
    for slot, count in counts.items():
        if not isinstance(slot, str) or not slot.isdecimal() or str(int(slot)) != slot:
            raise ValueError("Coverage slot keys must be canonical nonnegative integers")
        if type(count) is not int or count < 0:
            raise ValueError("Transaction counts must be nonnegative integers")
    slots = [int(slot) for slot in counts]
    if (
        type(coverage["first_slot"]) is not int
        or type(coverage["last_slot"]) is not int
        or coverage["first_slot"] != min(slots)
        or coverage["last_slot"] != max(slots)
    ):
        raise ValueError("Coverage endpoints differ from captured slots")
    # Consecutive captured slots need no extra annotation. A gap requires an
    # explicit canonical-parent assertion from the capture source, not an
    # assumption that all omitted slots were skipped by the chain.
    ordered = sorted(slots)
    predecessors = dict(zip(ordered[1:], ordered[:-1]))
    parents = coverage.get("parent_slots", {})
    if not isinstance(parents, dict):
        raise ValueError("Coverage parent links must be a mapping")
    for slot, parent in parents.items():
        if (
            slot not in counts
            or type(parent) is not int
            or int(slot) not in predecessors
            or predecessors[int(slot)] != parent
        ):
            raise ValueError("Coverage parent link differs from captured predecessor")
    for slot, previous in predecessors.items():
        if slot != previous + 1 and parents.get(str(slot)) != previous:
            raise ValueError("Coverage gap requires an explicit parent link")
    return counts


def validate_cursor(counts: dict[str, int], slot: int, position: int, order: int) -> None:
    if any(type(value) is not int for value in (slot, position, order)):
        raise CoverageError("Cursor fields must be integers")
    if str(slot) not in counts:
        raise CoverageError("Slot is outside the captured fixture range")
    if not -2 <= position <= counts[str(slot)]:
        raise CoverageError("Position is outside the captured slot")
    if not 0 <= order <= LAST_ORDER:
        raise CoverageError("Order is outside the captured cursor range")


def verify_history(reader: "History", fixture: dict) -> int:
    checked = 0
    for account in fixture["accounts"]:
        for event in account["versions"]:
            cursor = (event["slot"], event["position"], event["order"])
            # This reference scans the input, independently of the encoded index.
            prior = [
                row
                for row in account["versions"]
                if (row["slot"], row["position"], row["order"]) <= cursor
            ]
            expected = base64.b64decode(prior[-1]["raw_base64"], validate=True)
            if reader.get(account["address"], *cursor) != expected:
                raise ValueError("Indexed state differs from original fixture scan")
            checked += 1
    return checked


def build_history(fixture: dict, target: Path) -> dict:
    if target.exists():
        raise FileExistsError("Output directory already exists; choose a new directory")
    if fixture["schema"] != "solana-account-history-fixture/v1" or not fixture["accounts"]:
        raise ValueError("Unsupported or empty fixture")
    counts = validate_coverage(fixture["coverage"])
    payload = bytearray()
    objects = []
    index = {}
    full_bytes = 0
    patches = 0
    for account in fixture["accounts"]:
        key = account["address"]
        if key in index or not account["versions"]:
            raise ValueError("Duplicate account or empty account history")
        rows = []
        anchor = None
        anchor_id = None
        for version in account["versions"]:
            cursor = (version["slot"], version["position"], version["order"])
            validate_cursor(counts, *cursor)
            if rows and cursor <= tuple(rows[-1][:3]):
                raise ValueError("Fixture cursor order is not strictly increasing")
            raw = base64.b64decode(version["raw_base64"], validate=True)
            validate_account(raw, key)
            if hashlib.sha256(raw).hexdigest() != version["sha256"]:
                raise ValueError("Fixture account checksum differs")
            encoded, mode, reference = raw, "full", None
            if anchor is None:
                anchor, anchor_id = raw, len(objects)
            else:
                candidate = encode_patch(anchor, raw)
                if len(candidate) < len(raw):
                    encoded, mode, reference = candidate, "patch", anchor_id
                    patches += 1
            objects.append(
                {
                    "offset": len(payload),
                    "length": len(encoded),
                    "mode": mode,
                    "anchor": reference,
                    "sha256": version["sha256"],
                }
            )
            rows.append([*cursor, len(objects) - 1])
            payload.extend(encoded)
            full_bytes += len(raw)
        index[key] = rows
    codec = Zstd()
    packed = codec.compress(bytes(payload))
    if codec.decompress(packed) != bytes(payload):
        raise ValueError("Segment compression roundtrip differs")
    directory_raw = json.dumps(
        {"accounts": index, "objects": objects}, separators=(",", ":")
    ).encode()
    packed_index = codec.compress(directory_raw)
    manifest = {
        "schema": "solana-history-example/v2",
        "coverage": fixture["coverage"],
        "account_subset_only": True,
        "payload_sha256": hashlib.sha256(packed).hexdigest(),
        "decoded_sha256": hashlib.sha256(payload).hexdigest(),
        "index_sha256": hashlib.sha256(packed_index).hexdigest(),
        "decoded_index_sha256": hashlib.sha256(directory_raw).hexdigest(),
        "full_record_bytes": full_bytes,
        "encoded_object_bytes": len(payload),
        "compressed_payload_bytes": len(packed),
        "patch_objects": patches,
        "version_count": len(objects),
        "scope": "One bounded demonstration segment; not the production index layout",
    }
    create_output_directory(target)
    durable_write(target / "payload.zst", packed)
    durable_write(target / "index.zst", packed_index)
    manifest_raw = json.dumps(manifest, indent=2).encode() + b"\n"
    durable_write(target / "manifest.pending", manifest_raw)
    durable_write(
        target / "manifest.pending.sha256",
        hashlib.sha256(manifest_raw).hexdigest().encode() + b"\n",
    )
    reader = History(target, _pending=True)
    if verify_history(reader, fixture) != manifest["version_count"]:
        raise ValueError("Verified version count differs from manifest")
    sync_directory(target)
    (target / "manifest.pending.sha256").rename(target / "manifest.json.sha256")
    (target / "manifest.pending").rename(target / "manifest.json")
    sync_directory(target)
    return manifest


class History:
    def __init__(self, target: Path, *, _pending: bool = False) -> None:
        name = "manifest.pending" if _pending else "manifest.json"
        manifest_raw = (target / name).read_bytes()
        expected = (target / (name + ".sha256")).read_text().strip()
        if hashlib.sha256(manifest_raw).hexdigest() != expected:
            raise ValueError("Segment manifest checksum differs")
        self.manifest = json.loads(manifest_raw)
        if self.manifest["schema"] != "solana-history-example/v2":
            raise ValueError("Unsupported segment schema")
        self.counts = validate_coverage(self.manifest["coverage"])
        packed = (target / "payload.zst").read_bytes()
        if hashlib.sha256(packed).hexdigest() != self.manifest["payload_sha256"]:
            raise ValueError("Compressed segment checksum differs")
        self.payload = Zstd().decompress(packed)
        if hashlib.sha256(self.payload).hexdigest() != self.manifest["decoded_sha256"]:
            raise ValueError("Decoded segment checksum differs")
        packed_index = (target / "index.zst").read_bytes()
        if hashlib.sha256(packed_index).hexdigest() != self.manifest["index_sha256"]:
            raise ValueError("Compressed index checksum differs")
        raw_index = Zstd().decompress(packed_index)
        if hashlib.sha256(raw_index).hexdigest() != self.manifest["decoded_index_sha256"]:
            raise ValueError("Decoded index checksum differs")
        self.index = json.loads(raw_index)
        if (
            sum(len(rows) for rows in self.index["accounts"].values())
            != self.manifest["version_count"]
        ):
            raise ValueError("Index version count differs from manifest")
        for rows in self.index["accounts"].values():
            previous = None
            for slot, position, order, _identity in rows:
                validate_cursor(self.counts, slot, position, order)
                cursor = (slot, position, order)
                if previous is not None and cursor <= previous:
                    raise ValueError("Index cursor order is not strictly increasing")
                previous = cursor

    def _object(self, identity: int) -> bytes:
        row = self.index["objects"][identity]
        start, length = row["offset"], row["length"]
        raw = self.payload[start : start + length]
        if start < 0 or len(raw) != length:
            raise ValueError("Object slice lies outside segment")
        if row["mode"] == "patch":
            reference = row["anchor"]
            if not isinstance(reference, int) or not 0 <= reference < identity:
                raise ValueError("Patch has invalid/forward anchor")
            if self.index["objects"][reference]["mode"] != "full":
                raise ValueError("Chained patches are not supported")
            raw = decode_patch(self._object(reference), raw)
        elif row["mode"] != "full" or row["anchor"] is not None:
            raise ValueError("Unknown object mode or full object has an anchor")
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("Reconstructed account checksum differs")
        return raw

    def get(self, key: str, slot: int, position: int, order: int = LAST_ORDER) -> bytes:
        validate_cursor(self.counts, slot, position, order)
        if key not in self.index["accounts"]:
            raise CoverageError("Account is not in this captured subset; absence is unknown")
        rows = self.index["accounts"][key]
        index = bisect.bisect_right(rows, [slot, position, order, LAST_ORDER]) - 1
        if index < 0:
            raise CoverageError("Cursor precedes first known account state")
        raw = self._object(rows[index][3])
        validate_account(raw, key)
        return raw
