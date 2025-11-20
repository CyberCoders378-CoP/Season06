from Ship import Ship
import math


class EnemyShip(Ship):
    def __init__(self, x: float, y: float, enemy_type: str = "basic"):
        super().__init__(x, y, width=24, height=24, hp=1, speed=100.0)

        self.enemy_type = enemy_type
        self.wave_controller = None  # reference to WaveFormation if needed

        # New movement system:
        self.vx = 0.0
        self.vy = 0.0   # default downward drift
        self.has_target = False

        self.target_x = 0.0
        self.target_y = 0.0
        self.time_to_target = 0.0
        self.time_elapsed = 0.0

    # ---------------------------------------------------------
    # High-level movement commands
    # ---------------------------------------------------------

    def move_to(self, x: float, y: float, duration: float):
        """
        Command the ship to move to (x, y) in `duration` seconds.
        Automatically computes vx, vy.

        If duration == 0, teleport instantly.
        """
        self.target_x = x
        self.target_y = y

        if duration <= 0.001:
            # Instant jump
            self.x = x
            self.y = y
            self.vx = 0.0
            self.vy = 0.0
            self.has_target = False
            return

        self.time_to_target = duration
        self.time_elapsed = 0.0
        self.has_target = True

        # Compute required velocity
        dx = x - self.x
        dy = y - self.y
        self.vx = dx / duration
        self.vy = dy / duration

    def clear_move(self):
        """Stops scripted movement, keeps last velocity."""
        self.has_target = False
        self.time_to_target = 0.0
        self.time_elapsed = 0.0

    # ---------------------------------------------------------
    # Update loop
    # ---------------------------------------------------------

    def update(self, dt: float) -> None:
        """
        Handles:
          - move_to() scripted movement
          - default downward drift if no scripted movement
        """

        if self.has_target:
            # Follow velocity toward target
            self.x += self.vx * dt
            self.y += self.vy * dt

            self.time_elapsed += dt

            # Check arrival
            if self.time_elapsed >= self.time_to_target:
                # Snap perfectly to destination
                self.x = self.target_x
                self.y = self.target_y

                # Stop scripted movement
                self.vx = 0.0
                self.vy = 0.0
                self.has_target = False

        else:
            # Default movement when idle
            self.x += self.vx * dt
            self.y += self.vy * dt

        super().update(dt)
