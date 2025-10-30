
class SonicMap:
    def __init__(self, mapFile):
        self.grid = self.load_map_lines(mapFile)
        self.nb_rows: int = len(self.grid)
        self.nb_cols: int = len(self.grid[0]) if self.nb_rows else 0

    @staticmethod
    def load_map_lines(filename) -> list[str]:
        with open(filename, "r") as f:
            return [line.rstrip("\n") for line in f]

    def find_start(self):
        sp = [[float(c), float(r)] for r, row in enumerate(self.grid) for c, ch in enumerate(row) if ch == "S"]

        if len(sp) != 1:
            raise ValueError("Grid must contains 1 and only 1 'S'")

        return sp[0]

    def is_wall(self, row: int, col: int) -> bool:
        """Out-of-bounds = solid, '#' = solid, 'S' is actually empty."""
        if row < 0 or row >= self.nb_rows or col < 0 or col >= self.nb_cols:
            return True

        ch = self.grid[row][col]
        return ch == "#"

