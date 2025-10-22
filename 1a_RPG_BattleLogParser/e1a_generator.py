#!/usr/bin/env python3
import argparse
import random
from typing import List


POTION_LINE = "Player takes a potion, healing 100 health points."


def gen_monster_name(rng: random.Random) -> str:
    starts = ["Gr", "Sk", "Bl", "Cr", "Wr", "Th", "Gh", "Br", "Sl", "Kn", "Z", "V", "Dr", "Kr", "M", "N"]
    vowels = ["a", "e", "i", "o", "u", "y"]
    mids = ["rg", "zg", "bl", "kr", "dr", "sk", "gl", "gn", "zz", "lm", "rk", "sh", "th", "gr", "vr", "nd", "st", "mp"]
    ends = ["ling", "gore", "fang", "spawn", "wraith", "fiend", "maw", "claw", "hound", "beast",
            "drake", "ghoul", "spike", "stalker", "bane", "lurker"]
    name = rng.choice(starts) + rng.choice(vowels) + rng.choice(mids) + rng.choice(vowels) + rng.choice(ends)
    return name.capitalize()


def build_encounter_lines(monster: str, length: int, rng: random.Random) -> List[str]:
    lines: List[str] = []
    attacker = "player" if rng.random() < 0.5 else "monster"
    for _ in range(length):
        if attacker == "player":
            dmg = rng.randint(3, 15)
            lines.append(f"Player hit the {monster} for {dmg} dmg")
            attacker = "monster"
        else:
            dmg = rng.randint(2, 14)
            lines.append(f"Player took {dmg} dmg from the {monster}")
            attacker = "player"
    return lines


def plan_encounter_sizes_exact(total_lines: int, num_potions: int, min_enc: int, max_enc: int) -> List[int]:
    L = total_lines - num_potions
    if L <= 0:
        return []
    n = (L + max_enc - 1) // max_enc  # ceil(L / max_enc)
    while n * min_enc > L:
        n -= 1
    if n <= 0:
        n = 1
    base = [min_enc] * n
    remaining = L - n * min_enc
    i = 0
    while remaining > 0:
        if base[i] < max_enc:
            base[i] += 1
            remaining -= 1
        i = (i + 1) % n
    return base


def distribute_potions_even(num_encounters: int, num_potions: int) -> List[int]:
    gaps = max(0, num_encounters - 1)
    pots_after = [0] * gaps
    if gaps == 0 or num_potions == 0:
        return pots_after
    step = gaps / num_potions
    pos = 0.5 * step
    for _ in range(num_potions):
        idx = int(pos)
        if idx >= gaps:
            idx = gaps - 1
        pots_after[idx] += 1
        pos += step
    return pots_after


def generate_battle_log(lines: int = 1000,
                        potion_ratio: float = 0.05,
                        min_enc: int = 3,
                        max_enc: int = 4,
                        seed: int | None = None) -> List[str]:
    rng = random.Random(seed)
    num_potions = max(0, round(lines * potion_ratio))
    enc_sizes = plan_encounter_sizes_exact(lines, num_potions, min_enc, max_enc)
    num_encounters = len(enc_sizes)
    pots_after = distribute_potions_even(num_encounters, num_potions)
    out: List[str] = []
    for i, size in enumerate(enc_sizes):
        monster = gen_monster_name(rng)
        out.extend(build_encounter_lines(monster, size, rng))
        if i < num_encounters - 1:
            out.extend([POTION_LINE] * pots_after[i])
    assert len(out) == lines, f"Output length mismatch: {len(out)} != {lines}"
    for s in out:
        if s == POTION_LINE:
            continue
        if not (s.startswith("Player hit the ") or s.startswith("Player took ")):
            raise AssertionError(f"Unexpected line format: {s}")
    return out


def write_lines(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def parse_args():
    p = argparse.ArgumentParser(description="Generate a battle log for parsing exercises (even potion spread).")
    p.add_argument("--lines", type=int, default=1000, help="Total number of lines in the output file.")
    p.add_argument("--potion-ratio", type=float, default=0.05,
                   help="Approximate fraction of lines that are potion lines (e.g., 0.05 = 5%).")
    p.add_argument("--min-enc", type=int, default=3, help="Minimum lines per encounter.")
    p.add_argument("--max-enc", type=int, default=4, help="Maximum lines per encounter.")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    p.add_argument("--outfile", type=str, default="battle_log.txt", help="Output file path.")
    return p.parse_args()


def main():
    args = parse_args()
    if args.lines <= 0:
        raise SystemExit("--lines must be positive.")
    if not (0.0 <= args.potion_ratio < 1.0):
        raise SystemExit("--potion-ratio must be in [0.0, 1.0).")
    if args.min_enc < 1 or args.max_enc < args.min_enc:
        raise SystemExit("--min-enc must be >=1 and --max-enc must be >= --min-enc.")
    log_lines = generate_battle_log(lines=args.lines,
                                    potion_ratio=args.potion_ratio,
                                    min_enc=args.min_enc,
                                    max_enc=args.max_enc,
                                    seed=args.seed)
    write_lines(args.outfile, log_lines)
    print(f"Wrote {len(log_lines)} lines to {args.outfile}")


if __name__ == "__main__":
    main()
