# items.py — Опыт и предметы на земле

import pygame
import math
import random
from settings import *


class XPOrb:
    """Сфера опыта"""
    def __init__(self, x, y, xp_amount):
        self.x = float(x)
        self.y = float(y)
        self.xp = xp_amount
        self.size = XP_ORB_SIZE
        self.alive = True
        self.being_collected = False
        self.speed = 0.0
        self.anim_timer = random.random() * 10

        # Небольшой разброс при появлении
        self.x += random.uniform(-15, 15)
        self.y += random.uniform(-15, 15)

        # Определить размер и цвет по кол-ву опыта
        if xp_amount >= 50:
            self.size = 8
            self.color = ORANGE
            self.glow_color = YELLOW
        elif xp_amount >= 25:
            self.size = 6
            self.color = YELLOW
            self.glow_color = WHITE
        else:
            self.size = XP_ORB_SIZE
            self.color = XP_ORB_COLOR
            self.glow_color = (255, 255, 150)

    def update(self, dt, player_x, player_y, pickup_radius):
        if not self.alive:
            return False

        self.anim_timer += dt

        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        # Проверка радиуса сбора
        if dist < pickup_radius:
            self.being_collected = True

        if self.being_collected:
            # Лететь к игроку
            self.speed = XP_ORB_SPEED
            if dist > 0:
                self.x += (dx / dist) * self.speed * dt
                self.y += (dy / dist) * self.speed * dt

            # Подобрано
            if dist < 15:
                self.alive = False
                return True  # собрано

        return False

    def draw(self, screen, camera):
        if not self.alive:
            return

        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if sx < -20 or sx > SCREEN_WIDTH + 20 or sy < -20 or sy > SCREEN_HEIGHT + 20:
            return

        # Пульсация
        pulse = 1.0 + math.sin(self.anim_timer * 5) * 0.2
        draw_size = max(2, int(self.size * pulse))

        # Свечение
        glow_size = draw_size + 2
        pygame.draw.circle(screen, self.glow_color, (sx, sy), glow_size)
        pygame.draw.circle(screen, self.color, (sx, sy), draw_size)


class DroppedItem:
    """Предмет на земле (хилка, магнит, бомба, ускорение)"""
    def __init__(self, x, y, item_type):
        self.x = float(x)
        self.y = float(y)
        self.item_type = item_type
        self.alive = True
        self.lifetime = ITEM_LIFETIME
        self.size = ITEM_SIZE
        self.anim_timer = 0.0

        # Цвета и описание
        if item_type == "heal":
            self.color = GREEN
            self.secondary_color = WHITE
        elif item_type == "magnet":
            self.color = PURPLE
            self.secondary_color = CYAN
        elif item_type == "bomb":
            self.color = RED
            self.secondary_color = ORANGE
        elif item_type == "speed_boost":
            self.color = CYAN
            self.secondary_color = WHITE

    def update(self, dt, player_x, player_y):
        if not self.alive:
            return None

        self.anim_timer += dt
        self.lifetime -= dt

        if self.lifetime <= 0:
            self.alive = False
            return None

        # Проверка подбора
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 25:
            self.alive = False
            return self.item_type

        return None

    def draw(self, screen, camera):
        if not self.alive:
            return

        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if sx < -20 or sx > SCREEN_WIDTH + 20 or sy < -20 or sy > SCREEN_HEIGHT + 20:
            return

        # Мигание перед исчезновением
        if self.lifetime < 3.0:
            if int(self.anim_timer * 5) % 2 == 0:
                return

        # Подпрыгивание
        bob = math.sin(self.anim_timer * 3) * 3

        # Рисуем предмет в зависимости от типа
        if self.item_type == "heal":
            # Крестик
            pygame.draw.rect(screen, self.color,
                           (sx - 3, int(sy - 8 + bob), 6, 16))
            pygame.draw.rect(screen, self.color,
                           (sx - 8, int(sy - 3 + bob), 16, 6))
            pygame.draw.rect(screen, self.secondary_color,
                           (sx - 3, int(sy - 8 + bob), 6, 16), 1)
            pygame.draw.rect(screen, self.secondary_color,
                           (sx - 8, int(sy - 3 + bob), 16, 6), 1)

        elif self.item_type == "magnet":
            # U-образный магнит
            pygame.draw.arc(screen, self.color,
                          (sx - 8, int(sy - 8 + bob), 16, 16),
                          0, math.pi, 3)
            pygame.draw.line(screen, RED,
                           (sx - 8, int(sy + bob)), (sx - 8, int(sy + 6 + bob)), 3)
            pygame.draw.line(screen, BLUE,
                           (sx + 8, int(sy + bob)), (sx + 8, int(sy + 6 + bob)), 3)

        elif self.item_type == "bomb":
            # Бомба (круг + фитиль)
            pygame.draw.circle(screen, self.color, (sx, int(sy + bob)), 8)
            pygame.draw.circle(screen, self.secondary_color, (sx, int(sy + bob)), 8, 2)
            spark = int(self.anim_timer * 8) % 2
            spark_color = YELLOW if spark else ORANGE
            pygame.draw.line(screen, DARK_GRAY,
                           (sx + 3, int(sy - 7 + bob)), (sx + 6, int(sy - 12 + bob)), 2)
            pygame.draw.circle(screen, spark_color, (sx + 6, int(sy - 12 + bob)), 3)

        elif self.item_type == "speed_boost":
            # Молния
            points = [
                (sx - 4, int(sy - 10 + bob)),
                (sx + 2, int(sy - 2 + bob)),
                (sx - 1, int(sy - 2 + bob)),
                (sx + 4, int(sy + 10 + bob)),
                (sx - 2, int(sy + 2 + bob)),
                (sx + 1, int(sy + 2 + bob)),
            ]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, self.secondary_color, points, 1)


def roll_drop(player_luck_bonus=0):
    """Определить, что выпадет при убийстве врага"""
    luck_mult = 1.0 + player_luck_bonus / 100

    roll = random.random()
    cumulative = 0

    drops = [
        ("heal", DROP_CHANCE_HEAL * luck_mult),
        ("speed_boost", DROP_CHANCE_SPEED_BOOST * luck_mult),
        ("magnet", DROP_CHANCE_MAGNET * luck_mult),
        ("bomb", DROP_CHANCE_BOMB * luck_mult),
    ]

    for item_type, chance in drops:
        cumulative += chance
        if roll < cumulative:
            return item_type

    return None