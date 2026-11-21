"""Biome residents. Existing combat archetypes supply wind-ups and attacks."""
from dataclasses import dataclass
from functools import lru_cache

import pygame


@dataclass(frozen=True)
class Resident:
    biome: str
    archetype: str
    color: tuple
    traits: dict
    pixels: tuple  # body, highlight, eye, dark marking


RESIDENTS = {
    'clover_moth': Resident('meadow', 'skirmisher', (141, 207, 106), dict(hp=18, speed=105), (
        '22.....22', '212...212', '211141112', '.2114112.', '..33333..', '.1141411.', '211.4.112')),
    'sand_scorpion': Resident('dunes', 'sprinter', (221, 154, 76), dict(sprint_speed=270, sprint_cooldown=3.2), (
        '1.1...1.1', '121...121', '.1.313.1.', '..11111..', '.1424212.', '..1111..2', '.1.111.11', '.....111.')),
    'rime_lynx': Resident('glacier', 'ghoul', (139, 206, 226), dict(hp=30, strike_radius=26), (
        '21.....12', '211...112', '.2111112.', '.1344431.', '..12221..', '..11411..', '.1122211.', '22.....22')),
    'reed_toad': Resident('marsh', 'shooter', (113, 173, 98), dict(shoot_speed=155, shoot_range=196, damage=7), (
        '..33.33..', '.2141412.', '.2111112.', '111444111', '.2222222.', '..11111..', '222...222')),
    'thorn_stag': Resident('grove', 'sprinter', (207, 112, 91), dict(hp=42, sprint_duration=0.28, damage=9), (
        '2.2...2.2', '222...222', '..2...2..', '.1111111.', '..31413..', '..11111..', '...242...', '..11.11..')),
    'cinder_slug': Resident('basalt', 'exploder', (221, 107, 76), dict(speed=48, explode_radius=65, explode_damage=18), (
        '2.2......', '1.1..22..', '333.2112.', '111211412', '111141411', '.22111111', '..2222222')),
    'echo_bat': Resident('cavern', 'prism', (181, 142, 220), dict(hp=20, shot_offsets=(-0.15, 0.15), damage=6), (
        '2.......2', '21.1.1.12', '211111112', '.2134312.', '..11111..', '..2.1.2..', '....2....')),
    'tide_crab': Resident('coast', 'crusher', (223, 152, 116), dict(hp=50, strike_radius=46, damage=10, windup=0.32), (
        '1.2...2.1', '222...222', '.1.3.3.1.', '..11111..', '.1222221.', '114111411', '11.....11')),
    'gear_mite': Resident('foundry', 'tank', (160, 171, 164), dict(hp=65, speed=55, size=15, damage=10), (
        '...22....', '.221122..', '.144441..', '221333122', '211111112', '.122221..', '.42..24..', '22....22.')),
    'rune_wisp': Resident('ruins', 'ghost', (171, 191, 116), dict(hp=33, speed=68, strike_radius=31), (
        '....2....', '...212...', '..21112..', '.2134312.', '..21412..', '...212...', '..2.1.2..', '.2...2...')),
}
RESIDENT_BY_BIOME = {spec.biome: kind for kind, spec in RESIDENTS.items()}


@lru_cache(maxsize=256)
def resident_sprite(kind, size, flashing, frame=0):
    """Four pixel-art gait frames, cached and shared by residents of a type.

    Flying creatures flap their outer wings; grounded creatures alternate their
    outer feet. The central face/body stays intact and easy to recognise.
    Frame zero is the resting pose and the default for existing callers.
    """
    spec = RESIDENTS[kind]
    rows = spec.pixels
    palette = ((255, 255, 255) if flashing else spec.color,
               tuple(min(255, c + 40) for c in spec.color), (255, 237, 121), (44, 35, 55))
    width, height = max(map(len, rows)), len(rows)
    # Extra transparent pixels give limbs room to move without clipping.
    image = pygame.Surface((width + 2, height + 2), pygame.SRCALPHA)
    flyers = ('clover_moth', 'echo_bat', 'rune_wisp')
    phase = (0, 1, 0, -1)[frame % 4]
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell == '.':
                continue
            dx = dy = 0
            if kind in flyers:
                if x < 3 or x >= width - 3:
                    dy = phase
            elif y >= height - 2 and (x < 3 or x >= width - 3):
                dy = phase if x < width // 2 else -phase
            image.set_at((x + 1 + dx, y + 1 + dy), palette[int(cell)-1])
    return pygame.transform.scale(image, (2*size+4, 2*size+2))


class HabitatFade:
    """Render-only dissolution after a resident leaves its home biome."""
    duration = 0.75

    def __init__(self, enemy):
        self.x, self.y, self.size = enemy.x, enemy.y, enemy.size
        self.elapsed = 0.0
        self.sprite = resident_sprite(enemy.enemy_type, enemy.size, False, enemy.walk_frame)
        # Sample a small pixel grid once; no gameplay RNG or per-frame allocations.
        grid = pygame.transform.scale(self.sprite, (11, 11))
        self.pixels = [(x, y, grid.get_at((x, y))) for y in range(11) for x in range(11)
                       if grid.get_at((x, y)).a]
        self.canvas = pygame.Surface((self.size * 8 + 60, self.size * 8 + 60), pygame.SRCALPHA)

    def update(self, dt):
        self.elapsed += dt
        return self.elapsed < self.duration

    def draw(self, screen, camera):
        progress = min(1.0, self.elapsed / self.duration)
        sx, sy = camera.apply(self.x, self.y)
        # The sprite contracts as coloured pixels drift away, then vanishes.
        width = max(1, round(self.sprite.get_width() * (1 - .8 * progress)))
        height = max(1, round(self.sprite.get_height() * (1 - .8 * progress)))
        image = pygame.transform.scale(self.sprite, (width, height))
        self.canvas.fill((0, 0, 0, 0))
        cx, cy = self.canvas.get_rect().center
        self.canvas.blit(image, image.get_rect(center=(cx, int(cy - progress * 8))))
        cell = max(1, round(self.size / 6 * (1 - progress * .6)))
        for x, y, color in self.pixels:
            # Coordinate-derived drift avoids consuming the game's random stream.
            dx = (x - 5) * (self.size / 6 + progress * 3)
            dy = (y - 5) * (self.size / 6 + progress * 2) - progress * (10 + (x * 7 + y * 3) % 12)
            pygame.draw.rect(self.canvas, color, (int(cx + dx), int(cy + dy), cell, cell))
        self.canvas.set_alpha(round(255 * (1 - progress)))
        screen.blit(self.canvas, self.canvas.get_rect(center=(int(sx), int(sy))))
