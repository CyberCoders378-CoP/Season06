from EnemyShip import EnemyShip


class Boss(EnemyShip):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, enemy_type="boss")
        self.hp = 50
        self.speed = 80.0
        # Boss-specific behaviour variables
        self.phase = 1
        self.time_in_phase = 0.0

    def update(self, dt: float) -> None:
        self.time_in_phase += dt
        # Example: simple horizontal oscillation
        import math
        self.x += math.sin(self.time_in_phase) * self.speed * dt

        super().update(dt)
