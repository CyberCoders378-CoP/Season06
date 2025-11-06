from typing import List, Optional


class InstructionStream:
    """Feeds one instruction per second to the game."""
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.idx = 0

    def next(self) -> Optional[str]:
        if self.idx >= len(self.lines):
            return None

        s = self.lines[self.idx].strip()
        self.idx += 1
        return s
