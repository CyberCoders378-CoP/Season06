from typing import Tuple
from Config import Config


class UtilityFunctions:
    @staticmethod
    def pixels_per_unit() -> float:
        usable_w = Config.SCREEN_W - 2 * Config.PADDING
        world_span = (Config.WORLD_MAX - Config.WORLD_MIN)
        return usable_w / world_span  # keep square

    @staticmethod
    def world_to_screen(x: float, y: float) -> Tuple[int, int]:
        nx = (x - Config.WORLD_MIN) / (Config.WORLD_MAX - Config.WORLD_MIN)
        ny = (y - Config.WORLD_MIN) / (Config.WORLD_MAX - Config.WORLD_MIN)
        sx = int(Config.PADDING + nx * (Config.SCREEN_W - 2 * Config.PADDING))
        sy = int(Config.PADDING + (1 - ny) * (Config.SCREEN_H - 2 * Config.PADDING))
        return sx, sy

    @staticmethod
    def world_radius_to_pixels(r: float) -> int:
        return int(max(1, int(r * UtilityFunctions.pixels_per_unit())))