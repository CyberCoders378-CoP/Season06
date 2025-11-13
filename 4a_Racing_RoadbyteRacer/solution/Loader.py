# Loader.py
"""
EP4 – Maze Navigator (Medium)
Loader: streams track rows from plaintext .trk or encrypted .trk.enc files.

Plaintext format (.trk):
- ASCII text, one row per line
- '.' = free, '#' = obstacle
- All rows must have the same width

Encrypted format (.trk.enc):
- Layout: [4-byte little-endian uncompressed size XORed] + [zlib(payload) XORed]
- Keystream: bytes from random.Random(seed_key)
- seed_key = (seed ^ _A ^ crc32(filename) ^ _B) & 0xFFFFFFFF
- payload: concatenated ASCII rows (no newlines), same width for all rows
"""

from __future__ import annotations
from pathlib import Path
from typing import Iterable, Iterator, List, Optional
import random
import zlib


# Must match generator/encryptor constants
_A = 0x51A ^ 0x1
_B = (0xDEAD << 1) ^ 0xBEEF


class Loader:
    def __init__(self, seed: int):
        """
        seed: the PRNG seed paired to this track set (used only for .trk.enc files).
        """
        self.seed = int(seed)

    # ---------- Public API ----------
    def stream_decrypt_lines(self, path: str | Path) -> Iterator[str]:
        """
        Yield rows from a .trk (plaintext) or .trk.enc (encrypted) file.
        Automatically detects the format by extension.
        """
        p = Path(path)
        if p.suffix == ".enc":
            yield from self._stream_from_encrypted(p)
        else:
            yield from self._stream_from_plaintext(p)


    # ---------- Internal helpers ----------
    def _seed_key(self, filename: str) -> int:
        return (self.seed ^ _A ^ (zlib.crc32(filename.encode()) & 0xFFFFFFFF) ^ _B) & 0xFFFFFFFF

    def _keystream(self, seed_key: int) -> Iterator[int]:
        r = random.Random(seed_key)
        while True:
            n = r.getrandbits(32)
            # little-endian 4 bytes
            b = n.to_bytes(4, "little")
            for by in b:
                yield by

    def _stream_from_encrypted(self, p: Path) -> Iterator[str]:
        """
        .trk.enc reader:
        - XOR the first 4 bytes to get uncompressed size
        - XOR the remainder and zlib.decompress
        - Split the raw payload into equal-width rows (width inferred from total size and row count)
          -> We infer width by reading the first row length from the plaintext companion if present,
             otherwise require that Engine validates widths. To keep it simple and robust, we enforce a
             fixed width discovered from the caller by slicing based on the first line length after decode.
        """
        fname = p.name
        seed_key = self._seed_key(fname)
        ks = self._keystream(seed_key)

        data = p.read_bytes()
        if len(data) < 4:
            raise ValueError(f"Encrypted file too short: {p}")

        # XOR size header
        sz_bytes = bytes([data[i] ^ next(ks) for i in range(4)])
        uncompressed_size = int.from_bytes(sz_bytes, "little")

        # XOR compressed body
        comp = bytes(b ^ next(ks) for b in data[4:])
        raw = zlib.decompress(comp)

        if len(raw) != uncompressed_size:
            raise ValueError("Size mismatch after decrypt/decompress.")

        # We don't have newlines in payload; rows are concatenated.
        # To yield rows, we must infer the width. We do this lazily:
        # - If there’s a matching plaintext .trk next to it, use its width.
        # - Otherwise, assume the first 100 rows * 10 cols (default 100x10) if divisible.
        # - If neither fits, raise for clarity.
        width = self._infer_width_from_neighbor(p) or self._infer_default_width(len(raw))
        if width is None or len(raw) % width != 0:
            raise ValueError("Unable to infer row width from encrypted payload size.")

        for i in range(0, len(raw), width):
            yield raw[i : i + width].decode("ascii")

    def _infer_width_from_neighbor(self, p: Path) -> Optional[int]:
        """
        If a plaintext sibling exists (same stem without .enc), use its first line length as width.
        """
        try_plain = p.with_suffix("")  # remove .enc suffix
        if try_plain.exists() and try_plain.is_file():
            # read first non-empty line
            with try_plain.open("r", encoding="ascii") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line:
                        return len(line)
        return None

    def _infer_default_width(self, total_bytes: int) -> Optional[int]:
        """
        Default to 10 columns if the total size fits 10 evenly (for 100x10 tracks).
        Otherwise try common widths (13 for earlier episodes), else None.
        """
        for w in (10, 13, 16):
            if total_bytes % w == 0:
                return w
        return None

    def _stream_from_plaintext(self, p: Path) -> Iterator[str]:
        """
        Read one row per line ('.' and '#'), stripping newlines and ignoring empty lines.
        Ensures consistent widths.
        """
        if not p.exists():
            raise FileNotFoundError(p)

        width: Optional[int] = None
        with p.open("r", encoding="ascii") as f:
            for line in f:
                row = line.rstrip("\n")
                if not row:
                    continue
                if width is None:
                    width = len(row)
                elif len(row) != width:
                    raise ValueError(f"Inconsistent row width in {p}: expected {width}, got {len(row)}")
                # Optional: validate characters
                # Treat only '.' and '#' as valid; ignore others defensively.
                if any(ch not in ('.', '#', 'F') for ch in row):
                    raise ValueError("Invalid characters in plaintext track.")
                yield row
