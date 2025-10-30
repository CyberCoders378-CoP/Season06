import argparse
import pygame
import sys
from pathlib import Path
from SonicRecorder import SonicGame



def load_map_lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def draw_map(surface, lines: list[str], tile: int) -> tuple[int, int]:
    """Dessine # en rectangles, S en carré distinct, . transparent.
    Retourne (width_px, height_px)."""
    h = len(lines)
    w = max((len(row) for row in lines), default=0)
    for r, row in enumerate(lines):
        for c, ch in enumerate(row):
            x, y = c * tile, r * tile
            if ch == "#":
                pygame.draw.rect(surface, (60, 60, 60), (x, y, tile, tile))
            elif ch == "S":
                pygame.draw.rect(surface, (30, 144, 255), (x, y, tile, tile))  # bleu
            # '.' => rien
    return w * tile, h * tile


def overlay_text(surface, lines, font, color=(230, 230, 230), topleft=(8, 8)):
    x, y = topleft
    for s in lines:
        img = font.render(s, True, color)
        surface.blit(img, (x, y))
        y += img.get_height() + 2


def build_frame_command(keys, prev_space, thrust_val, jump_val):
    """Retourne (cmd_str, space_now) où cmd_str ∈ {LEFT, RIGHT, JUMP, WAIT}."""
    left = keys[pygame.K_LEFT]
    right = keys[pygame.K_RIGHT]
    space = keys[pygame.K_SPACE]

    # Déclenchement du saut sur front montant
    if space and not prev_space:
        return f"JUMP {jump_val:.2f}", space

    if left and not right:
        return f"LEFT {thrust_val:.2f}", space
    if right and not left:
        return f"RIGHT {thrust_val:.2f}", space

    return "WAIT", space


def save_commands(path: Path, commands: list[str]):
    path.write_text("\n".join(commands) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Record per-frame platformer commands at fixed FPS.")
    parser.add_argument("--out", type=Path, default=Path("data/commands.txt"))
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--thrust", type=float, default=1.6)
    parser.add_argument("--jump", type=float, default=5.0)
    parser.add_argument("--map", type=Path, default=None, help="Optional ASCII map to render")
    parser.add_argument("--tile", type=int, default=16)
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_caption("Command Recorder (20 FPS)")
    clock = pygame.time.Clock()

    # Préparer la surface (taille selon carte si fournie)
    if args.map and args.map.exists():
        map_lines = load_map_lines(args.map)
        width_px = max(800, (max(len(r) for r in map_lines) if map_lines else 0) * args.tile)
        height_px = max(600, len(map_lines) * args.tile if map_lines else 0)
    else:
        map_lines = []
        width_px, height_px = 1000, 700

    screen = pygame.display.set_mode((width_px, height_px))
    font = pygame.font.SysFont("consolas", 18)
    game = SonicGame(map_lines, 16)

    commands: list[str] = []
    paused = False
    prev_space = False
    just_saved = False

    while True:
        # Gestion événements (pour pause, undo, save, quit)
        # Rendu de fond (carte si présente)
        screen.fill((10, 10, 12))
        cmd_frame = "WAIT"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_commands(args.out, commands)
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save_commands(args.out, commands)
                    pygame.quit()
                    sys.exit(0)
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_s:
                    save_commands(args.out, commands)
                    just_saved = True
                elif event.key == pygame.K_BACKSPACE and commands:
                    commands.pop()

        if not paused:
            keys = pygame.key.get_pressed()
            cmd_frame, prev_space = build_frame_command(keys, prev_space, args.thrust, args.jump)
            commands.append(cmd_frame)

        game.manage(cmd_frame)
        game.draw(screen)

        # Overlay d'info
        hud = [
            f"Frames recorded: {len(commands)}  (target FPS: {args.fps})",
            f"Last cmd: {commands[-1] if commands else 'None'}",
            "Keys: ←/→ thrust | SPACE jump | P pause | BACKSPACE undo | S save | ESC quit",
            f"Output: {args.out}",
        ]

        if paused:
            hud.insert(0, "[PAUSED]")
        if just_saved:
            hud.append("[Saved]")
            just_saved = False
        overlay_text(screen, hud, font, color=(235, 235, 210), topleft=(8, 316))

        pygame.display.flip()
        clock.tick(args.fps)


if __name__ == "__main__":
    main()
