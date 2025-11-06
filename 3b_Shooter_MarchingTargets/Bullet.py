import pygame
from UtilityFunctions import UtilityFunctions
from Config import Config


class Bullet:
    """Raygun-style: a point in world space placed when fired."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True

    def draw(self, surf: pygame.Surface) -> None:
        sx, sy = UtilityFunctions.world_to_screen(self.x, self.y)
        pygame.draw.circle(surf, Config.BULLET_COLOR, (sx, sy), Config.BULLET_RADIUS_PX)
