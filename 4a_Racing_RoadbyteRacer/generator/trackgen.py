#!/usr/bin/env python3
"""
ep4_tools/trackgen.py

Usage examples:
  # 1) Generate plaintext only (for debugging)
  python trackgen.py generate --name TRK_41017.trk --seed 41017

  # 2) Encrypt an existing plaintext .trk to .trk.enc
  python trackgen.py encrypt  --file ../ep4/tracks/TRK_41017.trk --seed 41017

  # 3) Do both in one go
  python trackgen.py both     --name TRK_41017.trk --seed 41017 --ensure-solvable
"""
import argparse
import os
import zlib
import random
from pathlib import Path
from typing import List

# Defaults per your spec
DEFAULT_ROWS = 100
DEFAULT_WIDTH = 10
DEFAULT_OBS_RATE = 0.25  # ~25% obstacles
FINISH_ROWS = 5          # keep 0 for now (pure 100x10 maze); change if you want trailing 'F' rows


# Obfuscation salts (must match the loader)
_A = 0x51A ^ 0x1
_B = (0xDEAD << 1) ^ 0xBEEF


# -----------------------------
# Minimal DP solvability check
# -----------------------------
def solvable_any_start(rows: List[str]) -> bool:
    """True if any start column in top row can reach bottom row by moves {-1,0,+1} on '.' cells."""
    R, C = len(rows), len(rows[0])
    reach = {c for c in range(C) if rows[0][c] == '.'}
    if not reach:
        return False

    for r in range(1, R):
        nxt = set()
        for c in reach:
            for dc in (-1, 0, 1):
                nc = c + dc
                if 0 <= nc < C and rows[r][nc] == '.':
                    nxt.add(nc)

        if not nxt:
            return False

        reach = nxt
    return True


# -----------------------------
# Grid generation (~40% '#')
# -----------------------------
def gen_grid(seed: int,
             rows: int = DEFAULT_ROWS,
             width: int = DEFAULT_WIDTH,
             obstacle_rate: float = DEFAULT_OBS_RATE,
             ensure_solvable: bool = False,
             max_tries: int = 500) -> List[str]:
    """
    Generates a 2D grid with '.' and '#'.
    - Each row has at least one '.' (never fully blocked).
    - If ensure_solvable: guarantees at least one top-to-bottom path.
    """
    r = random.Random(seed)
    for attempt in range(1, max_tries + 1):
        grid = []
        for j in range(rows):
            row = []
            for i in range(width):
                if j == 0:
                    row.append('.')
                elif j >= rows - FINISH_ROWS:
                    row.append('F')
                else:
                    row.append('#' if r.random() < obstacle_rate else '.')


            # ensure at least one open cell
            if all(ch == '#' for ch in row):
                row[r.randrange(width)] = '.'
            grid.append(''.join(row))

        if not ensure_solvable or solvable_any_start(grid):
            return grid

        # tweak seed drift for next attempt
        r.seed(seed + attempt * 10007)
    raise RuntimeError("Failed to generate a solvable grid within max_tries.")


