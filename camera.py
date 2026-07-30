# camera.py — Камера с screen shake

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

        # Screen shake
        self.shake_intensity = 0.0
        self.shake_timer = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0

    def update(self, target_x, target_y, dt=0):
        """Центрировать камеру на цели"""
        self.offset_x = target_x - self.screen_width // 2
        self.offset_y = target_y - self.screen_height // 2

        # Обновить shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
            progress = self.shake_timer / 0.3 if self.shake_timer > 0 else 0
            current_intensity = self.shake_intensity * progress
            self.shake_offset_x = random.uniform(-current_intensity, current_intensity)
            self.shake_offset_y = random.uniform(-current_intensity, current_intensity)
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0

        self.offset_x -= self.shake_offset_x
        self.offset_y -= self.shake_offset_y

    def add_shake(self, intensity):
        """Добавить тряску камеры"""
        if not self.shake_enabled:
            return
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_timer = 0.3

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