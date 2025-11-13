# waves.py
from Boss import Boss
from EnemyShip import EnemyShip
from Engine import Engine


class WaveFormation:
    """
    Controls enemy waves.
    Responsible for spawning enemies and the final boss.
    """

    def __init__(self, engine: "Engine"):
        self.engine = engine
        self.current_wave = 1
        self.total_waves = 5
        self.boss_spawned = False

    def update(self, dt: float) -> None:
        """
        Called by Engine. Checks if wave is cleared, spawns next one or boss.
        """
        if self.current_wave <= self.total_waves:
            if self._wave_cleared():
                self.current_wave += 1
                self._spawn_wave(self.current_wave)
        else:
            # Boss phase
            if not self.boss_spawned:
                self._spawn_boss()
                self.boss_spawned = True

    def _wave_cleared(self) -> bool:
        # Consider wave cleared when no non-boss enemies remain
        for e in self.engine.enemies:
            if not isinstance(e, Boss) and e.alive:
                return False
        return True

    def _spawn_wave(self, wave_index: int) -> None:
        # Example simple columns of enemies
        width = self.engine.screen_width
        num_enemies = 5 + wave_index  # increase density
        spacing = width // (num_enemies + 1)

        for i in range(num_enemies):
            x = spacing * (i + 1)
            y = 50  # start near top
            enemy = EnemyShip(x, y, enemy_type="basic")
            self.engine.enemies.append(enemy)

    def _spawn_boss(self) -> None:
        boss = Boss(self.engine.screen_width // 2, 80)
        self.engine.enemies.append(boss)
