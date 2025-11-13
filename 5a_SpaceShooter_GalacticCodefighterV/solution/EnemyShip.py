from Ship import Ship


class EnemyShip(Ship):
    def __init__(self, x: float, y: float, enemy_type: str = "basic"):
        super().__init__(x, y, width=24, height=24, hp=1, speed=100.0)
        self.enemy_type = enemy_type
        self.wave_controller = None  # reference to WaveFormation if needed

    def update(self, dt: float) -> None:
        # Basic downward movement, can be overridden by patterns
        self.y += self.speed * dt
        super().update(dt)

