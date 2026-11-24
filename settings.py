# settings.py — v4 — ПОЛНАЯ ВЕРСИЯ

import pygame
import os

# ============================================================
# ОКНО
# ============================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Slide Survivors"

# ============================================================
# ПУТИ
# ============================================================
SAVE_DIR = os.path.join(os.path.expanduser("~"), ".slide_survivors")
HIGHSCORES_FILE = os.path.join(SAVE_DIR, "highscores.json")

# ============================================================
# ЦВЕТА
# ============================================================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
DARK_RED = (150, 30, 30)
GREEN = (50, 200, 50)
DARK_GREEN = (30, 130, 30)
BLUE = (50, 100, 220)
DARK_BLUE = (30, 60, 150)
YELLOW = (240, 220, 50)
ORANGE = (240, 150, 30)
PURPLE = (150, 50, 200)
DARK_PURPLE = (90, 30, 130)
CYAN = (50, 200, 220)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
BROWN = (139, 90, 43)
PINK = (255, 105, 180)
LIME = (150, 255, 50)
TEAL = (0, 180, 180)
GOLD = (255, 215, 0)
SILVER = (200, 200, 210)
CRIMSON = (180, 20, 20)

# ============================================================
# ИГРОК
# ============================================================
PLAYER_BASE_HP = 100
PLAYER_BASE_SPEED = 200
PLAYER_BASE_SIZE = 20
PLAYER_COLOR = CYAN
PLAYER_INVINCIBILITY_AFTER_HIT = 0.5
# Пассивная регенерация здоровья для всех героев
PLAYER_BASE_HP_REGEN = 1.0

# ============================================================
# ВРОЖДЁННЫЕ ПАССИВКИ ГЕРОЕВ
# ============================================================
# Слайдер: каждое убийство скольжением восстанавливает здоровье
SLIDER_PASSIVE_SLIDE_KILL_HEAL = 3
# Браулер: урон растёт с прогрессом текущего уровня (до +25%)
BRAWLER_PASSIVE_LEVEL_RAGE = 25.0
# Спарк: шанс примагнить опыт и предмет с каждого убийства
SPARK_PASSIVE_MAGNET_CHANCE = 10.0
# Шэдоу: временные улучшения длятся дольше
SHADOW_PASSIVE_TEMP_BONUS = 3.0

# ============================================================
# СКОЛЬЖЕНИЕ
# ============================================================
SLIDE_INITIAL_SPEED_MULTIPLIER = 5.0
SLIDE_DURATION = 1.2
SLIDE_COOLDOWN = 5.0
SLIDE_DECELERATION_CURVE = 3.0
SLIDE_TURN_SPEED = 90
SLIDE_KNOCKBACK_RADIUS = 30
SLIDE_BASE_KNOCKBACK_DAMAGE = 10
SLIDE_KNOCKBACK_FORCE = 400
SLIDE_SPEED_DAMAGE_MULTIPLIER = 0.17
# Один и тот же враг получает урон от скольжения не чаще, чем раз в этот интервал
SLIDE_HIT_COOLDOWN = 0.45
# Для всех героев кроме Слайдера скольжение — в основном мобильность
SLIDE_DAMAGE_NON_SLIDER_MULT = 0.55
SLIDE_TRAIL_DURATION = 2.0
# Скорость рикошета ульта Слайдера (герой и клоны)
SLIDER_ULT_SPEED = 1750

# ============================================================
# УВОРОТ, ЛЁД И АУРЫ
# ============================================================
PERFECT_DODGE_WINDOW = 0.16
ICE_RADIUS = 24
ICE_DURATION = 2.0
REPULSE_RADIUS = 95
REPULSE_PERIOD = 2.5
DRAIN_RADIUS = 115
DRAIN_PERIOD = 2.0
STASIS_RADIUS = 145

