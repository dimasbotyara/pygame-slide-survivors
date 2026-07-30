# particles.py — Частицы, числа урона, эффекты

import pygame
import random
import math
from settings import *


class Particle:
    """Одна частица"""

    def __init__(self, x, y, vx, vy, color, lifetime=0.5, size=4):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Замедление
        self.vx *= (1.0 - 2.0 * dt)
        self.vy *= (1.0 - 2.0 * dt)

        self.lifetime -= dt

    def draw(self, screen, camera):
        if self.lifetime <= 0:
            return

        sx, sy = camera.apply(self.x, self.y)

        # Прозрачность через размер
        progress = self.lifetime / self.max_lifetime
        current_size = max(1, int(self.size * progress))

        rect = pygame.Rect(
            int(sx - current_size // 2),
            int(sy - current_size // 2),
            current_size, current_size
        )
        pygame.draw.rect(screen, self.color, rect)


class DamageNumber:
    """Всплывающее число урона"""

    def __init__(self, x, y, damage, is_crit=False, color=None):
        self.x = float(x) + random.uniform(-10, 10)
        self.y = float(y) - 10
        self.damage = int(damage)
        self.is_crit = is_crit
        self.lifetime = DAMAGE_NUMBER_LIFETIME
        self.max_lifetime = DAMAGE_NUMBER_LIFETIME
        self.vy = -DAMAGE_NUMBER_RISE_SPEED
        self.color = color or (RED if is_crit else WHITE)

    def update(self, dt):
        self.y += self.vy * dt
        self.vy *= 0.95  # замедление подъёма
        self.lifetime -= dt

    def draw(self, screen, camera, font_small, font_normal):
        if self.lifetime <= 0:
            return

        sx, sy = camera.apply(self.x, self.y)

        text = f"{self.damage}"
        if self.is_crit:
            text += "!"
            font = font_normal
        else:
            font = font_small

        # Тень
        shadow_surface = font.render(text, True, BLACK)
        screen.blit(shadow_surface, (int(sx) + 1, int(sy) + 1))

        # Текст
        text_surface = font.render(text, True, self.color)
        if self.lifetime < 0.3:
            # Затухание через смешивание с фоном
            alpha = int(255 * (self.lifetime / 0.3))
            text_surface.set_alpha(alpha)
            shadow_surface.set_alpha(alpha)

        screen.blit(text_surface, (int(sx), int(sy)))


class GameMessage:
    """Игровое сообщение на экране (например, 'Враги усилились!')"""

    def __init__(self, text, color=YELLOW):
        self.text = text
        self.color = color
        self.lifetime = MESSAGE_DURATION
        self.max_lifetime = MESSAGE_DURATION

    def update(self, dt):
        self.lifetime -= dt

    def draw(self, screen, font, y_offset=0):
        if self.lifetime <= 0:
            return

        progress = self.lifetime / self.max_lifetime
        alpha = int(255 * min(1.0, progress * 2))  # Затухание в конце

        text_surface = font.render(self.text, True, self.color)
        text_rect = text_surface.get_rect(
            center=(SCREEN_WIDTH // 2, 120 + y_offset)
        )

        # Фоновая подложка
        bg_rect = text_rect.inflate(20, 10)
        bg_surface = pygame.Surface(
            (bg_rect.width, bg_rect.height), pygame.SRCALPHA
        )
        bg_surface.fill((0, 0, 0, min(180, alpha)))
        screen.blit(bg_surface, bg_rect)

        # Рамка
        pygame.draw.rect(screen, self.color, bg_rect, 1)

        # Текст
        screen.blit(text_surface, text_rect)


class ParticleManager:
    """Менеджер всех частиц и эффектов"""

    def __init__(self):
        self.particles = []
        self.damage_numbers = []
        self.messages = []
        self.damage_numbers_enabled = True

    def update(self, dt):
        # Частицы
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.lifetime > 0]

        # Числа урона
        for d in self.damage_numbers:
            d.update(dt)
        self.damage_numbers = [d for d in self.damage_numbers if d.lifetime > 0]

        # Сообщения
        for m in self.messages:
            m.update(dt)
        self.messages = [m for m in self.messages if m.lifetime > 0]

    def draw(self, screen, camera, font_small, font_normal):
        # Частицы
        for p in self.particles:
            p.draw(screen, camera)

        # Числа урона
        for d in self.damage_numbers:
            d.draw(screen, camera, font_small, font_normal)

        # Сообщения (поверх всего, экранные координаты)
        for i, m in enumerate(self.messages):
            m.draw(screen, font_normal, y_offset=i * 40)

    # ================================================================
    # УДОБНЫЕ МЕТОДЫ ДЛЯ СОЗДАНИЯ ЭФФЕКТОВ
    # ================================================================
    def spawn_hit_particles(self, x, y, color=WHITE, count=8):
        """Частицы при попадании"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.2, 0.5)
            size = random.randint(2, 5)
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_death_particles(self, x, y, color=RED, count=20):
        """Частицы при смерти врага"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.4, 0.8)
            size = random.randint(3, 7)
            # Варьируем цвет
            pcolor = (
                min(255, max(0, color[0] + random.randint(-30, 30))),
                min(255, max(0, color[1] + random.randint(-30, 30))),
                min(255, max(0, color[2] + random.randint(-30, 30)))
            )
            self.particles.append(Particle(x, y, vx, vy, pcolor, lifetime, size))

    def spawn_xp_particles(self, x, y, count=6):
        """Частицы при сборе опыта"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(30, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.3, 0.6)
            size = random.randint(2, 4)
            self.particles.append(Particle(x, y, vx, vy, YELLOW, lifetime, size))

    def spawn_slide_particles(self, x, y, dir_x, dir_y, count=2):
        """Частицы при скольжении (след)"""
        for _ in range(count):
            vx = -dir_x * random.uniform(50, 150) + random.uniform(-30, 30)
            vy = -dir_y * random.uniform(50, 150) + random.uniform(-30, 30)
            lifetime = random.uniform(0.3, 0.6)
            size = random.randint(3, 6)
            self.particles.append(Particle(x, y, vx, vy, CYAN, lifetime, size))

    def spawn_level_up_particles(self, x, y, count=30):
        """Частицы при повышении уровня"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 350)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.6, 1.2)
            size = random.randint(4, 8)
            color = random.choice([YELLOW, GOLD, WHITE, CYAN])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_heal_particles(self, x, y, count=12):
        """Частицы при лечении"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 120)
            vx = math.cos(angle) * speed
            vy = -abs(math.sin(angle) * speed) - 30  # вверх
            lifetime = random.uniform(0.5, 1.0)
            size = random.randint(3, 6)
            self.particles.append(Particle(x, y, vx, vy, GREEN, lifetime, size))

    def spawn_bomb_particles(self, x, y, count=40):
        """Частицы при взрыве бомбы"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 500)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.5, 1.2)
            size = random.randint(3, 7)
            color = random.choice([RED, ORANGE, YELLOW, WHITE])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def add_damage_number(self, x, y, damage, is_crit=False, color=None):
        """Добавить число урона"""
        if not self.damage_numbers_enabled:
            return
        self.damage_numbers.append(DamageNumber(x, y, damage, is_crit, color))

    def add_message(self, text, color=YELLOW):
        """Добавить сообщение на экран"""
        self.messages.append(GameMessage(text, color))

    # ================================================================
    # НОВЫЕ ЭФФЕКТЫ
    # ================================================================
    def spawn_crit_particles(self, x, y, count=15):
        """Золотая вспышка при критическом ударе"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(150, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.3, 0.6)
            size = random.randint(4, 8)
            color = random.choice([GOLD, YELLOW, WHITE, (255, 200, 100)])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_mega_hit_particles(self, x, y, count=35):
        """Эпический взрыв при мега-ударе"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(200, 600)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.5, 1.0)
            size = random.randint(5, 10)
            color = random.choice([RED, ORANGE, YELLOW, WHITE, GOLD])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_combo_milestone_particles(self, x, y, combo_count):
        """Праздничное кольцо частиц при комбо 50/100/200"""
        ring_count = min(60, 20 + combo_count // 5)
        for i in range(ring_count):
            angle = (i / ring_count) * math.pi * 2
            speed = random.uniform(200, 450)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.8, 1.5)
            size = random.randint(5, 9)
            color = random.choice([GOLD, YELLOW, CYAN, WHITE, ORANGE])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_orbital_blade_hit(self, x, y, count=6):
        """Искры при попадании орбитального клинка"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 180)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.15, 0.35)
            size = random.randint(2, 4)
            color = random.choice([CYAN, WHITE, (100, 220, 255)])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_poison_particles(self, x, y, count=5):
        """Ядовитые пузырьки (поднимаются вверх)"""
        for _ in range(count):
            vx = random.uniform(-30, 30)
            vy = random.uniform(-120, -40)
            lifetime = random.uniform(0.5, 1.0)
            size = random.randint(3, 6)
            color = random.choice([GREEN, (50, 200, 50), (80, 255, 80), LIME])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_shield_break_particles(self, x, y, count=12):
        """Осколки щита при поглощении урона"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.3, 0.7)
            size = random.randint(3, 6)
            color = random.choice([CYAN, (100, 180, 255), WHITE, (50, 150, 255)])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_executioner_particles(self, x, y, count=18):
        """Кровавый взрыв при казни"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(150, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.4, 0.8)
            size = random.randint(4, 8)
            color = random.choice([CRIMSON, RED, (180, 20, 20), (220, 50, 50)])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def spawn_electric_particles(self, x, y, count=8):
        """Электрические искры"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 350)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.1, 0.3)
            size = random.randint(2, 5)
            color = random.choice([YELLOW, WHITE, CYAN, (255, 255, 180)])
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))