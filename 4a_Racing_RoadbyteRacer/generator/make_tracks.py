# ep4_tools/make_tracks.py
import os, zlib, random, itertools
from pathlib import Path


W, H_LEN = 13, 180  # 180 rows long
FINISH_ROWS = 6


def gen_track(seed: int) -> bytes:
    r = random.Random(seed)
    rows = []
    open_cols = [W//2]  # maintain a “racing lane” that wiggles
    for y in range(H_LEN - FINISH_ROWS):
        lane = open_cols[-1] + r.choice([-1,0,1])
        lane = max(1, min(W-2, lane))
        open_cols.append(lane)
        row = ['#']*W
        row[lane] = '.'
        # add occasional widening
        if r.random() < 0.35:
            row[lane-1] = '.'
        if r.random() < 0.35:
            row[lane+1] = '.'
        rows.append(''.join(row))
    rows += ['F'*W]*FINISH_ROWS
    return ''.join(rows).encode('ascii')


def encrypt_track(payload: bytes, seed: int, fname: str) -> bytes:
    comp = zlib.compress(payload, 9)
    # mimic loader-derived keystream key
    import zlib, random
    _A = 0x51A ^ 0x1
    _B = (0xDEAD << 1) ^ 0xBEEF
    key = (seed ^ _A ^ zlib.crc32(fname.encode()) ^ _B) & 0xFFFFFFFF
    r = random.Random(key)

    def ks():
        while True:
            n = r.getrandbits(32)
            yield from n.to_bytes(4, 'little')

    k = ks()
    out = bytearray()
    sz = len(payload).to_bytes(4, 'little')
    out += bytes([b ^ next(k) for b in sz])
    out += bytes(b ^ next(k) for b in comp)
    return bytes(out)


def main():
    out_dir = Path("../student/tracks")
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = [41017, 58321, 90011]
    for s in seeds:
        fname = f"TRK_{s}.trk"
        raw = gen_track(s)
        enc = encrypt_track(raw, s, fname)
        (out_dir / fname).write_bytes(enc)
    print("Tracks written.")


if __name__ == "__main__":
    main()
