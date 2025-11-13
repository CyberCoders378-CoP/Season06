import pygame
from Sprite import Sprite


class Ship(Sprite):
    def __init__(self, x: float, y: float, width: int, height: int, hp: int, speed: float):
        super().__init__(x, y, width, height)
        self.hp = hp
        self.speed = speed
        self.sprite_image = None  # to be set by subclasses or Engine asset loader

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def update(self, dt: float) -> None:
        super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.sprite_image:
            surface.blit(self.sprite_image, (int(self.x), int(self.y)))
        else:
            # fallback debug
            pygame.draw.rect(surface, (0, 255, 0), self.rect, 1)

