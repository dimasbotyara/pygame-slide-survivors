"""Ground palettes and tiny pixel-art props; purely decorative, never pickups."""
from dataclasses import dataclass
from functools import lru_cache
import pygame


@dataclass(frozen=True)
class Biome:
    key: str
    ground: tuple
    ink: tuple  # outline, body, highlight, detail
    props: tuple
    scatter: tuple


BIOMES = (
    Biome('meadow', (37, 58, 45), ('304534','648952','96b66b','e3bf83'), ('clover','daisy'), ('grass','flower')),
    Biome('dunes', (86, 65, 44), ('524731','70905a','a0b475','d3a270'), ('cactus','fossil'), ('rock','bones')),
    Biome('glacier', (47, 71, 86), ('365362','6d95a4','c0d6d6','91c2cb'), ('ice_spire','snowflake'), ('rock',)),
    Biome('marsh', (41, 57, 50), ('354537','678554','98a96a','b98d67'), ('lilypad','cattail'), ('grass','mushroom')),
    Biome('grove', (66, 46, 53), ('49363c','a45e55','d89063','c5a078'), ('maple','stump'), ('grass','mushroom')),
    Biome('basalt', (48, 42, 46), ('332e36','665463','927573','db8359'), ('vent','slag'), ('rock','bones')),
    Biome('cavern', (51, 43, 69), ('483859','866b9d','b5a0bf','85b7b4'), ('geode','stalagmite'), ('rock','mushroom')),
    Biome('coast', (42, 72, 74), ('37525c','977d76','d0ad97','d89979'), ('shell','starfish'), ('rock','grass')),
    Biome('foundry', (52, 56, 61), ('353a43','737f85','a3aba3','b5945d'), ('gear','grate'), ('rock',)),
    Biome('ruins', (62, 60, 48), ('46483e','808372','b0a98a','a9be82'), ('runestone','column'), ('grass','bones')),
)

# Each cell is a pixel. Dots leave the floor visible through small details.
PATTERNS = {
    'clover': ('..22.22..', '.232.232.', '..22222..', '...222...', '.2222222.', '.232.232.', '.....1...', '......1..'),
    'daisy': ('...33...', '.332233.', '..2442..', '.332233.', '...33...', '....1.2.', '..2212..', '....1...'),
    'cactus': ('....33...', '...2321..', '.2.2321..', '.212321.2', '.22232122', '...2321..', '...2321..', '..111111.'),
    'fossil': ('...4444..', '.4433334.', '.4311144.', '.4314434.', '..434434.', '...4334..', '....44...'),
    'ice_spire': ('.....3...', '....331..', '....321..', '..3.321..', '.3233213.', '.32332132', '..2232132', '...11111.'),
    'snowflake': ('.3..3..3.', '..3.3.3..', '...434...', '.3344433.', '...434...', '..3.3.3..', '.3..3..3.'),
    'lilypad': ('..222222.', '.23322221', '232222211', '22222....', '.2222244.', '..112343.', '.....44..'),
    'cattail': ('..44.....', '..41..44.', '..41..41.', '...2..41.', '.3.2..2..', '..322.2.3', '...22223.', '....111..'),
    'maple': ('....3....', '.2.333.2.', '.2334322.', '332343233', '.2224222.', '...242...', '.....1...'),
    'stump': ('..44444..', '.4343341.', '.4434441.', '.2122121.', '.2122121.', '121221211', '11.....11'),
    'vent': ('....2....', '...3.....', '....2....', '...1441..', '..122421.', '.13222221', '111111111'),
    'slag': ('...111...', '..23221..', '.2324221.', '122244221', '122422211', '.1111111.'),
    'geode': ('...222...', '.2311132.', '231443132', '214334412', '.2133412.', '..22222..'),
    'stalagmite': ('...3.....', '...32....', '..232..2.', '..232.321', '.22321321', '122221221', '111111111'),
    'shell': ('..33333..', '.3232323.', '323232323', '.3222223.', '..32223..', '...444...'),
    'starfish': ('....4....', '....43...', '4..443..4', '.4443344.', '...434...', '..44.44..', '.44...44.'),
    'gear': ('...22...', '.223322.', '..2112..', '232..232', '232..232', '..2112..', '.222322.', '...22...'),
    'grate': ('444444444', '422222224', '231131131', '231131131', '231131131', '222222222', '111111111'),
    'runestone': ('...3322..', '..322221.', '..244221.', '..242421.', '..224221.', '..242221.', '.1222211.', '.1111111.'),
    'column': ('.3333333.', '.2222121.', '..32321..', '..32321..', '..32321..', '.2222221.', '133333221', '111111111'),
}


@lru_cache(maxsize=256)
def prop_sprite(kind, palette, scale, mirrored):
    rows = PATTERNS[kind]
    size = max(map(len, rows)), len(rows)
    sprite = pygame.Surface(size, pygame.SRCALPHA)
    colors = [pygame.Color('#' + hex_color) for hex_color in palette]
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell != '.':
                sprite.set_at((x, y), colors[int(cell)-1])
    if mirrored:
        sprite = pygame.transform.flip(sprite, True, False)
    return pygame.transform.scale(sprite, (size[0]*scale, size[1]*scale))