# ============================================================
# КОМБО
# ============================================================
COMBO_TIMEOUT = 3.0
BOMB_COMBO_EXTENSION = 5.0
EXPLOSION_FUSE = 0.325
COMBO_XP_BONUS_PER_STACK = 5
COMBO_MAX_MULTIPLIER = 500

# ============================================================
# КУЛАКИ — БУФФНУТЫЕ
# ============================================================
FIST_BASE_DAMAGE = 18
FIST_BASE_ATTACK_SPEED = 1.5
# Прорубающий удар бьёт всех вокруг, но с пониженным уроном
CLEAVE_DAMAGE_MULTIPLIER = 0.6
FIST_BASE_RANGE = 65
FIST_KNOCKBACK = 150
FIST_ARC = 140

FIST_COMBO_WINDOW = 1.0
FIST_COMBO_HITS = 3
FIST_COMBO_DAMAGE_MULTIPLIERS = [1.0, 1.3, 3.0]
FIST_COMBO_KNOCKBACK_MULTIPLIERS = [1.0, 1.2, 3.0]
FIST_COMBO_ARC = [140, 160, 360]
FIST_COMBO_RANGE_MULTIPLIERS = [1.0, 1.1, 1.5]

FIST_MEGA_HIT_EVERY = 5
FIST_MEGA_DAMAGE_MULTIPLIER = 4.0
FIST_MEGA_RANGE_MULTIPLIER = 2.0
FIST_MEGA_KNOCKBACK_MULTIPLIER = 4.0

FIST_STUN_DURATION = 2.0
FIST_BASE_STUN_CHANCE = 0
FIST_BASE_LIFESTEAL = 0

FIST_RAGE_MAX_BONUS = 200
FIST_RAGE_THRESHOLD = 0.7
FIST_RAGE_ATTACK_SPEED_BONUS = 100

GROUND_SLAM_RADIUS = 150
GROUND_SLAM_DAMAGE_MULTIPLIER = 2.0
GROUND_SLAM_PULL_FORCE = 200

COUNTER_ATTACK_DAMAGE_MULTIPLIER = 3.0
COUNTER_ATTACK_RANGE_MULTIPLIER = 1.5
COUNTER_ATTACK_INVINCIBILITY = 0.3

FIST_WAVE_SPEED = 500
FIST_WAVE_RANGE = 200
FIST_WAVE_WIDTH = 40
FIST_WAVE_DAMAGE_RATIO = 0.5

FIST_XP_PULL_RADIUS = 100

# ============================================================
# ЭЛЕКТРИЧЕСКИЙ СЛЕД
# ============================================================
ELECTRIC_TRAIL_DAMAGE = 5
ELECTRIC_TRAIL_RADIUS = 30
ELECTRIC_TRAIL_DURATION = 1.5

# ============================================================
# УДАРНАЯ ВОЛНА СКОЛЬЖЕНИЯ
# ============================================================
SHOCKWAVE_DAMAGE_MULTIPLIER = 0.5
SHOCKWAVE_RADIUS = 150
SHOCKWAVE_SPEED = 400

# ============================================================
# ВРАГИ
# ============================================================
ENEMY_SPAWN_RADIUS_MIN = 500
ENEMY_SPAWN_RADIUS_MAX = 800
ENEMY_DESPAWN_RADIUS = 1200
ENEMY_SPAWN_RATE_BASE = 1.0
ENEMY_SPAWN_RATE_MAX = 8.0
ENEMY_DIFFICULTY_SCALE_TIME = 600
ENEMY_MAX_COUNT = 300
RESIDENT_SPAWN_CHANCE = 0.25 / 3

