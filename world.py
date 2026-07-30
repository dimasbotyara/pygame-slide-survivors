# world.py — Мир с декорациями и следами скольжения

import pygame
import random
import math
from settings import *


class Decoration:
    """Декоративный элемент на карте"""
    def __init__(self, x, y, deco_type):
        self.x = x
        self.y = y
        self.deco_type = deco_type
        self.anim_offset = random.random() * 10
        self.size = random.uniform(0.8, 1.2)

    def draw(self, screen, camera, game_time):
        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if sx < -30 or sx > SCREEN_WIDTH + 30 or sy < -30 or sy > SCREEN_HEIGHT + 30:
            return

        if self.deco_type == "grass":
            sway = math.sin(game_time * 2 + self.anim_offset) * 3
            h = int(12 * self.size)
            pygame.draw.line(screen, (60, 120, 40),
                           (sx, sy), (int(sx + sway), sy - h), 2)
            pygame.draw.line(screen, (50, 110, 35),
                           (sx + 3, sy), (int(sx + 3 + sway * 0.7), sy - h + 3), 2)

        elif self.deco_type == "rock":
            s = int(6 * self.size)
            points = [
                (sx - s, sy + s // 2),
                (sx - s // 2, sy - s // 2),
                (sx + s // 3, sy - s),
                (sx + s, sy - s // 3),
                (sx + s // 2, sy + s // 2),
            ]
            pygame.draw.polygon(screen, (80, 80, 75), points)
            pygame.draw.polygon(screen, (60, 60, 55), points, 1)

        elif self.deco_type == "flower":
            sway = math.sin(game_time * 1.5 + self.anim_offset) * 2
            # Стебель
            pygame.draw.line(screen, (40, 100, 30),
                           (sx, sy), (int(sx + sway), sy - 10), 2)
            # Лепестки
            colors = [(255, 100, 100), (255, 200, 50), (200, 100, 255), (255, 150, 200)]
            petal_color = colors[int(self.anim_offset) % len(colors)]
            pygame.draw.circle(screen, petal_color,
                             (int(sx + sway), sy - 12), int(4 * self.size))
            pygame.draw.circle(screen, YELLOW,
                             (int(sx + sway), sy - 12), int(2 * self.size))

        elif self.deco_type == "mushroom":
            # Ножка
            pygame.draw.rect(screen, (200, 190, 170),
                           (sx - 2, sy - 4, 4, 8))
            # Шляпка
            s = int(6 * self.size)
            pygame.draw.ellipse(screen, (180, 50, 50),
                              (sx - s, sy - 8 - s // 2, s * 2, s))
            # Точки
            pygame.draw.circle(screen, WHITE, (sx - 2, sy - 8), 2)
            pygame.draw.circle(screen, WHITE, (sx + 3, sy - 10), 1)

        elif self.deco_type == "bones":
            c = (180, 170, 150)
            pygame.draw.line(screen, c, (sx - 5, sy - 3), (sx + 5, sy + 3), 2)
            pygame.draw.line(screen, c, (sx - 5, sy + 3), (sx + 5, sy - 3), 2)
            pygame.draw.circle(screen, c, (sx - 5, sy - 3), 2)
            pygame.draw.circle(screen, c, (sx + 5, sy - 3), 2)
            pygame.draw.circle(screen, c, (sx - 5, sy + 3), 2)
            pygame.draw.circle(screen, c, (sx + 5, sy + 3), 2)


class SlideTrail:
    """След от скольжения на земле"""
    def __init__(self, x, y, angle, speed_ratio):
        self.x = x
        self.y = y
        self.angle = angle
        self.lifetime = SLIDE_TRAIL_DURATION
        self.max_lifetime = SLIDE_TRAIL_DURATION
        self.width = max(4, int(12 * speed_ratio))
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive:
            return

        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if sx < -20 or sx > SCREEN_WIDTH + 20 or sy < -20 or sy > SCREEN_HEIGHT + 20:
            return

        alpha_ratio = self.lifetime / self.max_lifetime
        intensity = int(60 * alpha_ratio)
        color = (50 + intensity, 80 + intensity, 120 + intensity)

        length = 8
        dx = math.cos(self.angle) * length
        dy = math.sin(self.angle) * length

        width = max(1, int(self.width * alpha_ratio))
        pygame.draw.line(screen, color,
                        (int(sx - dx), int(sy - dy)),
                        (int(sx + dx), int(sy + dy)), width)


class World:
    """Бесконечный мир с декорациями и следами"""
    def __init__(self):
        self.tile_surface_1 = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.tile_surface_1.fill(GROUND_COLOR_1)

        self.tile_surface_2 = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.tile_surface_2.fill(GROUND_COLOR_2)

        self._add_tile_details(self.tile_surface_1, GROUND_COLOR_1)
        self._add_tile_details(self.tile_surface_2, GROUND_COLOR_2)

        # Кэш декораций по чанкам
        self.decoration_cache = {}
        self.chunk_size = 512

        # Следы скольжения
        self.slide_trails = []

    def _add_tile_details(self, surface, base_color):
        rng = random.Random(hash(base_color))
        for _ in range(5):
            x = rng.randint(2, TILE_SIZE - 2)
            y = rng.randint(2, TILE_SIZE - 2)
            detail_color = (
                min(255, base_color[0] + rng.randint(3, 12)),
                min(255, base_color[1] + rng.randint(3, 12)),
                min(255, base_color[2] + rng.randint(3, 12)),
            )
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < TILE_SIZE and 0 <= ny < TILE_SIZE:
                        if rng.random() < 0.6:
                            surface.set_at((nx, ny), detail_color)

    def get_decorations_for_chunk(self, cx, cy):
        """Получить/сгенерировать декорации для чанка"""
        key = (cx, cy)
        if key not in self.decoration_cache:
            rng = random.Random(hash(key) + 42)
            decos = []
            for _ in range(int(self.chunk_size * self.chunk_size * DECORATION_DENSITY / 1000)):
                if rng.random() < DECORATION_DENSITY * 10:
                    dx = rng.randint(0, self.chunk_size)
                    dy = rng.randint(0, self.chunk_size)
                    deco_type = rng.choice(DECORATION_TYPES)
                    decos.append(Decoration(
                        cx * self.chunk_size + dx,
                        cy * self.chunk_size + dy,
                        deco_type
                    ))
            self.decoration_cache[key] = decos

            # Очистка кэша (хранить максимум 50 чанков)
            if len(self.decoration_cache) > 50:
                keys = list(self.decoration_cache.keys())
                for old_key in keys[:10]:
                    del self.decoration_cache[old_key]

        return self.decoration_cache[key]

    def add_slide_trail(self, x, y, angle, speed_ratio):
        """Добавить след скольжения"""
        self.slide_trails.append(SlideTrail(x, y, angle, speed_ratio))

    def update(self, dt):
        """Обновить следы"""
        for trail in self.slide_trails:
            trail.update(dt)
        self.slide_trails = [t for t in self.slide_trails if t.alive]

        # Ограничить кол-во следов
        if len(self.slide_trails) > 500:
            self.slide_trails = self.slide_trails[-500:]

    def draw(self, screen, camera, game_time=0):
        """Нарисовать мир"""
        # Тайлы
        start_x = int(camera.offset_x // TILE_SIZE) - 1
        start_y = int(camera.offset_y // TILE_SIZE) - 1
        end_x = start_x + (SCREEN_WIDTH // TILE_SIZE) + 3
        end_y = start_y + (SCREEN_HEIGHT // TILE_SIZE) + 3

        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                if (tx + ty) % 2 == 0:
                    tile = self.tile_surface_1
                else:
                    tile = self.tile_surface_2

                screen_x = tx * TILE_SIZE - camera.offset_x
                screen_y = ty * TILE_SIZE - camera.offset_y
                screen.blit(tile, (int(screen_x), int(screen_y)))

        # Следы скольжения
        for trail in self.slide_trails:
            trail.draw(screen, camera)

        # Декорации
        chunk_start_x = int((camera.offset_x - 100) // self.chunk_size) - 1
        chunk_start_y = int((camera.offset_y - 100) // self.chunk_size) - 1
        chunk_end_x = int((camera.offset_x + SCREEN_WIDTH + 100) // self.chunk_size) + 1
        chunk_end_y = int((camera.offset_y + SCREEN_HEIGHT + 100) // self.chunk_size) + 1

        for cy in range(chunk_start_y, chunk_end_y + 1):
            for cx in range(chunk_start_x, chunk_end_x + 1):
                decos = self.get_decorations_for_chunk(cx, cy)
                for deco in decos:
                    deco.draw(screen, camera, game_time)