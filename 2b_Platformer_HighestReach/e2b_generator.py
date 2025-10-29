#!/usr/bin/env python3
"""
gen_platformer_level.py

Generates:
  - map.txt  : grid with '#' (solid), '.' (air), 'S' (spawn)
  - commands.txt : per-frame commands at 20 FPS (default) with impulses:
        RIGHT a / LEFT a / JUMP j / WAIT

Design:
  - Tiles are implicitly 16x16 px (not rendered here).
  - Commands are per frame; thrust accumulates in YOUR simulator.
  - Short ground stumps (1–2 tiles) only; NO tall pillars.
  - Heavy bias of platforms close to the ground for reachability.
  - Safe runway next to spawn.

Usage:
  python gen_platformer_level.py --width 64 --height 20 --seconds 40 --seed 7 \
      --out-map map.txt --out-cmd commands.txt
"""

import argparse
import random

# ====== Command stream parameters (tuned for 20 FPS) ======
FPS_DEFAULT = 20
RIGHT_THRUST = 1.6
LEFT_THRUST  = 1.6
JUMP_FORCE   = 5.0  # one-frame pulse; your sim should ignore if not on_ground

RUN_MIN, RUN_MAX = 20, 80          # run motif lengths (frames)
COAST_MIN, COAST_MAX = 10, 50      # coast motif lengths (frames)
HOP_NEUTRAL_BEFORE = 5
HOP_NEUTRAL_AFTER  = 10

MOTIF_WEIGHTS = {
    "run_right":  0.36,
    "run_left":   0.18,
    "coast":      0.18,
    "hop":        0.10,
    "burst_turn": 0.10,
    "stair_climb_intent": 0.08,
}

