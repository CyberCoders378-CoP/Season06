#!/usr/bin/env python3
"""
Organizer script:
- generate a plaintext track (rows of ASCII, '.' and '#', trailing 'F's)
- ensure each column has between min_obs and max_obs obstacles over the body
- set the target column (start_x) to have exact target_count (e.g. 17)
- verify solvable from start_x
- compress + XOR-encrypt the track payload (same pattern as your loader expects)
- create encrypted_flag.bin which is XOR-encrypted with keystream derived from the integer key (target_count)
- emit a manifest.json with mapping track -> seed -> target_count
"""

import os
import json
import zlib
import random
import hashlib
from pathlib import Path
from typing import List, Tuple

W = 13           # width
ROWS = 180       # total rows including finish rows
FINISH_ROWS = 6
BODY_ROWS = ROWS - FINISH_ROWS

OUT_DIR = Path("../student/tracks")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = {}

# --------------------------
# Utility: solvability check
# --------------------------
def solvable(rows: List[str], start_x: int, finish_rows: int = FINISH_ROWS) -> bool:
    body = rows[:-finish_rows] if finish_rows else rows
    W = len(rows[0])
    reachable = {start_x}
    for row in body:
        next_reach = set()
        for col in reachable:
            for dx in (-1, 0, 1):
                nx = col + dx
                if nx < 0 or nx >= W:
                    continue
                if row[nx] == '#':
                    continue
                next_reach.add(nx)
        if not next_reach:
            return False
        reachable = next_reach
    return True

# --------------------------
# Build a plaintext track:
# - mostly empty, but ensure column counts constraints and target_count at start column
# --------------------------
def build_track_with_column_constraints(seed: int, width: int = W,
                                         body_rows: int = BODY_ROWS,
                                         finish_rows: int = FINISH_ROWS,
                                         min_obs_per_col: int = 10,
                                         max_obs_per_col: int = 20,
                                         target_col: int = 3,
                                         target_count_for_target_col: int = 17
                                         ) -> List[str]:
    r = random.Random(seed)

    # Initialize empty grid (body only)
    grid = [['.' for _ in range(width)] for _ in range(body_rows)]

    # We'll produce target counts for each column in [min_obs, max_obs]
    targets = [r.randint(min_obs_per_col, max_obs_per_col) for _ in range(width)]
    # force target for the desired column
    targets[target_col] = target_count_for_target_col

    # We must ensure that sum(targets) <= width * body_rows (obvious)
    total_needed = sum(targets)
    assert total_needed <= width * body_rows, "Too many obstacles requested"

    # Fill obstacles column-wise but randomize row positions while ensuring at least one open cell per row
    # approach: for each column, choose target_count distinct rows to mark '#'
    rows_indices = list(range(body_rows))
    for col, tcount in enumerate(targets):
        rows_choice = r.sample(rows_indices, tcount)
        for ri in rows_choice:
            grid[ri][col] = '#'

    # Now enforce: every row must have at least one '.' (i.e., not fully blocked)
    # If a row is fully '#', pick a random column and set to '.'
    for ri in range(body_rows):
        if all(c == '#' for c in grid[ri]):
            # pick a column to open (prefer columns with > min_obs to avoid breaking targets)
            candidate_cols = [c for c in range(width) if sum(1 for rr in range(body_rows) if grid[rr][c] == '#') > targets[c]]
            if not candidate_cols:
                # fallback: pick any column
                candidate_cols = list(range(width))
            col_to_open = r.choice(candidate_cols)
            grid[ri][col_to_open] = '.'

    # Recompute actual per-column counts — they may differ slightly if we opened rows above.
    col_counts = [sum(1 for ri in range(body_rows) if grid[ri][c] == '#') for c in range(width)]
    # If target column was disturbed, patch it by adding/removing obstacles
    cur_target = col_counts[target_col]
    # If too many obstacles in target_col, remove some randomly
    if cur_target > target_count_for_target_col:
        to_remove = cur_target - target_count_for_target_col
        rows_with_hash = [ri for ri in range(body_rows) if grid[ri][target_col] == '#']
        for ri in random.sample(rows_with_hash, to_remove):
            grid[ri][target_col] = '.'
    elif cur_target < target_count_for_target_col:
        # add obstacles in rows that are '.' at that col
        to_add = target_count_for_target_col - cur_target
        candidate_rows = [ri for ri in range(body_rows) if grid[ri][target_col] == '.']
        if len(candidate_rows) < to_add:
            raise RuntimeError("Cannot reach exact target count for column")
        for ri in random.sample(candidate_rows, to_add):
            grid[ri][target_col] = '#'

    # Final sanity: every row must still have at least one '.'; if not, open a random column
    for ri in range(body_rows):
        if all(grid[ri][c] == '#' for c in range(width)):
            # open a random column
            grid[ri][r.randrange(width)] = '.'

    # Build rows as strings, append finish rows 'F'*W
    rows = [''.join(grid[ri]) for ri in range(body_rows)]
    rows += ['F' * width for _ in range(finish_rows)]
    return rows

# --------------------------
# Convert rows -> payload bytes (ASCII), compress, and XOR-encrypt consistent with your loader
# --------------------------
def xor_keystream_encrypt(payload_bytes: bytes, seed_key: int) -> bytes:
    """Used for the track file format: XOR payload with pseudo-keystream derived from seed_key.
       This mirrors the loader._keystream() logic you described earlier using random.Random(seed_key)
    """
    r = random.Random(seed_key)
    ks = bytearray()
    # produce enough keystream for payload
    needed = len(payload_bytes)
    while len(ks) < needed:
        n = r.getrandbits(32)
        ks.extend(n.to_bytes(4, 'little'))
    return bytes(b ^ ks[i] for i, b in enumerate(payload_bytes))

