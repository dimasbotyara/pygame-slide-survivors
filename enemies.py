# enemies.py — Враги с новыми типами, босс-арена, улучшенный визуал

import pygame
import math
import random
from settings import *
from translations import t
from typography import face
from wildlife import RESIDENTS, RESIDENT_BY_BIOME, resident_sprite



class Enemy:
    def __init__(self, x, y, enemy_type, difficulty_multiplier=1.0):
        self.x = float(x)
        self.y = float(y)
        self.enemy_type = enemy_type

        resident = RESIDENTS.get(enemy_type)
        self.home_biome = resident.biome if resident else None
        self.archetype = resident.archetype if resident else enemy_type
        data = ENEMY_TYPES[self.archetype]
        if resident:
            data = dict(data, **resident.traits, color=resident.color)

        self.max_hp = data["hp"] * difficulty_multiplier
        self.hp = self.max_hp
        self.base_speed = data["speed"]
        self.speed = data["speed"]
        self.damage = data["damage"] * difficulty_multiplier
        self.size = data["size"]
        self.color = data["color"]
        self.outline_color = data["outline_color"]
        self.xp_reward = data["xp"]
        self.knockback_resist = data["knockback_resist"]

        # Стрелок
        self.shoot_range = data.get("shoot_range", 0)
        self.shoot_speed = data.get("shoot_speed", 0)
        self.shoot_cooldown_max = data.get("shoot_cooldown", 0)
        self.shot_offsets = data.get("shot_offsets", (0,))
        self.strike_radius = data.get("strike_radius", self.size + 8)
        self.windup_dodged = False
        self.on_ice = False
        self.windup_duration = data.get("windup", 0.275 if self.shoot_range else 0.2)
        self.windup_left = 0.0
        self.aim_angle = 0.0

        # Некромант
        self.revive_radius = data.get("revive_radius", 0)
        self.revive_cooldown_max = data.get("revive_cooldown", 0)
        self.revive_timer = 0.0

        # Спринтер
        self.sprint_speed = data.get("sprint_speed", 0)
        self.sprint_cooldown_max = data.get("sprint_cooldown", 0)
        self.sprint_duration_max = data.get("sprint_duration", 0)
        self.sprint_timer = 0.0
        self.sprint_cooldown_timer = random.uniform(1, 3)  # случайная начальная задержка
        self.is_sprinting = False

        # Взрывник
        self.explode_damage = data.get("explode_damage", 0)
        self.explode_radius = data.get("explode_radius", 0)
        self.should_explode = False  # флаг для взрыва при смерти

        # Щитовик
        self.shield_arc = data.get("shield_arc", 0)
        self.shield_angle = 0.0  # направление щита (к игроку)

        # Движение
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0
        self.knockback_decay = 5.0

        # Состояние
        self.alive = True
        self.hit_cooldown = 0.0
        self.flash_timer = 0.0
        self.is_ghost = (self.archetype == "ghost")
        self.is_boss = False
        self.no_despawn = False  # не деспавнить

        # Визуал
        self.anim_timer = random.random() * 10

        # Для некроманта — хранить позиции смертей рядом
        self.nearby_corpse_positions = []

    def update(self, dt, player_x, player_y, enemies_list):
        if not self.alive:
            return

        self.anim_timer += dt

        if self.hit_cooldown > 0:
            self.hit_cooldown -= dt
        if self.flash_timer > 0:
            self.flash_timer -= dt
        if self.revive_timer > 0:
            self.revive_timer -= dt

        # Направление к игроку
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
        else:
            dir_x, dir_y = 0, 0

        # Обновить направление щита (для щитовика)
        if self.shield_arc > 0:
            self.shield_angle = math.atan2(dy, dx)

        # ──── Поведение по типу ────
        should_move = True
        current_speed = self.base_speed

        # Стрелок
        if self.shoot_range > 0 and dist < self.shoot_range:
            should_move = False
            if dist < self.shoot_range * 0.4:
                dir_x = -dir_x
                dir_y = -dir_y
                should_move = True

        # Спринтер
        if self.sprint_speed > 0:
            if self.is_sprinting:
                self.sprint_timer -= dt
                current_speed = self.sprint_speed
                if self.sprint_timer <= 0:
                    self.is_sprinting = False
                    self.sprint_cooldown_timer = self.sprint_cooldown_max
            else:
                self.sprint_cooldown_timer -= dt
                if self.sprint_cooldown_timer <= 0 and dist < 300:
                    self.is_sprinting = True
                    self.sprint_timer = self.sprint_duration_max

        # Некромант — держит дистанцию
        if self.revive_radius > 0:
            if dist < 120:
                dir_x = -dir_x
                dir_y = -dir_y
            elif dist < 200:
                should_move = False

        self.speed = current_speed

        if self.archetype == "skirmisher" and dist > self.strike_radius:
            # Weave across the approach rather than running straight at the hero.
            angle = math.sin(self.anim_timer * 3) * 0.95
            c, s = math.cos(angle), math.sin(angle)
            dir_x, dir_y = dir_x * c - dir_y * s, dir_x * s + dir_y * c

        if should_move and self.windup_left <= 0:
            if self.on_ice:
                # Carry the incoming heading across the ice, not the new target heading.
                speed = math.hypot(self.velocity_x, self.velocity_y)
                if speed > 0:
                    dir_x, dir_y = self.velocity_x / speed, self.velocity_y / speed
            self.velocity_x = dir_x * current_speed
            self.velocity_y = dir_y * current_speed
        else:
            self.velocity_x = 0
            self.velocity_y = 0

        # Откид
        if abs(self.knockback_vx) > 1 or abs(self.knockback_vy) > 1:
            self.x += self.knockback_vx * dt
            self.y += self.knockback_vy * dt
            self.knockback_vx *= max(0, 1 - self.knockback_decay * dt)
            self.knockback_vy *= max(0, 1 - self.knockback_decay * dt)

        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

        if not self.is_ghost:
            self.separate_from_others(enemies_list, dt)

    def separate_from_others(self, enemies_list, dt):
        push_x = 0.0
        push_y = 0.0
        count = 0

        for other in enemies_list:
            if other is self or not other.alive or other.is_ghost:
                continue
            dx = self.x - other.x
            dy = self.y - other.y
            dist = math.sqrt(dx * dx + dy * dy)
            min_dist = self.size + other.size

            if 0 < dist < min_dist:
                overlap = min_dist - dist
                push_x += (dx / dist) * overlap
                push_y += (dy / dist) * overlap
                count += 1

        if count > 0:
            push_force = 3.0
            self.x += push_x * push_force * dt
            self.y += push_y * push_force * dt

    def take_damage(self, damage, from_angle=None):
        """Получить урон. from_angle — откуда пришла атака (для щитовика)"""
        # Щитовик блокирует атаки спереди
        if self.shield_arc > 0 and from_angle is not None:
            angle_diff = from_angle - self.shield_angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            # Атака пришла спереди щитовика (он смотрит на игрока)
            # from_angle — это угол ОТ врага К источнику урона
            # shield_angle — это угол ОТ врага К игроку
            if abs(angle_diff) < math.radians(self.shield_arc / 2):
                damage *= 0.2  # 80% блок щитом
                self.flash_timer = 0.05

        self.hp -= damage
        self.flash_timer = 0.15

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            if self.explode_damage > 0:
                self.should_explode = True
            return True
        return False

    def apply_knockback(self, force_x, force_y):
        resist = self.knockback_resist
        self.knockback_vx += force_x * (1 - resist)
        self.knockback_vy += force_y * (1 - resist)

    def advance_attack(self, dt, player):
        """Return one impact event; a miss also spends the attack cooldown."""
        if not self.alive or getattr(self, "stun_timer", 0) > 0:
            self.windup_left = 0.0
            return None
        distance = math.hypot(player.x - self.x, player.y - self.y)
        reach = self.shoot_range or (self.strike_radius + player.size)
        if self.windup_left <= 0:
            if self.hit_cooldown <= 0 and distance <= reach:
                self.aim_angle = math.atan2(player.y - self.y, player.x - self.x)
                self.windup_dodged = False
                self.windup_left = self.windup_duration
            return None

        self.windup_left = max(0.0, self.windup_left - dt)
        if self.windup_left > 0:
            return None
        self.hit_cooldown = self.shoot_cooldown_max or 0.5
        if self.shoot_range:
            return "shot"
        return "hit" if distance <= reach else None

    def check_slide_escape(self, player, start):
        if (not player.is_sliding or not self.alive or self.shoot_range or self.windup_dodged
                or getattr(self, 'stun_timer', 0) > 0 or not 0 < self.windup_left <= PERFECT_DODGE_WINDOW):
            return False
        reach = self.strike_radius + player.size
        if math.hypot(start[0]-self.x, start[1]-self.y) <= reach < math.hypot(player.x-self.x, player.y-self.y):
            self.windup_dodged = True
            return True
        return False

    def draw_windup(self, screen, camera):
        if not self.alive or self.windup_left <= 0:
            return
        x, y = map(int, camera.apply(self.x, self.y))
        progress = 1 - self.windup_left / self.windup_duration
        color = YELLOW if progress < 0.65 else ORANGE
        if not self.shoot_range and self.windup_left <= PERFECT_DODGE_WINDOW:
            color = WHITE
        radius = self.size + 5 if self.shoot_range else self.strike_radius
        pygame.draw.circle(screen, color, (x, y), radius, 2)
        pygame.draw.circle(screen, color, (x, y), int(radius * progress), 2)
        if not self.shoot_range:
            return
        for offset in self.shot_offsets:
            angle = self.aim_angle + offset
            tip = (x + math.cos(angle) * self.shoot_range, y + math.sin(angle) * self.shoot_range)
            pygame.draw.line(screen, color, (x, y), tip, 2)

    def should_revive(self):
        """Некромант: пора ли воскрешать?"""
        if self.revive_radius <= 0 or self.revive_timer > 0:
            return False
        self.revive_timer = self.revive_cooldown_max
        return True

    def draw(self, screen, camera):
        if not self.alive:
            return

        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if sx < -60 or sx > SCREEN_WIDTH + 60 or sy < -60 or sy > SCREEN_HEIGHT + 60:
            return

        color = WHITE if self.flash_timer > 0 else self.color

        # Тень
        shadow_s = pygame.Surface((self.size * 2, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 40), (0, 0, self.size * 2, 6))
        screen.blit(shadow_s, (sx - self.size, sy + self.size - 2))

        # Рисуем по типу
        draw_method = getattr(self, f"_draw_{self.enemy_type}", None)
        if self.home_biome:
            sprite = resident_sprite(self.enemy_type, self.size, self.flash_timer > 0)
            bob = int(math.sin(self.anim_timer * 6) * 2)
            screen.blit(sprite, sprite.get_rect(center=(sx, sy + bob)))
        elif draw_method:
            draw_method(screen, sx, sy, color)
        else:
            pygame.draw.circle(screen, color, (sx, sy), self.size)
            pygame.draw.circle(screen, self.outline_color, (sx, sy), self.size, 2)

        # HP бар
        if self.hp < self.max_hp:
            bar_w = self.size * 2
            bar_h = 3
            bar_x = sx - bar_w // 2
            bar_y = sy - self.size - 8
            hp_ratio = self.hp / self.max_hp
            pygame.draw.rect(screen, DARK_RED, (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(screen, RED, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    # ──── ОТРИСОВКА ТИПОВ ────

    def _draw_skirmisher(self, screen, sx, sy, color):
        points = [(sx - 14, sy - 9), (sx, sy - 4), (sx + 14, sy - 9), (sx, sy + 13)]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, self.outline_color, points, 2)

    def _draw_crusher(self, screen, sx, sy, color):
        body = pygame.Rect(sx - 18, sy - 18, 36, 36)
        pygame.draw.rect(screen, color, body, border_radius=6)
        pygame.draw.rect(screen, self.outline_color, body, 3, border_radius=6)
        pygame.draw.line(screen, GOLD, (sx - 9, sy - 4), (sx + 9, sy - 4), 4)

    def _draw_prism(self, screen, sx, sy, color):
        points = [(sx, sy - 18), (sx + 14, sy), (sx, sy + 18), (sx - 14, sy)]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, self.outline_color, points, 2)
        pygame.draw.circle(screen, WHITE, (sx, sy), 4)

    def _draw_zombie(self, screen, sx, sy, color):
        pygame.draw.circle(screen, color, (sx, sy), self.size)
        pygame.draw.circle(screen, self.outline_color, (sx, sy), self.size, 2)
        bob = math.sin(self.anim_timer * 3) * 3
        pygame.draw.line(screen, color, (sx - self.size, sy),
                        (sx - self.size - 6, int(sy + bob + 5)), 3)
        pygame.draw.line(screen, color, (sx + self.size, sy),
                        (sx + self.size + 6, int(sy - bob + 5)), 3)
        pygame.draw.circle(screen, RED, (sx - 4, sy - 3), 3)
        pygame.draw.circle(screen, RED, (sx + 4, sy - 3), 3)

    def _draw_ghoul(self, screen, sx, sy, color):
        bob = math.sin(self.anim_timer * 8) * 2
        points = [
            (sx, sy - self.size - int(bob)),
            (sx - self.size, sy + self.size),
            (sx + self.size, sy + self.size)
        ]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, self.outline_color, points, 2)
        pygame.draw.circle(screen, WHITE, (sx - 3, sy), 2)
        pygame.draw.circle(screen, WHITE, (sx + 3, sy), 2)

    def _draw_fatty(self, screen, sx, sy, color):
        rect = pygame.Rect(sx - self.size, sy - self.size + 4,
                          self.size * 2, int(self.size * 1.6))
        pygame.draw.ellipse(screen, color, rect)
        pygame.draw.ellipse(screen, self.outline_color, rect, 2)
        pygame.draw.circle(screen, BLACK, (sx - 5, sy - 2), 3)
        pygame.draw.circle(screen, BLACK, (sx + 5, sy - 2), 3)
        pygame.draw.line(screen, BLACK, (sx - 4, sy + 6), (sx + 4, sy + 6), 2)

    def _draw_berserker(self, screen, sx, sy, color):
        pygame.draw.circle(screen, color, (sx, sy), self.size)
        spike_count = 6
        for i in range(spike_count):
            angle = (i / spike_count) * math.pi * 2 + self.anim_timer * 2
            spike_x = sx + int(math.cos(angle) * (self.size + 6))
            spike_y = sy + int(math.sin(angle) * (self.size + 6))
            pygame.draw.line(screen, DARK_RED, (sx, sy), (spike_x, spike_y), 2)
        pygame.draw.circle(screen, self.outline_color, (sx, sy), self.size, 2)
        pygame.draw.line(screen, YELLOW, (sx - 6, sy - 5), (sx - 2, sy - 2), 2)
        pygame.draw.line(screen, YELLOW, (sx + 6, sy - 5), (sx + 2, sy - 2), 2)

    def _draw_ghost(self, screen, sx, sy, color):
        points = [(sx - self.size, sy)]
        points.append((sx - self.size, sy - self.size))
        points.append((sx, sy - self.size - 4))
        points.append((sx + self.size, sy - self.size))
        points.append((sx + self.size, sy))
        wave_count = 3
        for i in range(wave_count * 2 + 1):
            wx = sx + self.size - (i * self.size * 2) / (wave_count * 2)
            wy = sy + math.sin(self.anim_timer * 4 + i) * 4
            points.append((int(wx), int(wy)))
        if len(points) >= 3:
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, self.outline_color, points, 2)
        pygame.draw.circle(screen, BLACK, (sx - 4, sy - 5), 3)
        pygame.draw.circle(screen, BLACK, (sx + 4, sy - 5), 3)

    def _draw_shooter(self, screen, sx, sy, color):
        rect = pygame.Rect(sx - self.size, sy - self.size, self.size * 2, self.size * 2)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, self.outline_color, rect, 2)
        pygame.draw.circle(screen, YELLOW, (sx, sy), 5, 1)
        pygame.draw.line(screen, YELLOW, (sx - 7, sy), (sx + 7, sy), 1)
        pygame.draw.line(screen, YELLOW, (sx, sy - 7), (sx, sy + 7), 1)

    def _draw_tank(self, screen, sx, sy, color):
        points = []
        for i in range(6):
            angle = (i / 6) * math.pi * 2 - math.pi / 2
            points.append((sx + int(math.cos(angle) * self.size),
                          sy + int(math.sin(angle) * self.size)))
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, self.outline_color, points, 3)
        pygame.draw.circle(screen, RED, (sx - 6, sy - 4), 4)
        pygame.draw.circle(screen, RED, (sx + 6, sy - 4), 4)
        pygame.draw.rect(screen, BLACK, (sx - 8, sy + 4, 16, 4))

    def _draw_necromancer(self, screen, sx, sy, color):
        # Мантия
        pygame.draw.circle(screen, color, (sx, sy), self.size)
        # Капюшон
        hood_points = [
            (sx - self.size + 2, sy + 2),
            (sx, sy - self.size - 6),
            (sx + self.size - 2, sy + 2),
        ]
        pygame.draw.polygon(screen, color, hood_points)
        pygame.draw.polygon(screen, self.outline_color, hood_points, 2)
        pygame.draw.circle(screen, self.outline_color, (sx, sy), self.size, 2)
        # Глаза (светящиеся)
        glow = int(abs(math.sin(self.anim_timer * 3)) * 255)
        eye_color = (glow, 0, glow)
        pygame.draw.circle(screen, eye_color, (sx - 4, sy - 2), 3)
        pygame.draw.circle(screen, eye_color, (sx + 4, sy - 2), 3)
        # Аура воскрешения
        if self.revive_timer < self.revive_cooldown_max * 0.3:
            aura_alpha = int(abs(math.sin(self.anim_timer * 5)) * 40)
            aura_s = pygame.Surface((self.revive_radius * 2, self.revive_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_s, (150, 0, 200, aura_alpha),
                             (self.revive_radius, self.revive_radius), self.revive_radius, 2)
            screen.blit(aura_s, (sx - self.revive_radius, sy - self.revive_radius))

    def _draw_sprinter(self, screen, sx, sy, color):
        # Аэродинамичная форма
        if self.is_sprinting:
            # Линии скорости
            for i in range(3):
                lx = sx - int(math.cos(math.atan2(self.velocity_y, self.velocity_x)) * (self.size + 5 + i * 6))
                ly = sy - int(math.sin(math.atan2(self.velocity_y, self.velocity_x)) * (self.size + 5 + i * 6))
                pygame.draw.line(screen, YELLOW, (lx, ly),
                               (lx - 8, ly), 2)
            draw_color = YELLOW
        else:
            draw_color = color

        # Ромб
        points = [
            (sx, sy - self.size),
            (sx + self.size, sy),
            (sx, sy + self.size),
            (sx - self.size, sy),
        ]
        pygame.draw.polygon(screen, draw_color, points)
        pygame.draw.polygon(screen, self.outline_color, points, 2)
        # Глаза
        pygame.draw.circle(screen, WHITE, (sx - 3, sy - 2), 2)
        pygame.draw.circle(screen, WHITE, (sx + 3, sy - 2), 2)

    def _draw_exploder(self, screen, sx, sy, color):
        # Пульсирует при низком HP
        hp_ratio = self.hp / self.max_hp
        pulse = 0
        if hp_ratio < 0.5:
            pulse = math.sin(self.anim_timer * (8 + (1 - hp_ratio) * 10)) * 3
        r = self.size + int(pulse)

        pygame.draw.circle(screen, color, (sx, sy), r)
        pygame.draw.circle(screen, self.outline_color, (sx, sy), r, 2)

        # Символ взрыва
        pygame.draw.line(screen, YELLOW, (sx - 4, sy - 4), (sx + 4, sy + 4), 2)
        pygame.draw.line(screen, YELLOW, (sx + 4, sy - 4), (sx - 4, sy + 4), 2)
        pygame.draw.line(screen, YELLOW, (sx, sy - 6), (sx, sy + 6), 2)
        pygame.draw.line(screen, YELLOW, (sx - 6, sy), (sx + 6, sy), 2)

        # Фитиль
        spark_color = YELLOW if int(self.anim_timer * 8) % 2 == 0 else ORANGE
        pygame.draw.circle(screen, spark_color, (sx, sy - r - 3), 3)

    def _draw_shielder(self, screen, sx, sy, color):
        # Тело
        pygame.draw.circle(screen, color, (sx, sy), self.size)
        pygame.draw.circle(screen, self.outline_color, (sx, sy), self.size, 2)

        # Щит (дуга спереди)
        shield_r = self.size + 6
        start_a = -self.shield_angle - math.radians(self.shield_arc / 2)
        end_a = -self.shield_angle + math.radians(self.shield_arc / 2)
        shield_rect = pygame.Rect(sx - shield_r, sy - shield_r, shield_r * 2, shield_r * 2)
        try:
            pygame.draw.arc(screen, GOLD, shield_rect, start_a, end_a, 4)
        except:
            pass

        # Глаза за щитом
        pygame.draw.circle(screen, WHITE, (sx - 3, sy - 2), 3)
        pygame.draw.circle(screen, WHITE, (sx + 3, sy - 2), 3)
        pygame.draw.circle(screen, BLACK, (sx - 3, sy - 2), 1)
        pygame.draw.circle(screen, BLACK, (sx + 3, sy - 2), 1)


class Boss(Enemy):
    def __init__(self, x, y, difficulty_multiplier=1.0):
        super().__init__(x, y, "zombie", difficulty_multiplier)

        self.enemy_type = "boss"
        self.max_hp = BOSS_HP * difficulty_multiplier
        self.hp = self.max_hp
        self.base_speed = BOSS_SPEED
        self.speed = BOSS_SPEED
        self.damage = BOSS_DAMAGE * difficulty_multiplier
        self.size = BOSS_SIZE
        self.strike_radius = BOSS_SIZE + 20
        self.windup_duration = 0.375
        self.color = BOSS_COLOR
        self.outline_color = BOSS_OUTLINE_COLOR
        self.xp_reward = BOSS_XP
        self.knockback_resist = BOSS_KNOCKBACK_RESIST
        self.is_boss = True
        self.no_despawn = True  # Босс не деспавнится!

        self.phase_2_triggered = False
        self.is_enraged = False

        # Арена
        self.arena_center_x = x
        self.arena_center_y = y
        self.arena_active = True

    def set_arena_center(self, px, py):
        """Установить центр арены на позицию игрока при спавне босса"""
        self.arena_center_x = px
        self.arena_center_y = py

    def update(self, dt, player_x, player_y, enemies_list, game_messages=None):
        super().update(dt, player_x, player_y, enemies_list)

        if self.hp / self.max_hp < 0.5 and not self.phase_2_triggered:
            self.phase_2_triggered = True
            self.is_enraged = True
            self.base_speed = BOSS_SPEED * 1.3
            self.color = CRIMSON
            if game_messages is not None:
                game_messages.append(t("BOSS_PHASE_2"))

    def draw(self, screen, camera):
        if not self.alive:
            return

        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        if sx < -100 or sx > SCREEN_WIDTH + 100 or sy < -100 or sy > SCREEN_HEIGHT + 100:
            return

        color = WHITE if self.flash_timer > 0 else self.color

        # Тень
        shadow_s = pygame.Surface((self.size * 3, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 50), (0, 0, self.size * 3, 12))
        screen.blit(shadow_s, (sx - self.size * 3 // 2, sy + self.size - 3))

        # Аура босса
        aura_pulse = abs(math.sin(self.anim_timer * 2))
        aura_r = self.size + 10 + int(aura_pulse * 8)
        aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_s, (150, 0, 200, 30), (aura_r, aura_r), aura_r)
        screen.blit(aura_s, (sx - aura_r, sy - aura_r))

        # Тело
        pygame.draw.circle(screen, color, (sx, sy), self.size)

        # Корона
        crown_base_y = sy - self.size + 5
        crown_width = self.size
        crown_height = 18
        spikes = 5
        crown_points = [(sx - crown_width, crown_base_y)]
        for i in range(spikes * 2 + 1):
            cx = sx - crown_width + (i * crown_width * 2) / (spikes * 2)
            cy = crown_base_y if i % 2 == 0 else crown_base_y - crown_height
            crown_points.append((int(cx), int(cy)))
        crown_points.append((sx + crown_width, crown_base_y))
        if len(crown_points) >= 3:
            pygame.draw.polygon(screen, GOLD, crown_points)
            pygame.draw.polygon(screen, ORANGE, crown_points, 2)

        # Обводка
        pygame.draw.circle(screen, self.outline_color, (sx, sy), self.size, 3)

        # Глаза
        for ex in [-12, 12]:
            pygame.draw.circle(screen, RED, (sx + ex, sy - 8), 7)
            pygame.draw.circle(screen, (255, 0, 0), (sx + ex, sy - 8), 4)
            pygame.draw.circle(screen, BLACK, (sx + ex, sy - 8), 2)

        # Рот
        pygame.draw.arc(screen, BLACK, (sx - 15, sy + 2, 30, 20), math.pi, 2 * math.pi, 3)

        # HP бар
        bar_w = self.size * 3
        bar_h = 8
        bar_x = sx - bar_w // 2
        bar_y = sy - self.size - 25
        hp_ratio = self.hp / self.max_hp

        # Фон
        pygame.draw.rect(screen, (40, 0, 0), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(screen, DARK_RED, (bar_x, bar_y, bar_w, bar_h))

        # HP
        hp_color = RED
        if hp_ratio < 0.3:
            hp_color = ORANGE
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        # Имя
        font = face("display", 14)
        name = font.render("БОСС", True, GOLD)
        screen.blit(name, (sx - name.get_width() // 2, bar_y - 18))

    def draw_arena(self, screen, camera):
        """Нарисовать стены арены"""
        if not self.arena_active or not self.alive:
            return

        cx, cy = camera.apply(self.arena_center_x, self.arena_center_y)
        cx, cy = int(cx), int(cy)
        r = BOSS_ARENA_RADIUS

        # Полупрозрачная стена
        pulse = abs(math.sin(self.anim_timer * 1.5))
        alpha = int(80 + 40 * pulse)

        arena_s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Рисуем непроходимую стену как кольцо
        pygame.draw.circle(arena_s, (150, 0, 200, alpha), (cx, cy), r, BOSS_ARENA_WALL_THICKNESS)

        # Внутреннее свечение
        pygame.draw.circle(arena_s, (200, 50, 255, 20), (cx, cy), r - 5, 3)

        screen.blit(arena_s, (0, 0))

        # Индикаторы на стене (точки)
        num_dots = 24
        for i in range(num_dots):
            angle = (i / num_dots) * math.pi * 2 + self.anim_timer * 0.5
            dx = cx + int(math.cos(angle) * r)
            dy = cy + int(math.sin(angle) * r)
            dot_alpha = int(150 + 100 * math.sin(self.anim_timer * 3 + i))
            dot_alpha = max(50, min(255, dot_alpha))
            pygame.draw.circle(screen, (200, 100, 255), (dx, dy), 3)


class EnemyProjectile:
    def __init__(self, x, y, dir_x, dir_y, speed, damage):
        self.x = float(x)
        self.y = float(y)
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.speed = speed
        self.damage = damage
        self.size = ENEMY_PROJECTILE_SIZE
        self.lifetime = ENEMY_PROJECTILE_LIFETIME
        self.alive = True

    def update(self, dt, speed_scale=1.0):
        self.x += self.dir_x * self.speed * dt * speed_scale
        self.y += self.dir_y * self.speed * dt * speed_scale
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive:
            return
        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)
        pygame.draw.circle(screen, ENEMY_PROJECTILE_COLOR, (sx, sy), self.size)
        pygame.draw.circle(screen, YELLOW, (sx, sy), self.size, 1)
        # Хвост
        tx = sx - int(self.dir_x * 8)
        ty = sy - int(self.dir_y * 8)
        pygame.draw.line(screen, ORANGE, (sx, sy), (tx, ty), 2)


class EnemySpawner:
    def __init__(self, world=None):
        self.world = world
        self.spawn_timer = 0.0
        self.boss_timer = 0.0
        self.game_time = 0.0
        self.difficulty_multiplier = 1.0

        self.difficulty_thresholds = [
            (60, 1.2, "MSG_DIFF_1"),
            (120, 1.5, "MSG_DIFF_2"),
            (180, 1.8, "MSG_DIFF_3"),
            (240, 2.2, "MSG_DIFF_4"),
            (300, 2.5, "MSG_DIFF_5"),
            (420, 3.0, "MSG_DIFF_6"),
        ]
        self.next_threshold_idx = 0

    def update(self, dt, player_x, player_y, enemies, game_messages):
        self.game_time += dt
        self.boss_timer += dt

        if self.next_threshold_idx < len(self.difficulty_thresholds):
            threshold_time, mult, msg_key = self.difficulty_thresholds[self.next_threshold_idx]
            if self.game_time >= threshold_time:
                self.difficulty_multiplier = mult
                game_messages.append(t(msg_key))
                self.next_threshold_idx += 1

        time_ratio = min(self.game_time / ENEMY_DIFFICULTY_SCALE_TIME, 1.0)
        spawn_rate = ENEMY_SPAWN_RATE_BASE + (ENEMY_SPAWN_RATE_MAX - ENEMY_SPAWN_RATE_BASE) * time_ratio

        self.spawn_timer += dt
        spawn_interval = 1.0 / spawn_rate

        while self.spawn_timer >= spawn_interval:
            self.spawn_timer -= spawn_interval
            if len(enemies) < ENEMY_MAX_COUNT:
                enemy = self.spawn_enemy(player_x, player_y)
                if enemy:
                    enemies.append(enemy)

        if self.boss_timer >= BOSS_SPAWN_INTERVAL:
            self.boss_timer = 0
            boss = self.spawn_boss(player_x, player_y)
            boss.set_arena_center(player_x, player_y)
            enemies.append(boss)
            game_messages.append(t("MSG_BOSS_SPAWNED"))

        return None  # возврат босса если нужен

    def spawn_enemy(self, player_x, player_y):
        angle = random.random() * math.pi * 2
        dist = random.uniform(ENEMY_SPAWN_RADIUS_MIN, ENEMY_SPAWN_RADIUS_MAX)
        spawn_x = player_x + math.cos(angle) * dist
        spawn_y = player_y + math.sin(angle) * dist

        if self.world is not None and random.random() < RESIDENT_SPAWN_CHANCE:
            habitat = self.world.biome_at(spawn_x, spawn_y).key
            return Enemy(spawn_x, spawn_y, RESIDENT_BY_BIOME[habitat], self.difficulty_multiplier)

        available_types = []
        total_weight = 0
        for etype, data in ENEMY_TYPES.items():
            if self.game_time >= data["min_time"]:
                available_types.append((etype, data["weight"]))
                total_weight += data["weight"]

        if not available_types:
            return None

        roll = random.random() * total_weight
        cumulative = 0
        chosen_type = available_types[0][0]
        for etype, weight in available_types:
            cumulative += weight
            if roll <= cumulative:
                chosen_type = etype
                break

        return Enemy(spawn_x, spawn_y, chosen_type, self.difficulty_multiplier)

    def spawn_boss(self, player_x, player_y):
        angle = random.random() * math.pi * 2
        dist = ENEMY_SPAWN_RADIUS_MAX * 0.7
        spawn_x = player_x + math.cos(angle) * dist
        spawn_y = player_y + math.sin(angle) * dist
        return Boss(spawn_x, spawn_y, self.difficulty_multiplier)