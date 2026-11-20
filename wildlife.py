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


@lru_cache(maxsize=32)
def resident_sprite(kind, size, flashing):
    spec = RESIDENTS[kind]
    rows = spec.pixels
    palette = ((255, 255, 255) if flashing else spec.color,
               tuple(min(255, c + 40) for c in spec.color), (255, 237, 121), (44, 35, 55))
    image = pygame.Surface((max(map(len, rows)), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell != '.':
                image.set_at((x, y), palette[int(cell)-1])
    return pygame.transform.scale(image, (2*size+4, 2*size+2))
