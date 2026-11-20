"""Temporary pickup bonuses in the same units as permanent upgrade stats."""
from dataclasses import dataclass
from functools import lru_cache
from typography import face


@dataclass(frozen=True)
class Tonic:
    stat: str
    bonus: int
    seconds: int
    icon: str
    color: tuple


TONICS = {
    'iron_acorn': Tonic('armor', 6, 10, '🛡', (173, 200, 178)),
    'ember_pepper': Tonic('damage', 60, 8, '🌶', (255, 141, 92)),
    'spark_honey': Tonic('attack_speed', 60, 8, '🍯', (250, 203, 91)),
    'hawk_eye': Tonic('crit_chance', 30, 10, '👁', (215, 164, 255)),
    'vine_wrap': Tonic('attack_range', 50, 10, '🌿', (133, 218, 132)),
    'ruby_fang': Tonic('fist_lifesteal', 12, 8, '🦷', (255, 134, 161)),
    'sage_scroll': Tonic('xp_multiplier', 50, 12, '📜', (229, 211, 139)),
    'pole_star': Tonic('xp_radius', 150, 12, '🌟', (137, 213, 247)),
    'gyro_fin': Tonic('slide_turn_speed', 100, 12, '🧭', (113, 229, 195)),
    'comet_wax': Tonic('slide_speed', 40, 10, '☄', (135, 178, 255)),
    'thunder_seed': Tonic('fist_stun_chance', 35, 8, '⚡', (248, 231, 94)),
    'ram_horn': Tonic('slide_damage', 80, 12, '🐏', (220, 177, 140)),
}
TONIC_IDS = tuple(TONICS)
TONIC_BY_STAT = {tonic.stat: key for key, tonic in TONICS.items()}


@lru_cache(maxsize=32)
def tonic_icon(key):
    tonic = TONICS[key]
    return face('emoji', 16).render(tonic.icon, True, tonic.color)
