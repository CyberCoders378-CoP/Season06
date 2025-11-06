import pygame
import math
from UtilityFunctions import UtilityFunctions
from Config import Config


class Target:
    def __init__(self, tid: int, x: float, y: float, vx: float, vy: float):
        self.id = tid
        self.x = x
        self.y = y
        self.vx = vx  # world units / second
        self.vy = vy
        self.alive = True
        self.color = Config.TARGET_COLOR

    def update(self, dt_sec: float) -> None:
        if not self.alive:
            self.color = Config.TARGET_COLOR_DEAD
            return

        self.x += self.vx * dt_sec
        self.y += self.vy * dt_sec

        if self.x <= Config.WORLD_MIN:
            self.vx*= -1

        if self.y <= Config.WORLD_MIN:
            self.vy*= -1

        if self.x >= Config.WORLD_MAX:
            self.vx*= -1

        if self.y >= Config.WORLD_MAX:
            self.vy*= -1

    def draw(self, surf: pygame.Surface) -> None:
        # Convert world radius to pixel radius dynamically
        pixel_radius = UtilityFunctions.world_radius_to_pixels(Config.TARGET_RADIUS)

        sx, sy = UtilityFunctions.world_to_screen(self.x, self.y)
        pygame.draw.circle(surf, self.color, (sx, sy), pixel_radius)

    def distance_to(self, wx: float, wy: float) -> float:
        dx = self.x - wx
        dy = self.y - wy
        return math.hypot(dx, dy)
