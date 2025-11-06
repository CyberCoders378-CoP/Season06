import math
import pygame
from typing import List


def get_shoot_score(target: List[str], shot: list[str]) -> int:
    pos_x = int(target[0])
    pos_y = int(target[1])

    radius_bullseye = float(target[2])
    radius_inner = float(target[3])
    radius_outer = float(target[4])

    #Calculate hypothenuse
    distance = math.hypot(pos_x - float(shot[0]), pos_y - float(shot[1]))

    if distance <= radius_bullseye:
        return 10
    elif distance <= radius_inner:
        return 5
    elif distance <= radius_outer:
        return 3

    return 0


def main():
    with open("data/rings.txt") as fr:
        targets = fr.readlines()
        targets = [t.strip().split() for t in targets]

    with open("data/shots.txt") as fs:
        shots = fs.readlines()
        shots = [s.strip().split(",") for s in shots]

    total_score = 0
    log_shots = {}
    log_nb = {"Bullseye": 0, "Inner": 0, "Outer": 0}
    for i, shot in enumerate(shots):
        for target in targets:
            score = get_shoot_score(target, shot)

            match score:
                case 10:
                    log_shots[i] = "Bullseye"
                    log_nb["Bullseye"] += 1
                case 5:
                    log_shots[i] = "Inner"
                    log_nb["Inner"] += 1
                case 3:
                    log_shots[i] = "Outer"
                    log_nb["Outer"] += 1

            total_score += score

    #print(f"Logs of all the shots individually: {log_shots}")
    #print(f"Logs By Count: {log_nb}")
    print(f"Final Score: {total_score}")



# ---------- Main Extended (PyGame Replay) ----------
# ---------- Config ----------
WORLD_MIN = -1000
WORLD_MAX = 1000
SCREEN_W = 900
SCREEN_H = 900
PADDING = 40
STEP_DELAY_MS = 1000  # 1 second between pairs

BG_COLOR = (15, 17, 22)
RING_BULL = (240, 208, 0)    # bullseye ring (outer edge)
RING_INNER = (80, 160, 255)
RING_OUTER = (80, 200, 120)
CENTER_DOT = (255, 255, 255)

SHOT_BULL = (255, 80, 80)    # 10 pts
SHOT_INNER = (80, 160, 255)  # 5 pts
SHOT_OUTER = (80, 200, 120)  # 3 pts
SHOT_MISS = (120, 120, 120)  # 0 pts

HUD_COLOR = (230, 230, 230)


# ---------- Core scoring (aligned with your solution: 10/5/3/0) ----------
def score_shot(cx, cy, r1, r2, r3, x, y) -> int:
    d = math.hypot(cx - x, cy - y)
    if d <= r1:
        return 10
    elif d <= r2:
        return 5
    elif d <= r3:
        return 3
    return 0


# ---------- Parsing ----------
def load_targets_and_shots(rings_path, shots_path):
    with open(rings_path, "r", encoding="utf-8") as fr:
        rings = [tuple(map(float, ln.split())) for ln in fr if ln.strip()]
    with open(shots_path, "r", encoding="utf-8") as fs:
        shots = [tuple(map(float, ln.split(","))) for ln in fs if ln.strip()]

    n = min(len(rings), len(shots))
    if n < len(rings) or n < len(shots):
        print(f"⚠️  Mismatched lines. Using the first {n} pairs.")
    pairs = []
    for i in range(n):
        cx, cy, R1, R2, R3 = rings[i]
        x, y = shots[i]
        pairs.append(((cx, cy, R1, R2, R3), (x, y)))
    return pairs

# ---------- World ↔ Screen mapping ----------
def pixels_per_unit() -> float:
    usable_w = SCREEN_W - 2 * PADDING
    world_span = (WORLD_MAX - WORLD_MIN)
    return usable_w / world_span  # square mapping

