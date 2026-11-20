# world.py — Мир с декорациями и следами скольжения

import pygame
import random
import math
from functools import lru_cache
from settings import *
from biomes import BIOMES, prop_sprite


class Decoration:
    """Декоративный элемент на карте"""
    def __init__(self, x, y, deco_type, biome, rng):
        self.x = x
        self.y = y
        self.deco_type = deco_type
        self.anim_offset = rng.random() * 10
        self.size = rng.uniform(0.8, 1.2)

        self.sprite = (prop_sprite(deco_type, biome.ink, rng.choice((2, 2, 3)), rng.choice((True, False)))
                       if deco_type in biome.props else None)

    def draw(self, screen, camera, game_time):
        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if getattr(camera, "culling_enabled", True) and (sx < -30 or sx > SCREEN_WIDTH + 30 or sy < -30 or sy > SCREEN_HEIGHT + 30):
            return

        if self.sprite is not None:
            screen.blit(self.sprite, self.sprite.get_rect(midbottom=(sx, sy)))
        elif self.deco_type == "grass":
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

        if getattr(camera, "culling_enabled", True) and (sx < -20 or sx > SCREEN_WIDTH + 20 or sy < -20 or sy > SCREEN_HEIGHT + 20):
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
    def __init__(self, seed=None):
        self.seed = random.randrange(2**31) if seed is None else seed
        self.biomes = list(BIOMES)
        random.Random(self.seed).shuffle(self.biomes)
        # Instance-local bounded caches do not retain worlds from previous runs.
        self._random_at = lru_cache(maxsize=4096)(self._random_at)
        self._site = lru_cache(maxsize=1024)(self._site)
        self.ground_color_at = lru_cache(maxsize=8192)(self.ground_color_at)
        self.terrain_tile = lru_cache(maxsize=768)(self.terrain_tile)

        # Кэш декораций по чанкам
        self.decoration_cache = {}
        self.chunk_size = 512

        # Следы скольжения
        self.slide_trails = []

    def _random_at(self, x, y, salt=0):
        # Stable integer mixer; independent of Python hash randomisation.
        n = (x * 374761393 + y * 668265263 + self.seed * 1442695041 + salt * 1274126177) & 0xffffffff
        n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
        return (n ^ (n >> 16)) / 4294967295

    def _noise(self, x, y, scale, salt):
        x, y = x / scale, y / scale
        ix, iy = math.floor(x), math.floor(y)
        u, v = x - ix, y - iy
        u, v = u*u*u*(u*(u*6-15)+10), v*v*v*(v*(v*6-15)+10)
        a, b = self._random_at(ix, iy, salt), self._random_at(ix+1, iy, salt)
        c, d = self._random_at(ix, iy+1, salt), self._random_at(ix+1, iy+1, salt)
        return (a+(b-a)*u)*(1-v) + (c+(d-c)*u)*v

    def _site(self, cx, cy):
        size = 1500
        return ((cx + .15 + .7*self._random_at(cx, cy, 1))*size,
                (cy + .15 + .7*self._random_at(cx, cy, 2))*size,
                .75 + .5*self._random_at(cx, cy, 3),
                self.biomes[min(9, int(self._random_at(cx, cy, 4)*10))])

    def _regions(self, x, y):
        # Low-frequency domain warp bends the cellular borders organically.
        x, y = (x + 620*(self._noise(x, y, 1800, 5)-.5),
                y + 620*(self._noise(x, y, 1800, 6)-.5))
        cx, cy = math.floor(x/1500), math.floor(y/1500)
        distances = {}
        regions = {}
        for yy in range(cy-2, cy+3):
            for xx in range(cx-2, cx+3):
                sx, sy, weight, biome = self._site(xx, yy)
                distance = math.hypot(x-sx, y-sy)/weight
                key = biome.key
                regions[key] = biome
                if key not in distances or distance < distances[key]:
                    distances[key] = distance
        return sorted(((regions[key], dist) for key, dist in distances.items()), key=lambda pair: pair[1])

    def biome_for_chunk(self, cx, cy):
        """Representative biome at the chunk centre (chunks may contain borders)."""
        return self.biome_at((cx+.5)*self.chunk_size, (cy+.5)*self.chunk_size)

    def biome_at(self, x, y):
        # Habitat queries only need the closest site: no sorting, square roots
        # or hashing the complete frozen Biome dataclass on every enemy tick.
        x, y = (x + 620*(self._noise(x, y, 1800, 5)-.5),
                y + 620*(self._noise(x, y, 1800, 6)-.5))
        cx, cy = math.floor(x/1500), math.floor(y/1500)
        best, nearest = None, float('inf')
        for yy in range(cy-2, cy+3):
            for xx in range(cx-2, cx+3):
                sx, sy, weight, biome = self._site(xx, yy)
                distance = ((x-sx)**2 + (y-sy)**2)/(weight*weight)
                if distance < nearest:
                    best, nearest = biome, distance
        return best

    def ground_color_at(self, x, y, blend=220, shading=True):
        regions = self._regions(x, y)
        nearest = regions[0][1]
        weights = [(biome, max(0, 1-(dist-nearest)/blend)**2) for biome, dist in regions]
        total = sum(weight for _, weight in weights)
        depth = (1 - .085*self._noise(x, y, 950, 7) - .025*self._noise(x, y, 310, 8)) if shading else 1
        return tuple(round(sum(b.ground[i]*w for b, w in weights)/total*depth) for i in range(3))

    def terrain_tile(self, tx, ty, quality='medium', blend=220, shading=True):
        # Shared edge samples prevent seams. Low uses a continuous bilinear
        # gradient (four corners), not abrupt single-colour biome squares.
        samples = {'low': 2, 'medium': 3, 'high': 5}[quality]
        small = pygame.Surface((samples, samples))
        for y in range(samples):
            for x in range(samples):
                small.set_at((x, y), self.ground_color_at(
                    (tx+x/(samples-1))*TILE_SIZE, (ty+y/(samples-1))*TILE_SIZE, blend, shading))
        tile = pygame.transform.smoothscale(small, (TILE_SIZE, TILE_SIZE))
        return tile.convert() if pygame.display.get_surface() else tile

    def get_decorations_for_chunk(self, cx, cy):
        """Получить/сгенерировать декорации для чанка"""
        key = (cx, cy)
        if key not in self.decoration_cache:
            rng = random.Random(hash((self.seed, cx, cy)))
            decos = []
            for _ in range(rng.randint(14, 22)):
                dx, dy = rng.randrange(self.chunk_size), rng.randrange(self.chunk_size)
                biome = self.biome_at(cx*self.chunk_size + dx, cy*self.chunk_size + dy)
                kind = rng.choice(biome.props if rng.random() < 0.65 else biome.scatter)
                decos.append(Decoration(cx*self.chunk_size + dx, cy*self.chunk_size + dy,
                                        kind, biome, rng))
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

    def draw(self, screen, camera, game_time=0, settings=None):
        """Нарисовать мир"""
        # Тайлы
        start_x = int(camera.offset_x // TILE_SIZE) - 1
        start_y = int(camera.offset_y // TILE_SIZE) - 1
        end_x = start_x + (SCREEN_WIDTH // TILE_SIZE) + 3
        end_y = start_y + (SCREEN_HEIGHT // TILE_SIZE) + 3

        quality = settings.get('terrain_quality', 'medium') if settings else 'medium'
        blend = settings.get('biome_blend', 220) if settings else 220
        shading = settings.get('terrain_shading', True) if settings else True
        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                tile = self.terrain_tile(tx, ty, quality, blend, shading)
                screen_x = tx * TILE_SIZE - camera.offset_x
                screen_y = ty * TILE_SIZE - camera.offset_y
                screen.blit(tile, (int(screen_x), int(screen_y)))

        # Следы скольжения
        if settings is None or settings.get("slide_trails"):
            for trail in self.slide_trails:
                trail.draw(screen, camera)

        # Декорации
        if settings is not None and not settings.get("decorations"):
            return
        chunk_start_x = int((camera.offset_x - 100) // self.chunk_size)
        chunk_start_y = int((camera.offset_y - 100) // self.chunk_size)
        chunk_end_x = int((camera.offset_x + SCREEN_WIDTH + 100) // self.chunk_size)
        chunk_end_y = int((camera.offset_y + SCREEN_HEIGHT + 100) // self.chunk_size)

        density = settings.get('decoration_density', 1) if settings else 1
        animation_time = game_time if settings is None or settings.get('animated_decorations', True) else 0
        for cy in range(chunk_start_y, chunk_end_y + 1):
            for cx in range(chunk_start_x, chunk_end_x + 1):
                decos = self.get_decorations_for_chunk(cx, cy)
                for deco in decos[:max(1, round(len(decos)*density))]:
                    deco.draw(screen, camera, animation_time)
