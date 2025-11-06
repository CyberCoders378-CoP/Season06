from __future__ import annotations
from typing import List

from Game import Game
from Target import Target


# ---------------- Data loading ----------------
def load_targets(path) -> List["Target"]:
    targets = []

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            parts = line.split()

            x, y, vx, vy = map(float, parts[0:4])
            targets.append(Target(i, x, y, vx, vy))

    return targets


def load_shots(path) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def main():
    # Load inputs
    targets = load_targets("data/rings.txt")
    instr = load_shots("data/shots.txt")

    game = Game(targets, instr)
    game.run()


if __name__ == "__main__":
    print("Hello e3b")
    main()
