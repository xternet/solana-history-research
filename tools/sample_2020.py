"""Select a reproducible, quarter-stratified cohort; does not execute transactions."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


def sample(inventory: list[dict], seed: str) -> list[int]:
    """Pick 25 produced slots per quarter from a verified 2020 inventory."""
    if not seed:
        raise ValueError("A published seed is required")
    quarters = [[] for _ in range(4)]
    seen = set()
    for row in inventory:
        slot, timestamp = row["slot"], row["block_time"]
        if type(slot) is not int or slot < 0 or slot in seen:
            raise ValueError("Invalid or duplicate slot")
        if type(timestamp) is not int:
            raise ValueError("block_time must be a verified integer Unix timestamp")
        seen.add(slot)
        date = datetime.fromtimestamp(timestamp, timezone.utc)
        if date.year != 2020:
            raise ValueError("Inventory must contain only verified 2020 produced slots")
        quarters[(date.month - 1) // 3].append(slot)
    selected = []
    for quarter in quarters:
        if len(quarter) < 25:
            raise ValueError("Each quarter requires at least 25 distinct produced slots")
        ranked = sorted(quarter, key=lambda slot: (
            sha256(f"{seed}:{slot}".encode()).digest(), slot))
        selected.extend(ranked[:25])
    return sorted(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--seed", required=True)
    args = parser.parse_args()
    raw = args.inventory.read_bytes()
    result = {"schema": 1, "year": 2020, "seed": args.seed,
              "inventory_sha256": sha256(raw).hexdigest(),
              "sampling": "25 lowest SHA256(seed:slot) ranks per UTC quarter",
              "slots": sample(json.loads(raw), args.seed),
              "native_execution": "not_run"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
