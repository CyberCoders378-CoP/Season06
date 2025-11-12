# AI.py
from typing import List


class AI:
    def choose_move(visible_rows: List[str], car_x: int) -> int:
        """
        visible_rows: top-most is the next row that will drop in (height = H, width = W)
        car_x: current column of the car [0..W-1]
        Return: -1 (left), 0 (stay), +1 (right)
        """
        # TODO: Students implement heuristic/path choice
        return 0  # baseline: do nothing