def world_to_screen(x: float, y: float):
    # Normalize to [0..1], then scale to screen; invert Y for screen coords
    s = pixels_per_unit()
    nx = (x - WORLD_MIN) / (WORLD_MAX - WORLD_MIN)
    ny = (y - WORLD_MIN) / (WORLD_MAX - WORLD_MIN)
    sx = int(PADDING + nx * (SCREEN_W - 2 * PADDING))
    sy = int(PADDING + (1 - ny) * (SCREEN_H - 2 * PADDING))
    return sx, sy

def world_radius_to_pixels(r: float) -> int:
    return int(r * pixels_per_unit())

# ---------- Drawing ----------
def draw_target(surface, cx, cy, R1, R2, R3):
    sx, sy = world_to_screen(cx, cy)
    # Outermost ring first (so inner rings are visible)
    pygame.draw.circle(surface, RING_OUTER, (sx, sy), world_radius_to_pixels(R3), width=2)
    pygame.draw.circle(surface, RING_INNER, (sx, sy), world_radius_to_pixels(R2), width=2)
    pygame.draw.circle(surface, RING_BULL, (sx, sy), world_radius_to_pixels(R1), width=2)
    pygame.draw.circle(surface, CENTER_DOT, (sx, sy), 3)

def draw_shot(surface, x, y, shot_score):
    sx, sy = world_to_screen(x, y)
    color = SHOT_MISS
    if shot_score == 10:
        color = SHOT_BULL
    elif shot_score == 5:
        color = SHOT_INNER
    elif shot_score == 3:
        color = SHOT_OUTER
    pygame.draw.circle(surface, color, (sx, sy), 5)

def draw_hud(surface, font, idx, total, counts, total_pairs):
    lines = [
        f"Shot: {idx}/{total_pairs}",
        f"Score: {total}",
        f"Bullseye(10): {counts['Bullseye']}",
        f"Inner(5): {counts['Inner']}",
        f"Outer(3): {counts['Outer']}",
        f"Misses(0): {counts['Miss']}",
        "Press ESC or Q to quit",
    ]
    x, y = 12, 10
    for line in lines:
        surf = font.render(line, True, HUD_COLOR)
        surface.blit(surf, (x, y))
        y += surf.get_height() + 4


def main_extended():
    # Load data
    pairs = load_targets_and_shots("data/rings.txt", "data/shots.txt")
    total_pairs = len(pairs)
    if total_pairs == 0:
        print("No pairs to display. Check your data files.")
        return

    pygame.init()
    pygame.display.set_caption("Shooter Replay – 1s per target/shot")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)

    # Animation state
    shown_pairs = 0
    last_step_time = 0

    # Score tracking
    total_score = 0
    counts = {"Bullseye": 0, "Inner": 0, "Outer": 0, "Miss": 0}


    running = True
    while running:
        dt = clock.tick(60)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

        # Step to next pair every STEP_DELAY_MS
        if shown_pairs < total_pairs and (now - last_step_time >= STEP_DELAY_MS):
            (cx, cy, R1, R2, R3), (x, y) = pairs[shown_pairs]
            s = score_shot(cx, cy, R1, R2, R3, x, y)
            total_score += s
            if s == 10:
                counts["Bullseye"] += 1
            elif s == 5:
                counts["Inner"] += 1
            elif s == 3:
                counts["Outer"] += 1
            else:
                counts["Miss"] += 1

            shown_pairs += 1
            last_step_time = now

        # ----- Render -----
        screen.fill(BG_COLOR)

        # Draw all targets
        for i in range(len(pairs)):
            (cx, cy, R1, R2, R3), _ = pairs[i]
            draw_target(screen, cx, cy, R1, R2, R3)

        # Draw everything revealed so far
        for i in range(shown_pairs):
            (cx, cy, R1, R2, R3), (x, y) = pairs[i]
            s = score_shot(cx, cy, R1, R2, R3, x, y)
            draw_shot(screen, x, y, s)

        draw_hud(screen, font, shown_pairs, total_score, counts, total_pairs)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    print("Hello e3a")
    main()
    main_extended()
