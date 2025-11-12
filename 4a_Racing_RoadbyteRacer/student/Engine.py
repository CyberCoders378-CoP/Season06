# Engine.py
import sys
from typing import List, Iterable


class Engine:
    W = 13
    H = 8  # number of rows of lookahead shown to AI

    def __init__(self):
        ...

    def step_collision(self, row: str, x: int) -> bool:
        return row[x] == '#'

    def run_game(self, stream: Iterable[str], ai_func, start_x=3) -> int:
        """
        stream yields decrypted rows from top to bottom (length W each).
        Returns total 'dodges' = count of obstacle rows that were avoided.
        """
        buffer: List[str] = []
        dodges = 0
        x = start_x

        # prefill buffer
        for _ in range(self.H):
            try:
                buffer.append(next(stream))
            except StopIteration:
                return dodges

        while True:
            # AI decides before the next row drops in
            move = ai_func(buffer, x)
            if move not in (-1, 0, 1):
                move = 0

            x = max(0, min(self.W-1, x + move))

            # next row drops
            try:
                row = next(stream)
            except StopIteration:
                # crossed finish by exhausting stream
                return dodges

            # detect obstacle row and collision
            if '#' in buffer[-1]:               # last visible row is now “at car bumper”
                collision = self.step_collision(buffer[-1], x)
                if collision:
                    return dodges
                else:
                    dodges += 1

            # scroll window
            buffer.pop(0)
            buffer.append(row)
