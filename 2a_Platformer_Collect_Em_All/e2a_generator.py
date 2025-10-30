#!/usr/bin/env python3
"""
Generate a grid-based platformer level and a sequence of moves.

Outputs:
- level.txt : grid using characters (# wall, . empty, C coin, P player)
- moves.txt : one of U/D/L/R per line

Features:
- Reproducible with --seed
- Fixed border walls for clean levels
- Adjustable interior wall/coin density
- Optional reachability check to ensure all coins are reachable from P
- Moves generated as a bounded random walk that avoids walls/out-of-bounds
"""

import argparse
import random
from typing import List, Tuple, Optional, Iterable
from collections import deque


Tile = str
Grid = List[List[Tile]]
Pos = Tuple[int, int]


# -------------------------------
# Grid helpers
# -------------------------------
def make_empty_grid(rows: int, cols: int) -> Grid:
    grid: Grid = []
    for _ in range(rows):
        grid.append(["."] * cols)
    return grid


def add_border_walls(grid: Grid) -> None:
    rows, cols = len(grid), len(grid[0])
    for c in range(cols):
        grid[0][c] = "#"
        grid[rows - 1][c] = "#"
    for r in range(rows):
        grid[r][0] = "#"
        grid[r][cols - 1] = "#"


def place_player(grid: Grid, rng: random.Random) -> Pos:
    rows, cols = len(grid), len(grid[0])
    attempts = 0
    while True:
        r = rng.randint(1, rows - 2)
        c = rng.randint(1, cols - 2)
        if grid[r][c] == ".":
            grid[r][c] = "P"
            return (r, c)
        attempts += 1
        if attempts > 10_000:
            raise RuntimeError("Could not place player 'P' on an empty tile.")


def sprinkle_tiles(
    grid: Grid,
    rng: random.Random,
    coin_ratio: float,
    wall_ratio: float,
    forbid_positions: Optional[Iterable[Pos]] = None,
) -> None:
    """Fill interior with coins and walls according to ratios (independent Bernoulli).
    Border is untouched here; call add_border_walls() separately.
    """
    rows, cols = len(grid), len(grid[0])
    forbidden = set(forbid_positions or [])
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if (r, c) in forbidden:
                continue
            # Only modify if currently empty
            if grid[r][c] != ".":
                continue
            x = rng.random()
            if x < wall_ratio:
                grid[r][c] = "#"
            elif x < wall_ratio + coin_ratio:
                grid[r][c] = "C"
            # else leave as "."


def count_coins(grid: Grid) -> int:
    return sum(ch == "C" for row in grid for ch in row)


def neighbors4(grid: Grid, r: int, c: int) -> List[Pos]:
    out: List[Pos] = []
    if r > 0: out.append((r - 1, c))
    if r + 1 < len(grid): out.append((r + 1, c))
    if c > 0: out.append((r, c - 1))
    if c + 1 < len(grid[0]): out.append((r, c + 1))
    return out


def bfs_reachable_from(grid: Grid, start: Pos) -> set:
    q: deque[Pos] = deque([start])
    seen = {start}
    while q:
        r, c = q.popleft()
        for nr, nc in neighbors4(grid, r, c):
            if (nr, nc) in seen:
                continue
            if grid[nr][nc] == "#":
                continue
            seen.add((nr, nc))
            q.append((nr, nc))
    return seen


def ensure_all_coins_reachable(grid: Grid, start: Pos, rng: random.Random, max_passes: int = 20_000) -> None:
    """If a coin is unreachable, randomly knock down walls along a naive approach:
    repeatedly open a random interior wall adjacent to any reachable cell until all coins are reachable
    or we hit a pass limit.
    """
    rows, cols = len(grid), len(grid[0])
    passes = 0
    while True:
        reachable = bfs_reachable_from(grid, start)
        # Collect all coin positions
        coins = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == "C"]
        if all(pos in reachable for pos in coins):
            return  # all reachable
        # Find candidate walls touching the reachable region to knock down
        candidates: List[Pos] = []
        for r, c in reachable:
            for nr, nc in neighbors4(grid, r, c):
                if 0 < nr < rows - 1 and 0 < nc < cols - 1 and grid[nr][nc] == "#":
                    candidates.append((nr, nc))
        if not candidates:
            # fallback: open a random interior wall
            interior_walls = [(r, c) for r in range(1, rows - 1) for c in range(1, cols - 1) if grid[r][c] == "#"]
            if not interior_walls:
                return
            r, c = rng.choice(interior_walls)
            grid[r][c] = "."
        else:
            r, c = rng.choice(candidates)
            grid[r][c] = "."
        passes += 1
        if passes > max_passes:
            # Give up; level stays as-is (rare for reasonable ratios)
            return


# -------------------------------
# Moves generation
# -------------------------------
DIRS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}
DIR_LIST = ["U", "D", "L", "R"]


def legal(grid: Grid, r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] != "#"


def find_player(grid: Grid) -> Pos:
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "P":
                return (r, c)

    raise ValueError("No 'P' in grid")


