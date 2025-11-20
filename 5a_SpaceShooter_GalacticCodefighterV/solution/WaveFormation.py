# waves.py
from Boss import Boss
from EnemyShip import EnemyShip
from typing import List, Tuple, Optional


class WaveFormation:
    """
    Controls enemy waves & spawning patterns.

    Features:
      - Different patterns per wave (line, staggered, triangle stream, etc.)
      - Timed spawning for patterns that drip enemies over time
      - Final boss after all waves are done
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine

        self.current_wave: int = 1
        self.total_waves: int = 5
        self.boss_spawned: bool = False

        # Per-wave spawn state
        self.wave_active: bool = False          # True when a wave is ongoing
        self.pending_spawns: List[Tuple[float, float]] = []  # (x, y) for yet-to-spawn enemies
        self.spawn_interval: float = 0.0        # time between spawns for stream patterns
        self.spawn_timer: float = 0.0           # accumulates dt

        # Simple pattern mapping for 5 waves
        # You can tweak this easily.
        self.wave_patterns = {
            1: "line_simple",               # Level 1 simple line, starting off-screen, moving to middle of the screen, they do not fight back, they do not move
            2: "line_dense",                # Level 2, dense line, starting off-screen, moving to middle of the screen, they hold their place 5s, then 1 at a time they kamakize to you, following the player ship X value, upon death, another ship kamikaze
            3: "triangle_stream",           # Level 3, triangle, starting off-screen, moving to middle of the screen, they shoot alternatively one each second
            4: "staggered_left_right",      # Level 3, triangle, starting off-screen, moving to middle of the screen, shooting all at the same time
            5: "v_stream",                  # Level 3, triangle, starting off-screen, moving to middle of the screen, shooting all at the same time
        }

        # Immediately prepare the first wave
        self._start_wave(self.current_wave)

    # ----------------------------------------------------------------------
    # Public API called by Engine
    # ----------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """
        Called every frame by Engine.
        Handles spawning logic and transitions between waves / boss.
        """
        if self.current_wave <= self.total_waves:
            # Handle normal waves
            if not self.wave_active:
                # Start the next wave
                self._start_wave(self.current_wave)

            # Handle timed spawns for the current wave
            self._update_spawning(dt)

            # Check if current wave is completely done
            if self._wave_cleared():
                self.current_wave += 1
                self.wave_active = False
                self.pending_spawns.clear()
                self.spawn_timer = 0.0

        else:
            # All waves done → boss phase
            if not self.boss_spawned:
                self._spawn_boss()
                self.boss_spawned = True

    # ----------------------------------------------------------------------
    # Wave lifecycle
    # ----------------------------------------------------------------------

    def _start_wave(self, wave_index: int) -> None:
        """
        Initialize the given wave: choose pattern, prepare spawn list and timers.
        """
        pattern = self.wave_patterns.get(wave_index, "line_simple")
        width = self.engine.screen_width

        self.wave_active = True
        self.pending_spawns.clear()
        self.spawn_timer = 0.0

        if pattern == "line_simple":
            # All at once, simple horizontal line
            num_enemies = 4 + wave_index  # slightly increasing
            self._spawn_line(num_enemies, y=-60)

        elif pattern == "line_dense":
            # More enemies in a line, maybe lower on the screen
            num_enemies = 6 + wave_index
            self._spawn_line(num_enemies, y=-80)

        elif pattern == "triangle_stream":
            # Triangle formation, but spawned ONE BY ONE over time
            self._prepare_triangle_stream()
            self.spawn_interval = 0.7   # seconds between enemies

        elif pattern == "staggered_left_right":
            # Left-right stagger pattern streaming in
            self._prepare_staggered_stream()
            self.spawn_interval = 0.5

        elif pattern == "v_stream":
            # V-shaped formation spawning in sequence
            self._prepare_v_stream()
            self.spawn_interval = 0.5

        else:
            # Fallback: simple line
            self._spawn_line(5 + wave_index, y=-60)

    # ----------------------------------------------------------------------
    # Spawn pattern helpers
    # ----------------------------------------------------------------------

    def _spawn_line(self, num_enemies: int, y: int) -> None:
        """
        Spawn a full line of enemies at once.
        """
        width = self.engine.screen_width
        spacing = width // (num_enemies + 1)

        for i in range(num_enemies):
            x = spacing * (i + 1)
            enemy = EnemyShip(x, y, enemy_type="basic")
            self.engine.enemies.append(enemy)

    def _prepare_triangle_stream(self) -> None:
        """
        Prepare positions for a triangle formation, but do NOT spawn yet.
        They will be spawned one by one over time in _update_spawning().
        """
        width = self.engine.screen_width
        center_x = width // 2
        base_y = -50
        row_spacing = 40
        col_spacing = 40

        positions: List[Tuple[float, float]] = []

        # Row 1 (apex)
        positions.append((center_x, base_y))

        # Row 2
        positions.append((center_x - col_spacing, base_y + row_spacing))
        positions.append((center_x + col_spacing, base_y + row_spacing))

        # Row 3
        positions.append((center_x - 2 * col_spacing, base_y + 2 * row_spacing))
        positions.append((center_x,                 base_y + 2 * row_spacing))
        positions.append((center_x + 2 * col_spacing, base_y + 2 * row_spacing))

        # Optional row 4 if you want more difficulty:
        # positions.append((center_x, base_y + 3 * row_spacing))

        # Enemies will spawn in this order
        self.pending_spawns.extend(positions)

    def _prepare_staggered_stream(self) -> None:
        """
        Prepare a zig-zag / staggered pattern entering one by one.
        """
        width = self.engine.screen_width
        left_x = int(width * 0.2)
        right_x = int(width * 0.8)
        base_y = -40
        row_spacing = 30

        positions: List[Tuple[float, float]] = []

        # Alternating left / right positions going down
        side = "left"
        for i in range(8):
            y = base_y + i * row_spacing
            x = left_x if side == "left" else right_x
            positions.append((x, y))
            side = "right" if side == "left" else "left"

        self.pending_spawns.extend(positions)

    def _prepare_v_stream(self) -> None:
        """
        Prepare a 'V' shape entering point-first, one enemy at a time.
        """
        width = self.engine.screen_width
        center_x = width // 2
        base_y = -40
        row_spacing = 35
        col_spacing = 45

        positions: List[Tuple[float, float]] = [(center_x, base_y)]

        # Next rows of the V
        for i in range(1, 5):
            y = base_y + i * row_spacing
            positions.append((center_x - i * col_spacing, y))
            positions.append((center_x + i * col_spacing, y))

        self.pending_spawns.extend(positions)

    # ----------------------------------------------------------------------
    # Spawning updates and wave completion
    # ----------------------------------------------------------------------

    def _update_spawning(self, dt: float) -> None:
        """
        For patterns that spawn enemies over time, handle timers and spawn.
        For instant patterns, pending_spawns will be empty and this does nothing.
        """
        if not self.pending_spawns:
            return  # nothing queued

        # Accumulate time and spawn whenever we reach the interval
        self.spawn_timer += dt
        while self.spawn_timer >= self.spawn_interval and self.pending_spawns:
            self.spawn_timer -= self.spawn_interval
            x, y = self.pending_spawns.pop(0)
            enemy = EnemyShip(x, y, enemy_type="basic")
            self.engine.enemies.append(enemy)

    def _wave_cleared(self) -> bool:
        """
        A wave is cleared when:
          - no pending spawns AND
          - no alive non-boss enemies remain.
        """
        if self.pending_spawns:
            return False

        for e in self.engine.enemies:
            if isinstance(e, Boss):
                continue
            if e.alive:
                return False

        return True

    # ----------------------------------------------------------------------
    # Boss
    # ----------------------------------------------------------------------

    def _spawn_boss(self) -> None:
        """
        Spawn the final boss in the center top area.
        """
        boss = Boss(self.engine.screen_width // 2, 80)
        self.engine.enemies.append(boss)
