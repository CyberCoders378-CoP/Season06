from typing import List
import pygame

from UtilityFunctions import UtilityFunctions
from Config import Config
from Bullet import Bullet
from Target import Target
from InstructionStream import InstructionStream


class Game:
    def __init__(self, targets: List[Target], instr: List[str]):
        pygame.init()
        pygame.display.set_caption("Medium3 – Moving Targets, Raygun Shots (OOP)")
        self.screen = pygame.display.set_mode((Config.SCREEN_W, Config.SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 22)

        self.targets = targets
        self.instructions = InstructionStream(instr)
        self.running = True

        # timing
        self.last_step_time = 0
        self.sim_time_ms = 0

        # bullets fired
        self.bullets: List[Bullet] = []

        # score
        self.score = 0
        self.hits = 0
        self.shots_fired = 0
        self.step_count = 0

    # ----- core loop -----
    def run(self):
        while self.running:
            dt_ms = self.clock.tick(60)
            self.sim_time_ms += dt_ms

            self.handle_events()
            self.update(16.67 / 1000.0)  # seconds
            self.draw()

        print(f"Final Score for the game after {self.shots_fired} shots : {self.score}pts")
        pygame.quit()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False

    # ----- update world -----
    def update(self, dt_sec: float):
        # 1) Continuous motion for all targets
        for t in self.targets:
            t.update(dt_sec)

        # 2) One instruction per second
        now = self.sim_time_ms
        if (now - self.last_step_time) >= Config.STEP_DELAY_MS:
            self.process_next_instruction()
            self.last_step_time = now
            self.step_count += 1

    def process_next_instruction(self):
        line = self.instructions.next()
        if not line:
            return

        parts = line.split(",")

        sx = float(parts[0])
        sy = float(parts[1])

        bullet = Bullet(sx, sy)
        self.bullets.append(bullet)
        self.shots_fired += 1

        # Raygun: resolve hit AT THE MOMENT of the shot (or across lifetime if configured)
        self.resolve_hits_at_point(sx, sy)

        bullet.alive = False

    def resolve_hits_at_point(self, sx: float, sy: float):
        # any target within TARGET_RADIUS (world units) is removed and scored
        hits_this_shot = 0
        for t in self.targets:
            if not t.alive:
                continue

            if t.distance_to(sx, sy) <= Config.TARGET_RADIUS:
                t.alive = False
                hits_this_shot += 1

        if hits_this_shot:
            self.hits += hits_this_shot
            self.score += hits_this_shot * Config.SCORE_PER_HIT

    # ----- rendering -----
    def draw(self):
        self.screen.fill(Config.BG_COLOR)

        # draw an outer "board" like Easy3 (just the world frame)
        self._draw_frame()

        # draw targets
        for t in self.targets:
            t.draw(self.screen)

        # draw bullets (if persistent)
        for b in self.bullets:
            b.draw(self.screen)

        # HUD
        self._draw_hud()

        pygame.display.flip()

    def _draw_frame(self):
        # three cosmetic rings around the world center (optional, like Easy3 vibe)
        cx, cy = UtilityFunctions.world_to_screen(0.0, 0.0)
        pygame.draw.circle(self.screen, Config.RING_OUTER, (cx, cy), UtilityFunctions.world_radius_to_pixels(900), width=2)
        pygame.draw.circle(self.screen, Config.RING_INNER, (cx, cy), UtilityFunctions.world_radius_to_pixels(600), width=2)
        pygame.draw.circle(self.screen, Config.RING_BULL, (cx, cy), UtilityFunctions.world_radius_to_pixels(300), width=2)
        pygame.draw.circle(self.screen, Config.CENTER_DOT, (cx, cy), 3)

    def _draw_hud(self):
        lines = [
            f"Time: {self.sim_time_ms/1000.0:7.2f}s",
            f"Step (1/s): {self.step_count}",
            f"Shots: {self.shots_fired}",
            f"Hits: {self.hits}",
            f"Score: {self.score}",
            "ESC/Q to quit",
        ]

        x, y = 12, 10
        for line in lines:
            surf = self.font.render(line, True, Config.HUD_COLOR)
            self.screen.blit(surf, (x, y))
            y += surf.get_height() + 4