def generate_moves_random_walk(
    grid: Grid,
    rng: random.Random,
    n_moves: int,
    bias_backtrack: float = 0.15,
) -> List[str]:
    """
    Generate moves that try to stay in-bounds and avoid walls via a simple random walk:
    - prefer continuing direction or gentle backtrack with small probability
    - if next step is illegal, pick a random legal direction
    """
    r, c = find_player(grid)
    moves: List[str] = []
    last_dir: Optional[str] = None

    for _ in range(n_moves):
        candidates = list(DIR_LIST)

        if last_dir and rng.random() < bias_backtrack:
            # occasionally backtrack for variety
            back = {"U": "D", "D": "U", "L": "R", "R": "L"}[last_dir]
            preferred_order = [back] + [d for d in DIR_LIST if d != back]
        elif last_dir and rng.random() < 0.55:
            # often keep moving forward
            preferred_order = [last_dir] + [d for d in DIR_LIST if d != last_dir]
        else:
            rng.shuffle(candidates)
            preferred_order = candidates

        chosen = None
        for d in preferred_order:
            dr, dc = DIRS[d]
            nr, nc = r + dr, c + dc
            if legal(grid, nr, nc):
                chosen = d
                r, c = nr, nc
                break

        if chosen is None:
            # stuck? choose any legal neighbor; if none, stay put by repeating last_dir or 'U'
            legal_dirs = []
            for d in DIR_LIST:
                dr, dc = DIRS[d]
                if legal(grid, r + dr, c + dc):
                    legal_dirs.append(d)
            if legal_dirs:
                chosen = rng.choice(legal_dirs)
                dr, dc = DIRS[chosen]
                r, c = r + dr, c + dc
            else:
                chosen = last_dir or "U"  # simulator will ignore illegal, but we try to avoid it

        moves.append(chosen)
        last_dir = chosen

    return moves


# -------------------------------
# I/O
# -------------------------------
def write_grid(path: str, grid: Grid) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in grid:
            f.write("".join(row) + "\n")


def write_moves(path: str, moves: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for m in moves:
            f.write(m + "\n")


# -------------------------------
# Generation pipeline
# -------------------------------
def generate_level(
    rows: int,
    cols: int,
    coin_ratio: float,
    wall_ratio: float,
    ensure_reachable: bool,
    rng: random.Random,
) -> Grid:
    if rows < 3 or cols < 3:
        raise ValueError("nb_rows and nb_cols must be >= 3")
    grid = make_empty_grid(rows, cols)
    add_border_walls(grid)

    # Temporarily place P to reserve a spot, then sprinkle tiles avoiding that spot
    pr, pc = rows // 2, cols // 2  # center-ish
    if grid[pr][pc] == "#":
        pr, pc = pr - 1, pc - 1
    grid[pr][pc] = "P"

    sprinkle_tiles(grid, rng, coin_ratio=coin_ratio, wall_ratio=wall_ratio, forbid_positions=[(pr, pc)])

    # Optionally ensure all coins are reachable from P
    if ensure_reachable and count_coins(grid) > 0:
        ensure_all_coins_reachable(grid, (pr, pc), rng=rng)

    # If P was accidentally boxed in (rare), relocate to a random empty interior
    if not any(grid[nr][nc] != "#" for nr, nc in neighbors4(grid, pr, pc)):
        grid[pr][pc] = "."
        place_player(grid, rng)

    return grid


# -------------------------------
# CLI
# -------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate level.txt and moves.txt for the platformer challenge.")
    p.add_argument("--nb_rows", type=int, default=10, help="Grid nb_rows (e.g., 100)")
    p.add_argument("--nb_cols", type=int, default=12, help="Grid nb_cols (e.g., 100)")
    p.add_argument("--coin-ratio", type=float, default=0.08, help="Probability a cell is a coin C (interior only)")
    p.add_argument("--wall-ratio", type=float, default=0.06, help="Probability a cell is a wall # (interior only)")
    p.add_argument("--ensure-reachable", action="store_true", help="Carve walls until all coins are reachable from P")
    p.add_argument("--moves", type=int, default=200, help="Number of moves to generate (e.g., 1000)")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    p.add_argument("--level-out", type=str, default="./data/level.txt", help="Output path for the grid")
    p.add_argument("--moves-out", type=str, default="./data/moves.txt", help="Output path for moves")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    grid = generate_level(
        rows=args.rows,
        cols=args.cols,
        coin_ratio=args.coin_ratio,
        wall_ratio=args.wall_ratio,
        ensure_reachable=args.ensure_reachable,
        rng=rng,
    )

    moves = generate_moves_random_walk(
        grid=grid,
        rng=rng,
        n_moves=args.moves,
        bias_backtrack=0.15,
    )

    write_grid(args.level_out, grid)
    write_moves(args.moves_out, moves)

    # Quick summary
    coins = count_coins(grid)
    pr, pc = find_player(grid)
    print(f"Generated {args.level_out} ({args.rows}x{args.cols}), coins: {coins}, player at: ({pr},{pc})")
    print(f"Generated {args.moves_out} with {args.moves} moves")
    if args.seed is not None:
        print(f"Seed: {args.seed}")


if __name__ == "__main__":
    main()
