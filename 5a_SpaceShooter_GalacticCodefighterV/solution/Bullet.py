from Sprite import Sprite


class Bullet(Sprite):
    def __init__(self, x: float, y: float, vx: float, vy: float, from_player: bool):
        super().__init__(x, y, width=4, height=8)
        self.vx = vx
        self.vy = vy
        self.from_player = from_player

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        super().update(dt)
