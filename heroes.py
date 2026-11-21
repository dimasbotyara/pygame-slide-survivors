# heroes.py — Hero selection definitions, ultimate abilities and unique upgrades

import pygame
from settings import *

HEROES = {
    "slider": {
        "id": "slider",
        "color": CYAN,
        "outline_color": WHITE,
        "base_hp": 100,
        "base_speed": 220,
        "slide_charges": 3,
        "slide_cooldown_mult": 0.85,
        "slide_speed_mult": 1.2,
        "fist_damage_mult": 1.0,
        "crit_chance": 5,
        "crit_mult": 150,
        "lifesteal": 0,
        "bonus_upgrades": [],
        "hero_upgrades": [
            "slider_hyper_slide", "slider_infinite_momentum", "slider_ghost_drive",
            "slider_corner_cut", "slider_impact_charge",
        ],
        "ult_id": "ult_chrono_slide",
        "ult_cast_time": 0.6,
    },
    "brawler": {
        "id": "brawler",
        "color": RED,
        "outline_color": DARK_RED,
        "base_hp": 125,
        "base_speed": 190,
        "slide_charges": 2,
        "slide_cooldown_mult": 1.0,
        "slide_speed_mult": 1.0,
        "fist_damage_mult": 1.3,
        "crit_chance": 5,
        "crit_mult": 150,
        "lifesteal": 0,
        "bonus_upgrades": [],
        "hero_upgrades": [
            "brawler_titan_fists", "brawler_blood_rage", "brawler_ironhide",
            "brawler_long_combo", "brawler_crescent_swing",
        ],
        "ult_id": "ult_earthquake_slam",
        "ult_cast_time": 1.5,
    },
    "spark": {
        "id": "spark",
        "color": YELLOW,
        "outline_color": GOLD,
        "base_hp": 90,
        "base_speed": 230,
        "slide_charges": 2,
        "slide_cooldown_mult": 0.9,
        "slide_speed_mult": 1.1,
        "fist_damage_mult": 1.0,
        "crit_chance": 5,
        "crit_mult": 150,
        "lifesteal": 0,
        "bonus_upgrades": ["slide_electric"],
        "hero_upgrades": [
            "spark_overcharge", "spark_thunder_strike", "spark_chain_reactor",
            "spark_stun_field", "spark_wave_conductor",
        ],
        "ult_id": "ult_chain_lightning",
        "ult_cast_time": 0.9,
    },
    "shadow": {
        "id": "shadow",
        "color": PURPLE,
        "outline_color": DARK_PURPLE,
        "base_hp": 85,
        "base_speed": 210,
        "slide_charges": 2,
        "slide_cooldown_mult": 1.0,
        "slide_speed_mult": 1.0,
        "fist_damage_mult": 1.1,
        "crit_chance": 20,
        "crit_mult": 200,
        "lifesteal": 4,
        "bonus_upgrades": [],
        "hero_upgrades": [
            "shadow_blade_mastery", "shadow_soul_drain", "shadow_critical_edge",
            "shadow_night_blood", "shadow_quickstep",
        ],
        "ult_id": "ult_shadow_dance",
        "ult_cast_time": 1.2,
    },
}

HERO_KEYS = ["slider", "brawler", "spark", "shadow"]


def get_hero_data(hero_id):
    return HEROES.get(hero_id, HEROES["slider"])
