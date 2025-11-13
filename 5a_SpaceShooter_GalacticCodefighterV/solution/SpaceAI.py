from ai_api import GameState, AICommand  # or from .engine_api import ...


class SpaceAI:
    """
    User-implemented AI.
    The engine will create exactly ONE instance of this class
    and call `decide()` roughly every 0.5 seconds.
    """

    def __init__(self):
        # Students can store "memory" here between calls
        self.last_target_id = None
        self.last_wave_seen = 0

    def decide(self, state: GameState) -> AICommand:
        """
        Called ~every 0.5 seconds with the current visible state.
        MUST return an AICommand object.
        """
        # Example super-dumb baseline behaviour:
        # - Move toward the nearest enemy on X axis
        # - Always shoot
        if not state.enemies:
            return AICommand(move_x=0, move_y=0, shoot=False)

        # Find nearest enemy by vertical distance
        nearest = min(state.enemies, key=lambda e: abs(e.y - state.player.y))

        move_x = 0
        if nearest.x < state.player.x:
            move_x = -1
        elif nearest.x > state.player.x:
            move_x = 1

        return AICommand(move_x=move_x, move_y=0, shoot=True)
