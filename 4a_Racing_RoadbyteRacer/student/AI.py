# AI.py
from typing import List, Optional
from Engine import Engine


class AI:
    def __init__(self, max_depth: int = 5):
        """
        max_depth: how many rows ahead to explore.
        The engine's lookahead should be >= max_depth for full effect.
        """
        ...

    def exit(self):
        ...

    @staticmethod
    def choose_start():
        """
        Return: In which column the user whishes to start the game, blindly
        """
        return 2

    def choose_move(self, visible_rows: List[str], car_x: int) -> int:
        """
        visible_rows[0] = row we are about to enter this tick.
        car_x: current column [0..W-1].

        Returns:
            -1 -> move left
             0 -> stay
            +1 -> move right
        """
        #TODO return something
        return 0
