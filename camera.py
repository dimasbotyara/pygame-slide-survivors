# camera.py — Камера с плавным следованием, look-ahead и screen shake/flash

import pygame
import random
import math


class Camera:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.shake_enabled = True

        # Плавное следование
        self.smooth_x = 0.0
        self.smooth_y = 0.0
        self.initialized = False
        self.lerp_speed = 8.0  # Скорость интерполяции

        # Look-ahead (камера забегает вперёд по направлению движения)
        self.look_ahead_x = 0.0
        self.look_ahead_y = 0.0
        self.look_ahead_distance = 60.0
        self.look_ahead_lerp = 3.0

        # Screen shake (переменная длительность)
        self.shake_intensity = 0.0
        self.shake_timer = 0.0
        self.shake_duration = 0.3
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0

        # Screen flash (вспышка экрана)
        self.flash_color = (255, 255, 255)
        self.flash_timer = 0.0
        self.flash_duration = 0.0
        self.flash_alpha = 0

    def update(self, target_x, target_y, dt=0, target_vx=0, target_vy=0):
        """Плавное следование за целью с look-ahead"""
        # Look-ahead — целевое смещение в направлении движения
        speed = math.sqrt(target_vx * target_vx + target_vy * target_vy)
        if speed > 10:
            norm_vx = target_vx / speed
            norm_vy = target_vy / speed
            target_lax = norm_vx * self.look_ahead_distance
            target_lay = norm_vy * self.look_ahead_distance
        else:
            target_lax = 0.0
            target_lay = 0.0

        # Плавная интерполяция look-ahead
        la_lerp = min(1.0, self.look_ahead_lerp * dt) if dt > 0 else 1.0
        self.look_ahead_x += (target_lax - self.look_ahead_x) * la_lerp
        self.look_ahead_y += (target_lay - self.look_ahead_y) * la_lerp

        # Целевая позиция камеры (центр экрана на игроке + look-ahead)
        goal_x = target_x + self.look_ahead_x - self.screen_width // 2
        goal_y = target_y + self.look_ahead_y - self.screen_height // 2

        # Первый кадр — мгновенная телепортация
        if not self.initialized:
            self.smooth_x = goal_x
            self.smooth_y = goal_y
            self.initialized = True
        else:
            # Плавная интерполяция (lerp)
            lerp_factor = min(1.0, self.lerp_speed * dt) if dt > 0 else 1.0
            self.smooth_x += (goal_x - self.smooth_x) * lerp_factor
            self.smooth_y += (goal_y - self.smooth_y) * lerp_factor

        self.offset_x = self.smooth_x
        self.offset_y = self.smooth_y

        # Обновить shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
            progress = max(0, self.shake_timer / self.shake_duration) if self.shake_duration > 0 else 0
            current_intensity = self.shake_intensity * progress
            self.shake_offset_x = random.uniform(-current_intensity, current_intensity)
            self.shake_offset_y = random.uniform(-current_intensity, current_intensity)
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0

        self.offset_x -= self.shake_offset_x
        self.offset_y -= self.shake_offset_y

        # Обновить flash
        if self.flash_timer > 0:
            self.flash_timer -= dt
            progress = max(0, self.flash_timer / self.flash_duration) if self.flash_duration > 0 else 0
            self.flash_alpha = int(180 * progress)
        else:
            self.flash_alpha = 0

    def add_shake(self, intensity, duration=0.3):
        """Добавить тряску камеры с настраиваемой длительностью"""
        if not self.shake_enabled:
            return
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_timer = duration
        self.shake_duration = duration

    def start_flash(self, color=(255, 255, 255), duration=0.15):
        """Запустить вспышку экрана (для крит/мега-удар/смерть босса)"""
        self.flash_color = color
        self.flash_timer = duration
        self.flash_duration = duration

    def draw_flash(self, screen):
        """Отрисовать вспышку экрана (вызывать после всего HUD)"""
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            flash_surface.fill((*self.flash_color, self.flash_alpha))
            screen.blit(flash_surface, (0, 0))

    def apply(self, world_x, world_y):
        """Мировые → экранные координаты"""
        screen_x = world_x - self.offset_x
        screen_y = world_y - self.offset_y
        return screen_x, screen_y

    def apply_rect(self, rect):
        return pygame.Rect(
            rect.x - self.offset_x,
            rect.y - self.offset_y,
            rect.width,
            rect.height
        )

    def reverse(self, screen_x, screen_y):
        """Экранные → мировые координаты"""
        world_x = screen_x + self.offset_x
        world_y = screen_y + self.offset_y
        return world_x, world_y

    def is_visible(self, world_x, world_y, margin=100):
        sx, sy = self.apply(world_x, world_y)
        return (
            -margin <= sx <= self.screen_width + margin and
            -margin <= sy <= self.screen_height + margin
        )