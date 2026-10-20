"""Extract a bounded account cohort from an operator-supplied native capture.

Optional local utility: not needed to run the included fixture. Reads native
base/journal/reference files; does not download a snapshot or run a validator.
"""

import argparse
import base64
from collections import Counter
import difflib
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from history_poc.store import address  # noqa: E402

TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
ROOT = Path(__file__).resolve().parents[1]


def source_records(path: Path, journal: bool = False):
    with path.open("rb") as stream:
        total = os.fstat(stream.fileno()).st_size
        ordinal = 0
        while stream.tell() < total:
            position = -2
            if journal:
                signed = stream.read(8)
                if len(signed) != 8:
                    raise ValueError("Truncated journal position")
                position = struct.unpack("<q", signed)[0]
            header = stream.read(89)
            if len(header) != 89:
                raise ValueError("Truncated account header")
            size = int.from_bytes(header[81:89], "little")
            if size > 64 * 1024**2 or stream.tell() + size > total:
                raise ValueError("Source account length exceeds file or safety bound")
            if size <= 512:
                yield position, ordinal, header + stream.read(size)
            else:
                stream.seek(size, os.SEEK_CUR)
            ordinal += 1


def extract(capture: Path, slots: list[int], count: int) -> dict:
    if not 1 <= count <= 16 or len(slots) != 2 or slots[1] != slots[0] + 1:
        raise ValueError("Use two contiguous cached slots and at most16accounts")
    candidates = {}
    first = capture / str(slots[0]) / "repeat-0"
    for _position, _order, raw in source_records(first / "accounts/base.bin"):
        if (
            len(raw) == 254
            and int.from_bytes(raw[32:40], "little") > 0
            and address(raw[48:80]) == TOKEN_PROGRAM
            and raw[197] in (1, 2)
        ):
            candidates[raw[:32]] = raw
    events = {
        key: [{"slot": slots[0], "position": -2, "order": 0, "raw": raw}]
        for key, raw in candidates.items()
    }
    current = dict(candidates)
    changes = Counter()
    counts = {}
    sources = []
    for slot in slots:
        directory = capture / str(slot) / "repeat-0"
        reference = (directory / "transactions.reference.json").read_bytes()
        counts[str(slot)] = len(json.loads(reference))
        sources.append(
            {"slot": slot, "transaction_reference_sha256": hashlib.sha256(reference).hexdigest()}
        )
        if slot != slots[0]:
            for _position, _order, raw in source_records(directory / "accounts/base.bin"):
                if raw[:32] in current and current[raw[:32]] != raw:
                    raise ValueError("Contiguous source account boundary mismatch")
        for position, order, raw in source_records(directory / "accounts/journal.bin", True):
            key = raw[:32]
            if key in candidates:
                if not -1 <= position <= counts[str(slot)]:
                    raise ValueError("Journal position outside complete slot")
                changes[key] += int(raw != current[key])
                current[key] = raw
                events[key].append(
                    {"slot": slot, "position": position, "order": order + 1, "raw": raw}
                )
    keys = sorted(
        (key for key in candidates if changes[key] >= 2), key=lambda key: (-changes[key], key)
    )[:count]
    if len(keys) != count:
        raise ValueError("Insufficient real repeated-change token-account fixtures")
    accounts = []
    for key in keys:
        versions = []
        for event in events[key]:
            raw = event["raw"]
            versions.append(
                {
                    "slot": event["slot"],
                    "position": event["position"],
                    "order": event["order"],
                    "raw_base64": base64.b64encode(raw).decode(),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
        accounts.append({"address": address(key), "versions": versions})
    return {
        "schema": "solana-account-history-fixture/v1",
        "network": "mainnet-beta",
        "coverage": {
            "first_slot": slots[0],
            "last_slot": slots[-1],
            "slot_transaction_counts": counts,
        },
        "scope": "Small account subset exported from a private local mainnet replay capture; provenance hashes only, not independently verified on-chain",
        "source": {
            "runtime": "Agave4.3.0 local native replay capture",
            "records": sources,
            "account_encoding": "32Bkey,u64lamports,u64rentEpoch,32Bowner,u8executable,u64dataLength,data; little-endian",
            "ordering": "position -2=before initialization; -1=automatic initialization;0..n-1=post transaction;n=final phase; order is a per-slot callback number from one run, only meaningful between same-account writes at the same position",
            "proof_limit": "Private source captures are not distributed; hashes alone do not allow independent on-chain provenance verification or provide a consensus account proof",
        },
        "accounts": accounts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--slots", type=int, nargs=2, required=True)
    parser.add_argument("--accounts", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--patch", action="store_true")
    args = parser.parse_args()
    output = json.dumps(extract(args.capture, args.slots, args.accounts), indent=2) + "\n"
    if args.patch:
        try:
            name = args.output.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            parser.error("--patch output must be inside the project directory")
        before = args.output.read_text() if args.output.exists() else ""
        print(
            "".join(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    output.splitlines(keepends=True),
                    fromfile="a/" + name,
                    tofile="b/" + name,
                )
            ),
            end="",
        )
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            stream.write(output)


if __name__ == "__main__":
    main()