ENEMY_TYPES = {
    "zombie": {
        "hp": 30, "speed": 60, "damage": 8, "size": 14,
        "color": GREEN, "outline_color": DARK_GREEN,
        "xp": 10, "weight": 50, "min_time": 0, "knockback_resist": 0.0,
    },
    "skirmisher": {
        "hp": 24, "speed": 112, "damage": 9, "size": 12,
        "color": TEAL, "outline_color": CYAN,
        "xp": 14, "weight": 18, "min_time": 20, "knockback_resist": 0.0,
    },
    "crusher": {
        "hp": 95, "speed": 46, "damage": 19, "size": 19,
        "color": BROWN, "outline_color": GOLD,
        "xp": 28, "weight": 12, "min_time": 75, "knockback_resist": 0.5,
        "strike_radius": 74, "windup": 0.425,
    },
    "prism": {
        "hp": 38, "speed": 48, "damage": 10, "size": 15,
        "color": PURPLE, "outline_color": PINK,
        "xp": 32, "weight": 9, "min_time": 135, "knockback_resist": 0.1,
        "shoot_range": 270, "shoot_speed": 205, "shoot_cooldown": 2.8,
        "shot_offsets": (-0.28, 0, 0.28), "windup": 0.4,
    },
    "ghoul": {
        "hp": 15, "speed": 140, "damage": 5, "size": 10,
        "color": BLUE, "outline_color": DARK_BLUE,
        "xp": 15, "weight": 30, "min_time": 30, "knockback_resist": 0.0,
    },
    "fatty": {
        "hp": 100, "speed": 35, "damage": 15, "size": 22,
        "color": BROWN, "outline_color": DARK_GRAY,
        "xp": 25, "weight": 15, "min_time": 60, "knockback_resist": 0.5,
    },
    "berserker": {
        "hp": 40, "speed": 100, "damage": 20, "size": 15,
        "color": RED, "outline_color": DARK_RED,
        "xp": 20, "weight": 20, "min_time": 90, "knockback_resist": 0.2,
    },
    "ghost": {
        "hp": 20, "speed": 80, "damage": 10, "size": 12,
        "color": LIGHT_GRAY, "outline_color": WHITE,
        "xp": 20, "weight": 15, "min_time": 120, "knockback_resist": 0.0,
    },
    "shooter": {
        "hp": 25, "speed": 50, "damage": 12, "size": 13,
        "color": ORANGE, "outline_color": DARK_RED,
        "xp": 25, "weight": 10, "min_time": 150, "knockback_resist": 0.1,
        "shoot_range": 300, "shoot_speed": 250, "shoot_cooldown": 2.0,
    },
    "tank": {
        "hp": 250, "speed": 25, "damage": 25, "size": 28,
        "color": DARK_GRAY, "outline_color": BLACK,
        "xp": 50, "weight": 5, "min_time": 180, "knockback_resist": 0.8,
    },
    "necromancer": {
        "hp": 60, "speed": 40, "damage": 8, "size": 14,
        "color": DARK_PURPLE, "outline_color": PURPLE,
        "xp": 35, "weight": 8, "min_time": 200, "knockback_resist": 0.3,
        "revive_radius": 150, "revive_cooldown": 5.0,
    },
    "sprinter": {
        "hp": 25, "speed": 70, "damage": 15, "size": 12,
        "color": LIME, "outline_color": GREEN,
        "xp": 30, "weight": 10, "min_time": 160, "knockback_resist": 0.1,
        "sprint_speed": 400, "sprint_cooldown": 4.0, "sprint_duration": 0.4,
    },
    "exploder": {
        "hp": 35, "speed": 80, "damage": 10, "size": 13,
        "color": ORANGE, "outline_color": RED,
        "xp": 20, "weight": 12, "min_time": 130, "knockback_resist": 0.0,
        "explode_damage": 30, "explode_radius": 80,
    },
    "shielder": {
        "hp": 80, "speed": 50, "damage": 12, "size": 16,
        "color": SILVER, "outline_color": GRAY,
        "xp": 30, "weight": 8, "min_time": 210, "knockback_resist": 0.6,
        "shield_arc": 90,
    },
}