# --------------------------------
# Plaintext .trk I/O (debuggable)
# --------------------------------
def write_plain_trk(rows: List[str], path: Path) -> None:
    """
    Writes plaintext .trk for debugging.
    One row per line, ASCII '.' and '#'.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii", newline="\n") as f:
        for row in rows:
            f.write(row + "\n")


def read_plain_trk(path: Path) -> List[str]:
    with path.open("r", encoding="ascii") as f:
        rows = [line.rstrip("\n") for line in f]
    if not rows:
        raise ValueError("Empty .trk file.")
    w = len(rows[0])
    if any(len(r) != w for r in rows):
        raise ValueError("Inconsistent row widths in .trk.")
    return rows


# -----------------------------------------
# Encryption: XOR(size+zlib(payload), KS)
# KS = bytes from random.Random(seed_key)
# seed_key = seed ^ _A ^ crc32(filename) ^ _B
# -----------------------------------------
def _seed_key(seed: int, filename: str) -> int:
    key = (seed ^ _A ^ (zlib.crc32(filename.encode()) & 0xFFFFFFFF) ^ _B) & 0xFFFFFFFF
    return key


def encrypt_trk_bytes(rows: List[str], seed: int, out_filename: str) -> bytes:
    payload = ''.join(rows).encode('ascii')
    comp = zlib.compress(payload, 9)
    key = _seed_key(seed, out_filename)
    rnd = random.Random(key)

    # produce enough keystream for 4-byte size + compressed bytes
    ks_len = 4 + len(comp)
    ks = bytearray()
    while len(ks) < ks_len:
        ks.extend(rnd.getrandbits(32).to_bytes(4, 'little'))

    out = bytearray(ks_len)
    size_le = len(payload).to_bytes(4, 'little')
    # XOR size
    for i in range(4):
        out[i] = size_le[i] ^ ks[i]
    # XOR compressed body
    for i, b in enumerate(comp, start=4):
        out[i] = b ^ ks[i]
    return bytes(out)


def write_encrypted_trk(rows: List[str], seed: int, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    blob = encrypt_trk_bytes(rows, seed, out_path.name)
    out_path.write_bytes(blob)


# --------------
# CLI handlers
# --------------
def cmd_generate(args: argparse.Namespace) -> None:
    rows = gen_grid(seed=args.seed,
                    rows=args.rows,
                    width=args.width,
                    obstacle_rate=args.rate,
                    ensure_solvable=args.ensure_solvable)
    out = Path(args.outdir) / args.name
    write_plain_trk(rows, out)
    print(f"[ok] wrote plaintext {out} ({len(rows)}x{len(rows[0])}, rate≈{args.rate:.2f})")
    if args.show_stats:
        total = len(rows) * len(rows[0])
        obs = sum(r.count('#') for r in rows)
        print(f"    obstacle cells: {obs}/{total} = {obs/total:.1%}")
        print(f"    solvable_any_start: {solvable_any_start(rows)}")


def cmd_encrypt(args: argparse.Namespace) -> None:
    src = Path(args.file)
    rows = read_plain_trk(src)
    dst = src.with_suffix(src.suffix + ".enc")
    write_encrypted_trk(rows, args.seed, dst)
    print(f"[ok] wrote encrypted {dst.name} next to {src.name}")


def cmd_both(args: argparse.Namespace) -> None:
    # generate plaintext
    rows = gen_grid(seed=args.seed,
                    rows=args.rows,
                    width=args.width,
                    obstacle_rate=args.rate,
                    ensure_solvable=args.ensure_solvable)
    base = Path(args.outdir) / args.name
    write_plain_trk(rows, base)
    print(f"[ok] wrote plaintext {base}")
    if args.show_stats:
        total = len(rows) * len(rows[0])
        obs = sum(r.count('#') for r in rows)
        print(f"    obstacle cells: {obs}/{total} = {obs/total:.1%}")
        print(f"    solvable_any_start: {solvable_any_start(rows)}")
    # encrypt separately
    enc_path = base.with_suffix(base.suffix + ".enc")
    write_encrypted_trk(rows, args.seed, enc_path)
    print(f"[ok] wrote encrypted {enc_path.name}")


# --------------
# Main / CLI
# --------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="EP4 track generator & encryptor")
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--seed", type=int, required=True, help="PRNG seed")
    common.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    common.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    common.add_argument("--rate", type=float, default=DEFAULT_OBS_RATE, help="Obstacle rate (0..1)")
    common.add_argument("--ensure-sovable", dest="ensure_solvable", action="store_true", help="Regenerate until solvable from some start")
    common.add_argument("--outdir", default="../student/tracks")
    common.add_argument("--show-stats", action="store_true")

    # generate
    g = sub.add_parser("generate", parents=[common])
    g.add_argument("--name", required=True, help="Plaintext filename, e.g., TRK_41017.trk")
    g.set_defaults(func=cmd_generate)

    # encrypt existing plaintext
    e = sub.add_parser("encrypt")
    e.add_argument("--file", required=True, help="Path to plaintext .trk")
    e.add_argument("--seed", type=int, required=True, help="Seed originally used for generation")
    e.set_defaults(func=cmd_encrypt)

    # both
    b = sub.add_parser("both", parents=[common])
    b.add_argument("--name", required=True, help="Base plaintext filename")
    b.set_defaults(func=cmd_both)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
