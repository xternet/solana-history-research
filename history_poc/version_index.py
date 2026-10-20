"""Offline pointer-index experiment; not a coverage validator or network router.

The original benchmark's delta-varint format is retained. Blocks now split at
shard changes and directory searches use the complete (slot, position, order).
"""

import bisect
from dataclasses import dataclass

BLOCK_ROWS = 32
MAX_U64 = 2**64 - 1


@dataclass(frozen=True)
class Version:
    slot: int
    position: int
    order: int
    object_id: int
    kind: int
    shard: int

    @property
    def cursor(self) -> tuple[int, int, int]:
        return self.slot, self.position, self.order


def validate(row: Version) -> None:
    for value in (row.slot, row.order, row.object_id, row.kind, row.shard):
        if type(value) is not int or not 0 <= value <= MAX_U64:
            raise ValueError("Pointer fields must be unsigned 64-bit integers")
    if type(row.position) is not int or not -2 <= row.position < 2**63 or row.kind > 1:
        raise ValueError("Invalid pointer position/source kind")


def uvar(value: int) -> bytes:
    if not 0 <= value <= MAX_U64:
        raise ValueError("Varint exceeds unsigned 64-bit bounds")
    output = bytearray()
    while value >= 128:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)


def read_u(raw: bytes, offset: int) -> tuple[int, int]:
    start, value = offset, 0
    for shift in range(0, 70, 7):
        if offset >= len(raw):
            raise ValueError("Truncated varint")
        byte = raw[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            if value > MAX_U64 or raw[start:offset] != uvar(value):
                raise ValueError("Noncanonical or oversized varint")
            return value, offset
    raise ValueError("Oversized varint")


def encode_block(rows: list[Version]) -> bytes:
    if not 1 <= len(rows) <= BLOCK_ROWS:
        raise ValueError("Pointer block must contain 1–32 versions")
    output = bytearray()
    previous_slot, previous_position = 0, 0
    for index, row in enumerate(rows):
        validate(row)
        if row.shard != rows[0].shard or (index and row.cursor <= rows[index - 1].cursor):
            raise ValueError("Pointer block crosses shards or has unordered/duplicate cursors")
        delta = row.position - previous_position if row.slot == previous_slot else row.position
        output.extend(uvar(row.slot - previous_slot))
        output.extend(uvar((delta << 1) ^ (delta >> 63)))
        output.extend(uvar(row.order) + uvar(row.object_id) + bytes([row.kind]))
        previous_slot, previous_position = row.slot, row.position
    return bytes(output)


def decode_block(raw: bytes, count: int, shard: int) -> list[Version]:
    if type(count) is not int or not 1 <= count <= BLOCK_ROWS:
        raise ValueError("Invalid pointer block row count")
    rows = []
    offset, slot, position = 0, 0, 0
    for _ in range(count):
        delta, offset = read_u(raw, offset)
        signed, offset = read_u(raw, offset)
        position = ((signed >> 1) ^ -(signed & 1)) + (position if delta == 0 else 0)
        slot += delta
        order, offset = read_u(raw, offset)
        object_id, offset = read_u(raw, offset)
        if offset >= len(raw):
            raise ValueError("Truncated pointer kind")
        rows.append(Version(slot, position, order, object_id, raw[offset], shard))
        offset += 1
    if offset != len(raw) or encode_block(rows) != raw:
        raise ValueError("Pointer block length or canonical encoding differs")
    return rows


@dataclass(frozen=True)
class Block:
    first: tuple[int, int, int]
    count: int
    shard: int
    raw: bytes


class VersionIndex:
    """Global key directory over sorted pointer rows from all supplied shards.

    None means before the first supplied version, NOT proven account absence.
    Source completeness and account payload validation are separate concerns.
    """

    def __init__(self, histories: dict[str, list[Version]]) -> None:
        self.blocks: dict[str, list[Block]] = {}
        self.starts: dict[str, list[tuple[int, int, int]]] = {}
        for key, rows in histories.items():
            if not rows:
                raise ValueError("Empty account pointer history")
            blocks = []
            offset = 0
            for index, row in enumerate(rows):
                validate(row)
                if index and row.cursor <= rows[index - 1].cursor:
                    raise ValueError("Pointer history must be strictly ordered")
                if index > offset and (
                    index - offset == BLOCK_ROWS or row.shard != rows[offset].shard
                ):
                    part = rows[offset:index]
                    blocks.append(
                        Block(part[0].cursor, len(part), part[0].shard, encode_block(part))
                    )
                    offset = index
            part = rows[offset:]
            blocks.append(Block(part[0].cursor, len(part), part[0].shard, encode_block(part)))
            self.blocks[key] = blocks
            self.starts[key] = [block.first for block in blocks]

    def lookup(self, key: str, cursor: tuple[int, int, int]) -> Version | None:
        validate(Version(*cursor, 0, 0, 0))
        index = bisect.bisect_right(self.starts[key], cursor) - 1
        if index < 0:
            return None
        block = self.blocks[key][index]
        rows = decode_block(block.raw, block.count, block.shard)
        return next(row for row in reversed(rows) if row.cursor <= cursor)
