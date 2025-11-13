# Engine.py
"""
EP4 – Maze Navigator (Medium)
Engine: streams rows to the AI and simulates movement.

Rules:
- Grid cells: '.' = free, '#' = obstacle
- Each tick: AI returns -1 (left), 0 (stay), +1 (right)
- Only horizontal moves are counted toward the score (# Movements)
- Collision occurs if the next entered cell is '#'
- Reaching the end of the stream = success
"""

from typing import Callable, Iterable, List, Optional, Tuple


class Engine:
    W = 10
    H = 5  # number of rows of lookahead shown to AI

    def __init__(self, lookahead: int = H, start_x: int = W//2):
        """
        lookahead: number of upcoming rows exposed to the AI each tick
        start_x:   starting column; if None, will default to center after first row is known
        """
        if lookahead < 1:
            raise ValueError("lookahead must be >= 1")

        self.lookahead = lookahead
        self.start_x = start_x if (0 < start_x < Engine.W) else Engine.W//2

    @staticmethod
    def _is_free(ch: str) -> bool:
        # Treat anything other than '.' as blocked, to be safe.
        return ch == "."

    @staticmethod
    def _is_goal(ch: str) -> bool:
        # Treat anything other than '.' as blocked, to be safe.
        return ch == "F"

    def run_game(self, stream: Iterable[str], ai_func: Callable[[List[str], int], int]) -> Tuple[int, List[int]]:
        """
        stream: yields ASCII lines of equal width ('.' and '#')
        ai_func(visible_rows, cur_x) -> move in {-1, 0, +1}
        Returns: total number of horizontal movements performed.
        """
        # Prime the buffer
        buffer: List[str] = []
        it = iter(stream)

        # Load first row to determine width and set start position
        try:
            first_row = next(it)
        except StopIteration:
            return 0, []

        width = len(first_row)
        if width == 0:
            return 0, []


        # Build initial lookahead window
        buffer.append(first_row)
        for _ in range(self.lookahead - 1):
            try:
                buffer.append(next(it))
            except StopIteration:
                break

        movements = 0
        path = []
        row_index = 0
        x = self.start_x

        # Simulation loop:
        # At each tick, AI chooses move based on the current lookahead window.
        while True:
            # Sanity: ensure row widths are consistent
            if any(len(r) != width for r in buffer):
                raise ValueError("Inconsistent row width detected in stream.")

            # Ask AI for the next horizontal move
            try:
                move = int(ai_func(buffer[:], x))  # pass a shallow copy for safety
                path.append(move)
            except Exception as e:
                move = 0
                print(e)

            if move < -1 or move > 1:
                move = 0

            # Count horizontal movement if any
            if move != 0:
                movements += 1

            # Apply move with clamping
            x = max(0, min(width - 1, x + move))

            # Enter the next row (front of buffer) and check collision
            current_row = buffer[0]
            if not self._is_free(current_row[x]):
                if self._is_goal(current_row[x]):
                    # Collision: stop and report movements so far
                    print("Congratulation! you reach the goal!!!")
                    return movements, path

                # Collision: stop and report movements so far
                print("BANG! You hit a wall")
                return movements, path

            # Advance: pop the row we just entered
            buffer.pop(0)
            row_index += 1

            # Try to append one more row to maintain lookahead
            try:
                nxt = next(it)
                buffer.append(nxt)
            except StopIteration:
                if self._is_goal(current_row[x]) == "F":
                    # Collision: stop and report movements so far
                    print("Congratulation! you reach the goal!!!")
                    return movements, path

                return movements, path

