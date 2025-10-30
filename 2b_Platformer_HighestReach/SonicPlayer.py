from math import floor
from SonicMap import SonicMap
# ---------------------- Constantes physiques & rendu ----------------------
G = 0.06
FRICTION = 0.80
VX_MAX = 0.5
VY_UP_MAX = 0.6    # TOWARDS Up (negative vertical speed)
VY_DOWN_MAX = 0.8  # Towards down (positive vertical speed)

class SonicPlayer:
    def __init__(self, sonic_map:SonicMap) -> None:
        start_pos = sonic_map.find_start()

        self.map = sonic_map
        self.x: float = float(start_pos[0])
        self.y: float = float(start_pos[1])
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.on_ground: bool = False

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    def _move_horizontal(self) -> None:
        new_x = self.x + self.vx
        test_col = int(floor(new_x))
        test_row = int(floor(self.y))

        if self.map.is_wall(test_row, test_col):
            # blocked : Realign just before the position
            if self.vx > 0:
                # Coming from the left -> realign before the wall
                self.x = floor(new_x) - 1e-6

            elif self.vx < 0:
                # Coming from the left -> realign a tiny bit after the wall
                self.x = floor(new_x) + 1 + 1e-6

            self.vx = 0.0
        else:
            self.x = new_x

    def _move_vertical(self) -> None:
        new_y = self.y + self.vy
        test_row = int(floor(new_y))
        test_col = int(floor(self.x))
        self.on_ground = False

        if self.map.is_wall(test_row, test_col):
            if self.vy > 0:
                # Coming from above on the platform, we set on_ground and stop
                self.y = floor(new_y) - 1e-6
                self.vy = 0.0
                self.on_ground = True

            elif self.vy < 0:
                # Hit a ceiling
                self.y = floor(new_y) + 1 + 1e-6
                self.vy = 0.0
        else:
            self.y = new_y

    def manage(self, command):
        match command[0]:
            case "WAIT":
                ...
            case "JUMP":
                if self.on_ground:
                    self.vy -= float(command[1])
            case "RIGHT":
                self.vx += float(command[1])
            case "LEFT":
                self.vx -= float(command[1])

        # 2) Gravity
        self.vy += G

        # 3) Friction
        self.vx *= FRICTION

        # 4) Clamps
        self.vx = self._clamp(self.vx, -VX_MAX, VX_MAX)
        self.vy = self._clamp(self.vy, -VY_UP_MAX, VY_DOWN_MAX)

        # 5) Movement on the X axis, then on the Y axis (a bit different for both)
        self._move_horizontal()
        self._move_vertical()

    def print_debug(self):
        print(f"pos=({self.x:.2f},{self.y:.2f})  vel=({self.vx:.2f},{self.vy:.2f}),on_ground={self.on_ground} ")