RUN_JUMP_CHANCE = 0.18
RUN_JUMP_COOLDOWN = (FPS_DEFAULT // 2)

# ====== Map generation params ======
DEFAULT_WIDTH  = 64
DEFAULT_HEIGHT = 20
DEFAULT_PLATFORMS = 14   # additional mid/high platforms (optional spice)

MIN_PLATFORM_LEN = 3
MAX_PLATFORM_LEN = 11

# Low platform band relative to ground
LOW_ROW_MIN_OFFSET = 2     # ground_y - 2 (closest to ground)
LOW_ROW_MAX_OFFSET = 6     # ground_y - 6 (upper bound of "low")
LOW_PLATFORM_TARGET =  max(10, DEFAULT_WIDTH // 2)  # lots of short low ledges

# Short stumps on ground
STUMPS_PER_WIDTH = 14      # one stump per ~14 columns
STUMP_MIN_H, STUMP_MAX_H = 1, 2


def gen_map(width: int, height: int, ground_y: int, platforms: int, rng: random.Random) -> list[str]:
    """Generate rectangular grid with ground, low platforms, short stumps, and a spawn runway."""
    assert width >= 8 and height >= 8
    grid = [["." for _ in range(width)] for _ in range(height)]

    # Ground
    ground_y = ground_y if 0 <= ground_y < height else height - 1
    for c in range(width):
        grid[ground_y][c] = "#"

    # ---- Short ground stumps (no tall pillars) ----
    num_stumps = max(0, width // STUMPS_PER_WIDTH)
    for _ in range(num_stumps):
        c = rng.randrange(3, width - 3)
        # Keep space from neighbors to avoid fused lumps
        if any(grid[ground_y - 1][cc] == "#" for cc in (c - 1, c, c + 1)):
            continue
        h = rng.randint(STUMP_MIN_H, STUMP_MAX_H)  # small bump 1–2 high
        for r in range(ground_y - h, ground_y):
            if 0 <= r < height:
                grid[r][c] = "#"

    # ---- Dense low-altitude platforms (2–6 above ground), biased low ----
    offsets = list(range(LOW_ROW_MIN_OFFSET, LOW_ROW_MAX_OFFSET + 1))
    # weights: more near ground (e.g., 6->1 pattern)
    weights = [max(1, (LOW_ROW_MAX_OFFSET + 1 - o)) for o in offsets]
    weight_sum = sum(weights)

    def pick_low_row() -> int:
        t = rng.randrange(weight_sum)
        s = 0
        for o, w in zip(offsets, weights):
            s += w
            if t < s:
                return ground_y - o
        return ground_y - offsets[0]

    def can_place_segment(r: int, c0: int, length: int) -> bool:
        if r <= 0 or r >= height - 1:
            return False
        if c0 < 1 or c0 + length >= width - 1:
            return False
        for c in range(c0, c0 + length):
            if grid[r][c] == "#":
                return False
            if r - 1 >= 0 and grid[r - 1][c] == "#":  # avoid ceilings directly above
                return False
        return True

    placed_low = 0
    attempts = LOW_PLATFORM_TARGET * 4
    while placed_low < LOW_PLATFORM_TARGET and attempts > 0:
        attempts -= 1
        r = pick_low_row()
        seg_len = rng.randint(3, 8)
        c_start = rng.randint(1, width - seg_len - 2)
        if can_place_segment(r, c_start, seg_len):
            for c in range(c_start, c_start + seg_len):
                grid[r][c] = "#"
            placed_low += 1

    # ---- Optional: some mid/high platforms for variety (sparser) ----
    if platforms > 0:
        attempts = platforms * 3
        placed = 0
        row_min = 2
        row_max = max(ground_y - (LOW_ROW_MAX_OFFSET + 2), row_min)
        while placed < platforms and attempts > 0 and row_max > row_min:
            attempts -= 1
            r = rng.randint(row_min, row_max)
            length = rng.randint(MIN_PLATFORM_LEN, MAX_PLATFORM_LEN)
            c_start = rng.randint(1, width - length - 2)
            if can_place_segment(r, c_start, length):
                for c in range(c_start, c_start + length):
                    grid[r][c] = "#"
                placed += 1

    # ---- Spawn pocket near ground with safe runway ----
    spawn_row = ground_y - 1
    spawn_col = 2
    # clear space around spawn
    for rr in [spawn_row, spawn_row - 1]:
        if 0 <= rr < height:
            for cc in range(spawn_col - 1, spawn_col + 3):
                if 0 <= cc < width:
                    grid[rr][cc] = "."

    grid[spawn_row][spawn_col] = "S"

    # Safe runway to the right of spawn (momentum build-up)
    lane_width = 12
    for rr in range(spawn_row - 2, spawn_row + 1):
        if 0 <= rr < height:
            for cc in range(spawn_col, min(spawn_col + lane_width, width - 1)):
                grid[rr][cc] = "."

    return ["".join(row) for row in grid]


# ====== Command motifs ======
def emit_run(direction: str, length: int, rng: random.Random) -> list[str]:
    thrust = RIGHT_THRUST if direction == "right" else LEFT_THRUST
    op = "RIGHT" if direction == "right" else "LEFT"
    cmds = []
    since_jump = RUN_JUMP_COOLDOWN
    for _ in range(length):
        if since_jump >= RUN_JUMP_COOLDOWN and rng.random() < RUN_JUMP_CHANCE:
            cmds.append(f"JUMP {JUMP_FORCE:.2f}")
            since_jump = 0
        else:
            cmds.append(f"{op} {thrust:.2f}")
            since_jump += 1
    return cmds


def emit_coast(length: int) -> list[str]:
    return ["WAIT"] * length


def emit_hop() -> list[str]:
    cmds = ["WAIT"] * HOP_NEUTRAL_BEFORE
    cmds.append(f"JUMP {JUMP_FORCE:.2f}")
    cmds += ["WAIT"] * HOP_NEUTRAL_AFTER
    return cmds


def emit_burst_turn(rng: random.Random) -> list[str]:
    if rng.random() < 0.5:
        burst = [f"LEFT {LEFT_THRUST:.2f}"] * rng.randint(5, 12)
    else:
        burst = [f"RIGHT {RIGHT_THRUST:.2f}"] * rng.randint(5, 12)
    return burst + emit_coast(rng.randint(COAST_MIN, COAST_MAX))


def emit_stair_climb_intent(rng: random.Random) -> list[str]:
    cmds = []
    for _ in range(rng.randint(2, 5)):
        run_len = rng.randint(RUN_MIN // 2, RUN_MAX // 2)
        cmds += [f"RIGHT {RIGHT_THRUST:.2f}"] * run_len
        cmds += ["WAIT"] * rng.randint(2, 5)
        cmds.append(f"JUMP {JUMP_FORCE:.2f}")
        cmds += ["WAIT"] * rng.randint(3, 8)
    return cmds


def pick_motif(rng: random.Random) -> str:
    total = sum(MOTIF_WEIGHTS.values())
    x = rng.random() * total
    s = 0.0
    for k, w in MOTIF_WEIGHTS.items():
        s += w
        if x <= s:
            return k
    return "run_right"


def build_command_stream(total_frames: int, rng: random.Random, fps: int) -> list[str]:
    cmds: list[str] = []
    while len(cmds) < total_frames:
        motif = pick_motif(rng)
        if motif == "run_right":
            cmds += emit_run("right", rng.randint(RUN_MIN, RUN_MAX), rng)
        elif motif == "run_left":
            cmds += emit_run("left", rng.randint(max(5, RUN_MIN // 2), RUN_MAX // 2), rng)
        elif motif == "coast":
            cmds += emit_coast(rng.randint(COAST_MIN, COAST_MAX))
        elif motif == "hop":
            cmds += emit_hop()
        elif motif == "burst_turn":
            cmds += emit_burst_turn(rng)
        elif motif == "stair_climb_intent":
            cmds += emit_stair_climb_intent(rng)
        else:
            cmds += emit_coast(rng.randint(10, 20))
    return cmds[:total_frames]


# ====== CLI / main ======
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate platformer grid and per-frame commands.")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--ground-y", type=int, default=-1, help="Row index for ground (default: height-1)")
    parser.add_argument("--platforms", type=int, default=DEFAULT_PLATFORMS, help="Extra mid/high platforms (optional)")
    parser.add_argument("--seconds", type=int, default=30, help="Duration of command stream")
    parser.add_argument("--fps", type=int, default=FPS_DEFAULT, help="Frames per second")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--out-map", type=str, default="map.txt")
    parser.add_argument("--out-cmd", type=str, default="commands.txt")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fps = max(1, args.fps)
    total_frames = max(1, args.seconds * fps)
    ground_y = args.ground_y if args.ground_y >= 0 else (args.height - 1)

    grid_lines = gen_map(args.width, args.height, ground_y, args.platforms, rng)
    cmds = build_command_stream(total_frames, rng, fps)

    with open(args.out_map, "w", encoding="utf-8") as f:
        f.write("\n".join(grid_lines) + "\n")

    with open(args.out_cmd, "w", encoding="utf-8") as f:
        for line in cmds:
            f.write(line + "\n")

    print(f"Wrote {args.out_map} ({args.width}x{args.height}, ground_y={ground_y}) "
          f"and {args.out_cmd} ({total_frames} frames @ {fps} FPS).")


if __name__ == "__main__":
    main()
