import math
from math import floor
from typing import List, Optional, Tuple
import pygame


# ---------------------- Constantes physiques & rendu ----------------------
TILE = 16
FPS = 20

G = 0.06
FRICTION = 0.80
VX_MAX = 0.5
VY_UP_MAX = 0.6    # vers le haut (vy négatif)
VY_DOWN_MAX = 0.8  # vers le bas (vy positif)

BG_COLOR = (10, 10, 12)
TILE_COLOR = (60, 60, 60)
SPAWN_COLOR = (30, 144, 255)

# ---------------------- Classe principale ----------------------


class SonicGame:
    """
    Simulation de plateformer à 20 FPS :
      - Grille ASCII (# = solide, . = air, S = spawn)
      - Joueur ponctuel (x,y floats) échantillonné sur (floor(y), floor(x))
      - manage(cmd) : applique une commande frame, la gravité, la friction,
                      déplace avec collisions et mémorise l'atterrissage max
      - draw(surface) : rend la carte et un hérisson procédural
    """
    def __init__(self, grid_lines: List[str], view_scale: int = TILE) -> None:
        # Carte / dimensions
        self.grid: List[str] = grid_lines[:]  # immuable ici
        self.rows: int = len(self.grid)
        self.cols: int = len(self.grid[0]) if self.rows else 0

        # Validation rectangle
        for line in self.grid:
            if len(line) != self.cols:
                raise ValueError("La carte doit être rectangulaire.")

        # Localiser le spawn 'S'
        sp = [(r, c) for r, row in enumerate(self.grid) for c, ch in enumerate(row) if ch == "S"]
        if len(sp) != 1:
            raise ValueError("La carte doit contenir exactement un 'S'.")

        self.spawn_row: int = sp[0][0]
        self.spawn_col: int = sp[0][1]

        # État joueur (positions en float)
        self.x: float = float(self.spawn_col)
        self.y: float = float(self.spawn_row)
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.on_ground: bool = False

        # Métriques de défi
        self.highest_platform_row_landed: Optional[int] = None  # plus petit row touché en descente
        self.last_cmd: str = "WAIT"

        # Rendu
        self.scale: int = view_scale  # pixels par tuile
        self.hud_font: Optional[pygame.font.Font] = None

    # ---- Collision helpers ----
    def _is_solid(self, row: int, col: int) -> bool:
        """Hors-bord = solide, '#' = solide, 'S' traité comme air."""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return True

        ch = self.grid[row][col]
        return ch == "#"

    @staticmethod
    def _parse_command(s: str) -> Tuple[str, Optional[float]]:
        s = s.strip()
        if not s:
            return "WAIT", None

        parts = s.split()
        op = parts[0].upper()
        val = float(parts[1]) if len(parts) > 1 else None

        return op, val

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    # ---- Physique par frame ----
    def manage(self, command: Optional[str]) -> None:
        """
        Applique une commande (une par frame), met à jour la physique et les collisions.
        command: 'LEFT a' | 'RIGHT a' | 'JUMP j' | 'WAIT' | None
        """
        op, val = self._parse_command(command)
        self.last_cmd = op if (op == "WAIT" or val is None) else f"{op} {val:.2f}"

        # 1) Impulsions de la commande
        if op == "LEFT" and val is not None:
            self.vx -= val
        elif op == "RIGHT" and val is not None:
            self.vx += val
        elif op == "JUMP" and val is not None:
            if self.on_ground:
                self.vy -= val
        # WAIT => rien

        # 2) Gravité
        self.vy += G

        # 3) Friction
        self.vx *= FRICTION

        # 4) Clamps
        self.vx = self._clamp(self.vx, -VX_MAX, VX_MAX)
        self.vy = self._clamp(self.vy, -VY_UP_MAX, VY_DOWN_MAX)

        # 5) Déplacement axe X puis Y (point dans grille avec floor)
        self._move_horizontal()
        self._move_vertical()

    def _move_horizontal(self) -> None:
        new_x = self.x + self.vx
        test_col = int(floor(new_x))
        test_row = int(floor(self.y))

        if self._is_solid(test_row, test_col):
            # bloqué : s'aligner au bord selon la direction
            if self.vx > 0:
                # venant de la gauche → placer juste avant le mur
                self.x = floor(new_x) - 1e-6
            elif self.vx < 0:
                # venant de la droite
                self.x = floor(new_x) + 1 + 1e-6
            self.vx = 0.0
        else:
            self.x = new_x

    def _move_vertical(self) -> None:
        new_y = self.y + self.vy
        test_row = int(floor(new_y))
        test_col = int(floor(self.x))
        self.on_ground = False

        if self._is_solid(test_row, test_col):
            if self.vy > 0:
                # on tombe sur une plateforme : se poser dessus
                self.y = floor(new_y) - 1e-6
                self.vy = 0.0
                self.on_ground = True
                landed_row = int(floor(new_y))
                if (self.highest_platform_row_landed is None or
                        landed_row < self.highest_platform_row_landed):
                    self.highest_platform_row_landed = landed_row
            elif self.vy < 0:
                # on cogne un plafond
                self.y = floor(new_y) + 1 + 1e-6
                self.vy = 0.0
        else:
            self.y = new_y

    # ---- Rendu ----
    def draw(self, surface: pygame.Surface) -> None:
        """Dessine la grille et un petit hérisson procédural à (x,y)."""
        if self.hud_font is None:
            self.hud_font = pygame.font.SysFont("consolas", 16)

        # fond
        surface.fill(BG_COLOR)

        # tuiles
        for r, row in enumerate(self.grid):
            for c, ch in enumerate(row):
                if ch == "#":
                    pygame.draw.rect(
                        surface, TILE_COLOR,
                        (c * self.scale, r * self.scale, self.scale, self.scale)
                    )
                elif ch == "S":
                    pygame.draw.rect(
                        surface, SPAWN_COLOR,
                        (c * self.scale, r * self.scale, self.scale, self.scale)
                    )

        # hérisson procédural (petit sprite vectoriel)
        px = int(self.x * self.scale)
        py = int((self.y - 0.5) * self.scale)
        self._draw_hedgehog(surface, px, py, self.scale)

        # HUD
        text_lines = [
            f"pos=({self.x:.2f},{self.y:.2f})  vel=({self.vx:.2f},{self.vy:.2f})",
            f"on_ground={self.on_ground}  highest_land={self.highest_platform_row_landed}",
            f"last_cmd={self.last_cmd}"
        ]
        y0 = 400
        for s in text_lines:
            img = self.hud_font.render(s, True, (235, 235, 210))
            surface.blit(img, (8, y0))
            y0 += img.get_height() + 2

    def _draw_hedgehog(self, surf: pygame.Surface, cx: int, cy: int, scale: int) -> None:
        """
        Hérisson minimaliste :
          - corps ellipsoïdal brun
          - piquants triangulaires autour
          - œil & museau
        """
        body_w = int(scale * 0.9)
        body_h = int(scale * 0.7)
        body_rect = pygame.Rect(0, 0, body_w, body_h)
        body_rect.center = (cx, cy)
        body_color = (139, 69, 19)   # saddlebrown
        spike_color = (90, 45, 10)

        # Piquants (anneau de triangles)
        spikes = 10
        radius = max(body_w, body_h) // 2 + int(scale * 0.2)
        for i in range(spikes):
            ang = (2 * math.pi * i) / spikes
            x1 = cx + int(math.cos(ang) * (radius - 2))
            y1 = cy + int(math.sin(ang) * (radius - 2))
            x2 = cx + int(math.cos(ang + 0.2) * (radius + scale * 0.2))
            y2 = cy + int(math.sin(ang + 0.2) * (radius + scale * 0.2))
            x3 = cx + int(math.cos(ang - 0.2) * (radius + scale * 0.2))
            y3 = cy + int(math.sin(ang - 0.2) * (radius + scale * 0.2))
            pygame.draw.polygon(surf, spike_color, [(x1, y1), (x2, y2), (x3, y3)])

        # Corps
        pygame.draw.ellipse(surf, body_color, body_rect)

        # Museau
        nose_r = max(2, scale // 8)
        nose_x = body_rect.right - nose_r - 2
        nose_y = body_rect.centery
        pygame.draw.circle(surf, (0, 0, 0), (nose_x, nose_y), nose_r)

        # Œil
        eye_r = max(2, scale // 10)
        eye_x = body_rect.centerx + body_w // 4
        eye_y = body_rect.centery - body_h // 4
        pygame.draw.circle(surf, (250, 250, 250), (eye_x, eye_y), eye_r)
        pygame.draw.circle(surf, (0, 0, 0), (eye_x, eye_y), eye_r // 2)
