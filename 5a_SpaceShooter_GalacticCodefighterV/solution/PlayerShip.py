import math

from Ship import Ship


class PlayerShip(Ship):
    def __init__(self, x: float, y: float):
        # TODO: tweak width/height/hp/speed
        super().__init__(x, y, width=32, height=32, hp=3, speed=200.0)
        self.dest_x = x
        self.dest_y = y
        self.shoot_cooldown = 0.25
        self.time_since_last_shot = 0.0

    def set_destination(self, x: float, y: float) -> None:
        self.dest_x = x
        self.dest_y = y

    def can_shoot(self) -> bool:
        return self.time_since_last_shot >= self.shoot_cooldown

    def request_shot(self) -> bool:
        """Called by Engine when AI says shoot. Returns True if shot actually fired."""
        if self.can_shoot():
            self.time_since_last_shot = 0.0
            return True

        return False

    def update(self, dt: float) -> None:
        # Move toward destination
        self.time_since_last_shot += dt

        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        dist_sq = dx * dx + dy * dy

        if dist_sq > 1.0:
            # normalize
            dist = math.sqrt(dist_sq)
            vx = dx / dist * self.speed
            vy = dy / dist * self.speed

            self.x += vx * dt
            self.y += vy * dt

        super().update(dt)

