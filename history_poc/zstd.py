"""Minimal bounded binding to the system Zstandard library."""

import ctypes
import ctypes.util

MAX_FRAME_BYTES = 8 * 1024**2


class Zstd:
    def __init__(self) -> None:
        library = ctypes.util.find_library("zstd")
        if library is None:
            raise RuntimeError("Zstandard shared library is required; install libzstd")
        self.lib = ctypes.CDLL(library)
        signatures = {
            "ZSTD_compressBound": ([ctypes.c_size_t], ctypes.c_size_t),
            "ZSTD_isError": ([ctypes.c_size_t], ctypes.c_uint),
            "ZSTD_getFrameContentSize": ([ctypes.c_void_p, ctypes.c_size_t], ctypes.c_ulonglong),
            "ZSTD_compress": (
                [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int],
                ctypes.c_size_t,
            ),
            "ZSTD_decompress": (
                [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t],
                ctypes.c_size_t,
            ),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.lib, name)
            function.argtypes = arguments
            function.restype = result

    def compress(self, raw: bytes, level: int = 3) -> bytes:
        if type(level) is not int or not 1 <= level <= 15:
            raise ValueError("Example compression level must be an integer from 1 to 15")
        if not 0 < len(raw) <= MAX_FRAME_BYTES:
            raise ValueError("Raw frame is empty or exceeds the example's 8MiB bound")
        target = ctypes.create_string_buffer(self.lib.ZSTD_compressBound(len(raw)))
        size = self.lib.ZSTD_compress(target, len(target), raw, len(raw), level)
        if self.lib.ZSTD_isError(size):
            raise ValueError("Zstandard compression failed")
        return target.raw[:size]

    def decompress(self, packed: bytes) -> bytes:
        expected = self.lib.ZSTD_getFrameContentSize(packed, len(packed))
        if not 0 < expected <= MAX_FRAME_BYTES:
            raise ValueError("Unknown, empty or oversized Zstandard frame")
        target = ctypes.create_string_buffer(expected)
        size = self.lib.ZSTD_decompress(target, expected, packed, len(packed))
        if self.lib.ZSTD_isError(size) or size != expected:
            raise ValueError("Zstandard decompression failed or size differs")
        return target.raw[:size]
