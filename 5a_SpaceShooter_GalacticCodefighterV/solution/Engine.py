import math

import pygame
from typing import List, Optional

from Boss import Boss
from Bullet import Bullet
from EnemyShip import EnemyShip
from PlayerShip import PlayerShip
from SpaceAI import SpaceAI
from WaveFormation import WaveFormation
from ai_api import AICommand, NavigationStatus, GameState, PlayerState, EnemyState, BulletState, WaveState


class Engine:
    def __init__(self, screen_width: int = 480, screen_height: int = 640):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Galactic Code Fighter V")

        self.clock = pygame.time.Clock()
        self.running = True

        # Entities
        self.player = PlayerShip(screen_width // 2, screen_height - 80)
        self.enemies: List[EnemyShip] = []
        self.bullets: List[Bullet] = []

        # Waves
        self.waves = WaveFormation(self)

        # AI
        self.ai = SpaceAI()
        self.ai_timer = 0.0
        self.ai_interval = 0.5  # seconds
        self.current_command = AICommand(False, self.player.x, self.player.y, False)

        # Navigation state
        self.current_destination: Optional[tuple[float, float]] = None

        # Game progression
        self.time = 0.0
        self.game_won = False

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.time += dt
            self._handle_events()
            self._update(dt)
            self._draw()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def _update(self, dt: float) -> None:
        # Update waves
        self.waves.update(dt)

        # AI decision every 0.5s
        self.ai_timer += dt
        nav_status = self._compute_navigation_status()

        if self.ai_timer >= self.ai_interval and not self.game_won:
            self.ai_timer -= self.ai_interval
            state = self._build_game_state(nav_status)
            self.current_command = self.ai.decide(state)

            if self.current_command.set_destination:
                self.current_destination = (
                    self.current_command.dest_x,
                    self.current_command.dest_y,
                )
                self.player.set_destination(*self.current_destination)

        # Handle shooting requested by AI
        if self.current_command.shoot and self.player.request_shot():
            bullet = Bullet(self.player.x + self.player.width // 2, self.player.y, 0, -300.0, from_player=True)
            self.bullets.append(bullet)

        # Update entities
        self.player.update(dt)

        for e in self.enemies:
            e.update(dt)

        for b in self.bullets:
            b.update(dt)

        # Collision handling, clean-up, win condition...
        self._handle_collisions()
        self._cleanup()
        self._check_win_condition()

    def _draw(self) -> None:
        self.screen.fill((0, 0, 0))

        if self.game_won:
            self._draw_win_screen()
        else:
            self.player.draw(self.screen)
            for e in self.enemies:
                e.draw(self.screen)
            for b in self.bullets:
                b.draw(self.screen)

        pygame.display.flip()

    def _compute_navigation_status(self) -> NavigationStatus:
        if self.current_destination is None:
            return NavigationStatus(
                has_destination=False,
                dest_x=self.player.x,
                dest_y=self.player.y,
                reached=True,
                distance=0.0,
            )

        dest_x, dest_y = self.current_destination
        distance = math.hypot(dest_x - self.player.x, dest_y - self.player.y)
        reached = distance < 5.0  # tolerance

        return NavigationStatus(
            has_destination=True,
            dest_x=dest_x,
            dest_y=dest_y,
            reached=reached,
            distance=distance,
        )

    def _build_game_state(self, nav_status: NavigationStatus) -> GameState:
        # Adapt engine objects -> light snapshot classes for AI
        player_state = PlayerState(
            x=self.player.x,
            y=self.player.y,
            hp=self.player.hp,
            lives=1,  # or more if you add them
            can_shoot=self.player.can_shoot(),
            cooldown=max(0.0, self.player.shoot_cooldown - self.player.time_since_last_shot),
        )

        enemies_state = [
            EnemyState(
                x=e.x,
                y=e.y,
                hp=e.hp,
                enemy_type=e.enemy_type,
            )
            for e in self.enemies
            if e.alive
        ]

        player_bullets_state = [
            BulletState(b.x, b.y, b.vx, b.vy, b.from_player)
            for b in self.bullets
            if b.from_player
        ]

        enemy_bullets_state = [
            BulletState(b.x, b.y, b.vx, b.vy, b.from_player)
            for b in self.bullets
            if not b.from_player
        ]

        # Simple wave/boss info
        boss_hp = None
        for e in self.enemies:
            if isinstance(e, Boss) and e.alive:
                boss_hp = e.hp
                break

        wave_state = WaveState(
            current_wave=self.waves.current_wave,
            enemies_remaining=len([e for e in self.enemies if e.alive and not isinstance(e, Boss)]),
            boss_hp=boss_hp,
        )

        return GameState(
            width=self.screen_width,
            height=self.screen_height,
            time=self.time,
            player=player_state,
            enemies=enemies_state,
            player_bullets=player_bullets_state,
            enemy_bullets=enemy_bullets_state,
            wave=wave_state,
            navigation=nav_status,
        )

    def _handle_collisions(self) -> None:
        """
        Handle all collisions using basic rectangle overlap:
          - Player bullets vs enemies
          - Enemy bullets vs player
          - Enemies vs player (ramming)
        """

        # ---------------------------------------------------------
        # 1. Player bullets → Enemy ships
        # ---------------------------------------------------------
        for bullet in self.bullets:
            if not bullet.alive or not bullet.from_player:
                continue

            for enemy in self.enemies:
                if not enemy.alive:
                    continue

                if bullet.rect.colliderect(enemy.rect):
                    enemy.take_damage(1)
                    bullet.alive = False
                    break  # Bullet can only hit one enemy

        # ---------------------------------------------------------
        # 2. Enemy bullets → Player ship
        # ---------------------------------------------------------
        for bullet in self.bullets:
            if not bullet.alive or bullet.from_player:
                continue

            if bullet.rect.colliderect(self.player.rect):
                # Player takes damage
                self.player.take_damage(1)
                bullet.alive = False

        # ---------------------------------------------------------
        # 3. Enemy ships → Player ship (ramming)
        # ---------------------------------------------------------
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            if enemy.rect.colliderect(self.player.rect):
                # Both take damage (classic shmup ramming)
                self.player.take_damage(1)
                enemy.take_damage(9999)  # insta-kill enemy

    def _cleanup(self) -> None:
        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]

    def _check_win_condition(self) -> None:
        # Win when boss is dead and all waves done
        boss_alive = any(isinstance(e, Boss) and e.alive for e in self.enemies)
        if self.waves.current_wave > self.waves.total_waves and not boss_alive:
            self.game_won = True

    def _draw_win_screen(self) -> None:
        # Winning screen + flag
        font = pygame.font.SysFont("arial", 30)
        text_surface = font.render("YOU WIN!", True, (0, 255, 0))
        flag_surface = font.render("FLAG: MEDIUM5_SPACESHOOTER_AI", True, (255, 255, 0))

        rect1 = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 30))
        rect2 = flag_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 30))

        self.screen.blit(text_surface, rect1)
        self.screen.blit(flag_surface, rect2)