def write_encrypted_trk(rows: List[str], fname: str, seed: int, out_dir: Path = OUT_DIR):
    width = len(rows[0])
    payload = ''.join(rows).encode('ascii')
    compressed = zlib.compress(payload, 9)
    # We will encode length of uncompressed payload (4 bytes little-endian), XOR'ed like before
    # Derive seed_key exactly the same way your loader will: (seed ^ _A ^ crc32(fname) ^ _B) & 0xffffffff
    # choose obfuscation constants consistent with your loader
    _A = 0x51A ^ 0x1
    _B = (0xDEAD << 1) ^ 0xBEEF
    import binascii
    seed_key = (seed ^ _A ^ (zlib.crc32(fname.encode()) & 0xffffffff) ^ _B) & 0xffffffff

    out = bytearray()
    sz_enc = bytes(len(payload).to_bytes(4, 'little'))
    # XOR size
    # build keystream and XOR the size + compressed payload
    r = random.Random(seed_key)
    ks = bytearray()
    # need keystream for size and compressed length
    while len(ks) < 4 + len(compressed):
        n = r.getrandbits(32)
        ks.extend(n.to_bytes(4, 'little'))
    # XOR size bytes
    for i in range(4):
        out.append(sz_enc[i] ^ ks[i])
    # XOR compressed bytes
    for i, b in enumerate(compressed):
        out.append(b ^ ks[4 + i])

    path = out_dir / fname
    path.write_bytes(bytes(out))
    return path

# --------------------------
# Flag encryption using integer key k:
# - derive SHA256(str(k)).digest() and repeat as keystream to XOR the flag bytes
# --------------------------
def encrypt_flag_with_int_key(flag_bytes: bytes, k: int) -> bytes:
    seed = hashlib.sha256(str(k).encode()).digest()
    # expand keystream to flag length
    ks = bytearray()
    while len(ks) < len(flag_bytes):
        ks.extend(hashlib.sha256(ks + seed).digest())  # chain to vary bytes
    ks = ks[:len(flag_bytes)]
    return bytes(b ^ ks[i] for i, b in enumerate(flag_bytes))

def decrypt_flag_with_int_key(cipher_bytes: bytes, k: int) -> bytes:
    return encrypt_flag_with_int_key(cipher_bytes, k)  # XOR symmetric

# --------------------------
# Top-level generator flow
# --------------------------
def make_one_track_and_encrypt_flag(seed: int, track_name: str,
                                    start_x: int = 3,
                                    min_obs_per_col: int = 10,
                                    max_obs_per_col: int = 20,
                                    target_count_for_start_col: int = 17,
                                    flag_plain: str = "PYTHON_CLUB{R04DBYT3_R4C3R}"
                                    ) -> Tuple[str, int]:
    # 1) generate rows satisfying constraints (may need to re-seed attempts until solvable)
    attempt = 0
    while True:
        attempt += 1
        rows = build_track_with_column_constraints(seed + attempt, width=W,
                                                   body_rows=BODY_ROWS,
                                                   finish_rows=FINISH_ROWS,
                                                   min_obs_per_col=min_obs_per_col,
                                                   max_obs_per_col=max_obs_per_col,
                                                   target_col=start_x,
                                                   target_count_for_target_col=target_count_for_start_col)
        if solvable(rows, start_x, FINISH_ROWS):
            break
        if attempt > 200:
            raise RuntimeError("failed to build solvable track after many attempts")

    # 2) write encrypted .trk file using the seed (choose fname)
    fname = track_name
    trkpath = write_encrypted_trk(rows, fname, seed)

    # 3) compute actual count in start column to double-check (sanity)
    body = rows[:-FINISH_ROWS]
    actual_start_count = sum(1 for r in body if r[start_x] == '#')
    assert actual_start_count == target_count_for_start_col, f"start column count mismatch: {actual_start_count}"

    # 4) encrypt flag with integer key = actual_start_count
    flag_bytes = flag_plain.encode('utf-8')
    cipher_flag = encrypt_flag_with_int_key(flag_bytes, actual_start_count)
    # write encrypted flag to file (name derived from track)
    enc_flag_name = f"{track_name}.flag.enc"
    (OUT_DIR / enc_flag_name).write_bytes(cipher_flag)

    return fname, actual_start_count

# --------------------------
# Example invocation: generate several tracks
# --------------------------
if __name__ == "__main__":
    seeds = [41017, 58321, 90011]
    names = [f"TRK_{s}.trk" for s in seeds]
    flag_text = "PYTHON_CLUB{R04DBYT3_R4C3R}"

    for s, name in zip(seeds, names):
        print(f"Generating track {name} seed={s} ...")
        fname, k = make_one_track_and_encrypt_flag(s, name, start_x=3,
                                                  min_obs_per_col=10, max_obs_per_col=20,
                                                  target_count_for_start_col=17,
                                                  flag_plain=flag_text)
        MANIFEST[fname] = {"seed": s, "start_x": 3, "key_count": k}

    # save manifest (organizer-only)
    ("manifest.json").write_text(json.dumps(MANIFEST, indent=2))
    print("Done. Manifest and encrypted flags written to", OUT_DIR)
