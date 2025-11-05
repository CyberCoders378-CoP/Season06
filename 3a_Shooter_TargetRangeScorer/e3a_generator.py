import random
import math
from typing import List, Tuple

WORLD_MIN = -1000
WORLD_MAX = 1000

# Radii generation ranges (you can tweak these to change density/fit rate)
R1_MIN, R1_MAX = 2.0, 5.0
R2_ADD_MIN, R2_ADD_MAX = 5.0, 10.0
R3_ADD_MIN, R3_ADD_MAX = 10.0, 20.0

# Placement controls
MIN_GAP = 5.0          # extra clearance between outer rings (in world units)
CENTER_ATTEMPTS = 2000 # attempts per radii set to find a non-overlapping center
RADII_REGEN_MAX = 25   # times we allow re-rolling radii if placement fails

def gen_radii() -> Tuple[float, float, float]:
    R1 = round(random.uniform(R1_MIN, R1_MAX), 1)
    R2 = round(R1 + random.uniform(R2_ADD_MIN, R2_ADD_MAX), 1)
    R3 = round(R2 + random.uniform(R3_ADD_MIN, R3_ADD_MAX), 1)
    return R1, R2, R3

def non_overlapping_center(
    R3: float, placed: List[Tuple[int, int, float]], min_gap: float
) -> Tuple[int, int]:
    """
    Try to find a (cx, cy) in the world such that the circle with radius R3
    doesn't overlap any existing target's outer circle, considering min_gap.
    Returns (cx, cy) or raises ValueError if not found after many attempts.
    """
    for _ in range(CENTER_ATTEMPTS):
        cx = random.randint(WORLD_MIN, WORLD_MAX)
        cy = random.randint(WORLD_MIN, WORLD_MAX)
        ok = True
        for (pcx, pcy, pR3) in placed:
            dx = cx - pcx
            dy = cy - pcy
            if math.hypot(dx, dy) < (R3 + pR3 + min_gap):
                ok = False
                break
        if ok:
            return cx, cy
    raise ValueError("No non-overlapping center found for these radii.")

def place_target(placed: List[Tuple[int, int, float]], min_gap: float) -> Tuple[int, int, float, float, float]:
    """
    Generate radii and a center that fits without overlapping previously placed targets.
    Retries with new radii (up to RADII_REGEN_MAX) if necessary.
    """
    for _ in range(RADII_REGEN_MAX):
        R1, R2, R3 = gen_radii()
        try:
            cx, cy = non_overlapping_center(R3, placed, min_gap)
            return cx, cy, R1, R2, R3
        except ValueError:
            continue
    # As a last resort, try smaller radii aggressively
    for _ in range(RADII_REGEN_MAX):
        # Bias toward smaller targets to improve packing
        R1 = round(random.uniform(R1_MIN, (R1_MIN + R1_MAX) / 2), 1)
        R2 = round(R1 + random.uniform(R2_ADD_MIN, (R2_ADD_MIN + R2_ADD_MAX) / 2), 1)
        R3 = round(R2 + random.uniform(R3_ADD_MIN, (R3_ADD_MIN + R3_ADD_MAX) / 2), 1)
        try:
            cx, cy = non_overlapping_center(R3, placed, min_gap)
            return cx, cy, R1, R2, R3
        except ValueError:
            continue
    raise RuntimeError("Could not place a non-overlapping target. Consider reducing num_shots or radii.")

def generate_data(num_shots: int = 20, seed: int = None, min_gap: float = MIN_GAP):
    if seed is not None:
        random.seed(seed)

    placed: List[Tuple[int, int, float]] = []  # (cx, cy, R3)
    targets: List[Tuple[int, int, float, float, float]] = []

    # 1) Place all targets without overlap
    nb_missed = 0
    for i in range(num_shots):
        try:
            cx, cy, R1, R2, R3 = place_target(placed, min_gap)
        except RuntimeError as e:
            # If extremely dense, produce what we have and warn
            print(f"⚠️  {e} after placing {i} targets. Outputting partial set.")
            num_shots = i
            break
        placed.append((cx, cy, R3))
        targets.append((cx, cy, R1, R2, R3))

    # 2) Generate one shot around each placed target (bullseye/inner/outer/miss)
    with open("data/rings.txt", "w", encoding="utf-8") as fr, \
         open("data/shots.txt", "w", encoding="utf-8") as fs:

        for (cx, cy, R1, R2, R3) in targets:
            fr.write(f"{cx} {cy} {R1} {R2} {R3}\n")

            case = random.choice(["bullseye", "inner", "outer", "miss1", "miss2", "miss3"])
            if case == "bullseye":
                d = random.uniform(0, R1 * 0.9)
            elif case == "inner":
                d = random.uniform(R1 + 1, R2 * 0.9)
            elif case == "outer":
                d = random.uniform(R2 + 1, R3 * 0.9)
            else:  # miss
                d = random.uniform(R3 + 10, R3 + 300)
                nb_missed += 1

            angle = random.uniform(0, 2 * math.pi)
            x = round(cx + d * math.cos(angle), 2)
            y = round(cy + d * math.sin(angle), 2)

            # keep shots inside world bounds for neatness
            x = max(WORLD_MIN, min(WORLD_MAX, x))
            y = max(WORLD_MIN, min(WORLD_MAX, y))
            fs.write(f"{x},{y}\n")

    print(f"✅ Generated {num_shots} non-overlapping targets and paired shots.")
    print("   - rings.txt → cx cy R1 R2 R3")
    print("   - shots.txt → x,y")
    print(f"nb_missed: {nb_missed}")

def main():
    # Adjust defaults here if you want
    generate_data(num_shots=100, seed=42, min_gap=5.0)

if __name__ == "__main__":
    main()
