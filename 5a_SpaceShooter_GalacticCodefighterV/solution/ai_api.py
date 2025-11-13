from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AICommand:
    # If True, engine updates its internal destination to (dest_x, dest_y).
    # If False, engine keeps the previous destination and just uses `shoot`.
    set_destination: bool
    dest_x: float
    dest_y: float

    # Shooting is independent of moving.
    shoot: bool


@dataclass(frozen=True)
class PlayerState:
    x: float
    y: float
    hp: int
    lives: int
    can_shoot: bool
    cooldown: float  # seconds until next allowed shot


@dataclass(frozen=True)
class EnemyState:
    x: float
    y: float
    hp: int
    enemy_type: str  # "basic", "kamikaze", "boss", etc.


@dataclass(frozen=True)
class BulletState:
    x: float
    y: float
    vx: float
    vy: float
    from_player: bool


@dataclass(frozen=True)
class WaveState:
    current_wave: int        # 1-5 = regular, 6 = boss, etc.
    enemies_remaining: int
    boss_hp: Optional[int]   # None if no boss on screen


@dataclass(frozen=True)
class NavigationStatus:
    has_destination: bool
    dest_x: float
    dest_y: float
    reached: bool            # True on the frame we first consider it “arrived”
    distance: float          # current distance to the destination


@dataclass(frozen=True)
class GameState:
    width: int
    height: int
    time: float              # game time in seconds
    player: PlayerState
    enemies: List[EnemyState]
    player_bullets: List[BulletState]
    enemy_bullets: List[BulletState]
    wave: WaveState
    navigation: NavigationStatus
