# AI.py
from typing import List, Optional
from Engine import Engine


class AI:
    def __init__(self, max_depth: int = 5):
        """
        max_depth: how many rows ahead to explore.
        The engine's lookahead should be >= max_depth for full effect.
        """
        self.max_depth = max_depth
        self.width = Engine.W

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
        if not visible_rows:
            return 0  # nothing to do

        width = len(visible_rows[0])
        #depth_limit = min(self.max_depth, len(visible_rows))

        best_cost = float("inf")
        best_move = 0  # default: stay

        for first_move in (-1, 0, 1):
            new_x = car_x + first_move

            if new_x < 0 or new_x >= width:
                continue  # out of bounds

            # Check if first step collides on the next row
            if visible_rows[0][new_x] == "#":
                continue  # immediate crash, discard

            initial_cost = 1 if first_move != 0 else 0

            # Explore deeper moves over the next rows
            total_cost = self._search_branch(visible_rows, 1, new_x, initial_cost)

            if total_cost is None:
                # No safe continuation for this first move
                continue

            # Choose the move that minimizes cost; tie-break nicely
            if self._is_better_move(total_cost, first_move, best_cost, best_move, car_x):
                best_cost = total_cost
                best_move = first_move

        return best_move

    def _search_branch(self, visible_rows: List[str], depth: int, cur_x: int, cost_so_far: int) -> Optional[int]:
        """
        Recursive depth-limited search.

        visible_rows: rows[0..depth_limit-1] ahead (0 already used by caller at depth=0).
        depth: current depth in [1..depth_limit].
        cur_x: current column at this depth.
        cost_so_far: lateral movements accumulated so far.

        Returns:
            minimal total cost reachable from here (int), or
            None if all continuations lead to collision.
        """
        # If we reached the horizon, evaluate this path
        if depth >= self.max_depth:
            return cost_so_far

        row = visible_rows[depth]
        best: Optional[int] = None

        for move in (-1, 0, 1):
            nx = cur_x + move
            if nx < 0 or nx >= self.width:
                continue

            if row[nx] == "#":
                # This move would crash at this depth -> skip
                continue

            new_cost = cost_so_far + (1 if move != 0 else 0)
            sub = self._search_branch(visible_rows, depth + 1, nx, new_cost)

            if sub is None:
                continue

            if best is None or sub < best:
                best = sub

        return best

    def _is_better_move(self, candidate_cost: int, candidate_move: int, best_cost: int, best_move: int, car_x: int) -> bool:
        """
        Decide whether candidate_move is better than current best.
        - Prefer lower total cost
        - On tie, prefer staying (0)
        - On tie again, prefer staying closer to center
        """
        if candidate_cost < best_cost:
            return True
        if candidate_cost > best_cost:
            return False

        # cost tie -> prefer staying
        if candidate_move == 0 and best_move != 0:
            return True
        if best_move == 0 and candidate_move != 0:
            return False

        # both same type (both 0, or both non-zero) -> prefer closer to center
        center = (self.width - 1) / 2.0
        cand_pos = car_x + candidate_move
        best_pos = car_x + best_move
        cand_dist = abs(cand_pos - center)
        best_dist = abs(best_pos - center)
        return cand_dist < best_dist