# ============================================================
# БОСС
# ============================================================
BOSS_SPAWN_INTERVAL = 300
BOSS_HP = 1000
BOSS_SPEED = 40
BOSS_DAMAGE = 30
BOSS_SIZE = 45
BOSS_COLOR = PURPLE
BOSS_OUTLINE_COLOR = BLACK
BOSS_XP = 500
BOSS_KNOCKBACK_RESIST = 0.9
BOSS_ARENA_RADIUS = 1200
BOSS_ARENA_WALL_THICKNESS = 8

# ============================================================
# ОПЫТ
# ============================================================
XP_BASE_TO_LEVEL = 50
XP_GROWTH = 1.25
XP_PICKUP_RADIUS_BASE = 60
XP_ORB_SIZE = 5
XP_ORB_COLOR = YELLOW
XP_ORB_SPEED = 350
# Чем дольше сфера летит к игроку, тем сильнее она разгоняется
XP_ORB_ACCELERATION = 420
XP_ORB_MAX_SPEED = 1500
CHOICES_PER_LEVEL = 3

# ============================================================
# ПРЕДМЕТЫ
# ============================================================
DROP_CHANCE_HEAL = 0.05
DROP_CHANCE_MAGNET = 0.02
DROP_CHANCE_BOMB = 0.01
DROP_CHANCE_TONIC = 0.043  # temporary tonic upgrades are about three times rarer
DROP_CHANCE_SPEED_BOOST = 0.03
HEAL_AMOUNT = 30
SPEED_BOOST_DURATION = 5.0
SPEED_BOOST_MULTIPLIER = 1.5
ITEM_LIFETIME = 10.0
ITEM_SIZE = 8

# ============================================================
# СНАРЯДЫ
# ============================================================
ENEMY_PROJECTILE_SIZE = 5
ENEMY_PROJECTILE_COLOR = ORANGE
ENEMY_PROJECTILE_LIFETIME = 5.0

# ============================================================
# ЧАСТИЦЫ
# ============================================================
PARTICLE_LIFETIME = 0.5
DAMAGE_NUMBER_LIFETIME = 0.8
DAMAGE_NUMBER_RISE_SPEED = 50

# ============================================================
# МИНИ-КАРТА
# ============================================================
MINIMAP_SIZE = 150
MINIMAP_MARGIN = 10
MINIMAP_SCALE = 0.05
MINIMAP_BG_ALPHA = 140
MINIMAP_PLAYER_COLOR = CYAN
MINIMAP_ENEMY_COLOR = RED
MINIMAP_BOSS_COLOR = PURPLE
MINIMAP_ITEM_COLOR = GREEN
MINIMAP_XP_COLOR = YELLOW

# ============================================================
# SCREEN SHAKE
# ============================================================
SHAKE_BOSS_HIT = 3
SHAKE_PLAYER_HIT = 5
SHAKE_BOSS_SPAWN = 10
SHAKE_BOSS_DEATH = 15
SHAKE_BOMB = 12
SHAKE_GROUND_SLAM = 10
SHAKE_UPPERCUT = 6
SHAKE_MEGA_HIT = 8

# ============================================================
# UI
# ============================================================
UI_FONT_SIZE = 24
UI_FONT_SIZE_LARGE = 48
UI_FONT_SIZE_SMALL = 16
UI_HP_BAR_WIDTH = 200
UI_HP_BAR_HEIGHT = 20
UI_XP_BAR_HEIGHT = 8
UI_MARGIN = 10
UI_UPGRADE_BOX_WIDTH = 380
UI_UPGRADE_BOX_HEIGHT = 330

# ============================================================
# КАРТА
# ============================================================
TILE_SIZE = 64

# ============================================================
# РЕКОРДЫ
# ============================================================
MAX_HIGHSCORES = 10
MESSAGE_DURATION = 3.0
LEVEL_UP_RING_SPEED = 300
LEVEL_UP_RING_MAX_RADIUS = 200
LEVEL_UP_RING_LIFETIME = 0.8