import pygame


class Sprite:
    def __init__(self, x: float, y: float, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.alive = True

        # For collision
        self.rect = pygame.Rect(int(x), int(y), width, height)

    def update(self, dt: float) -> None:
        """Update logic, dt in seconds."""
        self.rect.topleft = (int(self.x), int(self.y))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw sprite. Default: debug rectangle."""
        pygame.draw.rect(surface, (255, 0, 255), self.rect, 1)
