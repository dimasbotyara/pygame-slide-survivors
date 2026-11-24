# player.py — v4 — МОЩНЫЕ кулаки, мега-удары, ярость, волны

import pygame
import math
import random as rng_module
from settings import *
from heroes import get_hero_data
from preferences import BINDINGS
from consumables import TONICS, TONIC_BY_STAT



class FistWave:
    """Волна от удара кулаком — летит вперёд и наносит урон"""
    def __init__(self, x, y, angle, damage, speed, max_range, width):
        self.x = float(x)
        self.y = float(y)
        self.start_x = x
        self.start_y = y
        self.angle = angle
        self.dir_x = math.cos(angle)
        self.dir_y = math.sin(angle)
        self.damage = damage
        self.speed = speed
        self.max_range = max_range
        self.width = width
        self.alive = True
        self.hit_enemies = []
        self.distance_traveled = 0.0

    def update(self, dt):
        if not self.alive:
            return
        move = self.speed * dt
        self.x += self.dir_x * move
        self.y += self.dir_y * move
        self.distance_traveled += move
        if self.distance_traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive:
            return
        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        alpha = 1.0 - self.distance_traveled / self.max_range
        w = int(self.width * alpha)
        if w < 2:
            return

        # Дуга/полумесяц
        perp_x = -self.dir_y
        perp_y = self.dir_x

        points = []
        segments = 8
        for i in range(segments + 1):
            t = (i / segments - 0.5) * 2
            px = sx + int(perp_x * t * w)
            py = sy + int(perp_y * t * w)
            # Выпуклость вперёд
            bulge = (1 - t * t) * w * 0.3
            px += int(self.dir_x * bulge)
            py += int(self.dir_y * bulge)
            points.append((px, py))

        if len(points) >= 2:
            cv = int(255 * alpha)
            color = (cv, cv // 2, 0)
            pygame.draw.lines(screen, color, False, points, max(1, int(3 * alpha)))

            # Центральная точка
            pygame.draw.circle(screen, YELLOW, (sx, sy), max(2, int(4 * alpha)))


class Player:
    def __init__(self, x, y, hero_id="slider"):
        self.x = float(x)
        self.y = float(y)

        hero_data = get_hero_data(hero_id)
        self.hero_id = hero_id
        self.bindings = dict(BINDINGS)
        self.hero_data = hero_data

        self.max_hp = hero_data["base_hp"]
        self.hp = self.max_hp
        self.base_speed = hero_data["base_speed"]
        self.size = PLAYER_BASE_SIZE

        self.player_color = hero_data["color"]
        self.outline_color = hero_data["outline_color"]

        self.stats = {
            "max_hp": 0, "hp_regen": 0.0, "move_speed": 0, "armor": 0,
            "xp_radius": 0, "luck": 0,
            "damage": 0, "attack_speed": 0, "attack_range": 0,
            "crit_chance": hero_data["crit_chance"],
            "crit_multiplier": hero_data["crit_mult"],
            "target_count": 0,
            "fist_combo_hits": 0, "fist_lifesteal": hero_data["lifesteal"], "fist_stun_chance": 0,
            "fist_rage": 0, "fist_ground_slam": 0, "fist_counter_attack": 0,
            "fist_arc_bonus": 0, "fist_wave": 0, "fist_xp_pull": 0,
            "slide_speed": 0, "slide_duration": 0, "slide_cooldown": 0,
            "slide_damage": 0, "slide_knockback_radius": 0,
            "slide_charges": max(0, hero_data["slide_charges"] - 1),
            "slide_kill_reset_chance": 0, "slide_turn_speed": 0,
            "slide_invincibility_after": 0.0,
            "slide_electric_trail": 1 if "slide_electric" in hero_data["bonus_upgrades"] else 0,
            "slide_shockwave": 0,
            "xp_multiplier": 0, "drop_chance": 0, "heal_effectiveness": 0,
            "aura_damage": 0.0, "aura_slow": 0, "block_chance": 0, "thorns": 0,
            "projectile_count": 0, "projectile_spread": 0,
            "effect_duration": 0, "pierce": 0,
            # Новые механики (апгрейды)
            "shield_max": 0, "executioner_chance": 0, "poison_thorns": 0,
            "time_warp": 0, "giant_growth": 0, "adrenaline": 0,
            "double_impact_chance": 0, "orbital_blade_count": 0,
            "heal_on_kills": 0,
            "ice_trail": 0, "repulse_aura": 0, "drain_aura": 0, "stasis_aura": 0,
            "cleave": 0, "combo_grace": 0, "ult_per_kill": 0,
            "hit_grace": 0, "boost_duration": 0,
        }

        # Ультимейт, щит и статистика
        self.ult_charge = 0.0  # 0.0 - 100.0
        self.ult_cooldown_timer = 0.0
        self.ult_cast_timer = 0.0
        self.ult_cast_duration = 0.0
        self.ultimate_action_lock = False
        self.total_slides_count = 0
        self.shield_hp = 0.0
        self.shield_regen_timer = 0.0
        self.adrenaline_timer = 0.0
        self.adrenaline_active = False
        self.orbital_blades_angle = 0.0
        self.orbital_blade_hit_enemies = {}  # enemy_id -> cooldown
        self.giant_growth_active = False
        self.base_size = PLAYER_BASE_SIZE
        self.time_warp_active = False

        # Скольжение
        self.is_sliding = False
        self.slide_timer = 0.0
        self.slide_cooldown_timer = 0.0
        self.slide_charges = 1
        self.slide_max_charges = 1
        self.slide_direction_x = 0.0
        self.slide_direction_y = 0.0
        self.slide_current_speed = 0.0
        self.slide_angle = 0.0
        self.slide_was_pressed = False
        self.slide_needs_repress = False
        # Кулдаун повторного урона скольжения по одному и тому же врагу
        self.slide_hit_timers = {}

        # Kill комбо
        self.combo_count = 0
        self.combo_timer = 0.0
        self.combo_window = COMBO_TIMEOUT
        self.combo_max_reached = 0

        # Кулаки
        self.dodge_charge = False
        self.fist_dodge_cleave = False
        self.fist_combo_index = 0
        self.fist_combo_timer = 0.0
        self.fist_cooldown_timer = 0.0
        self.fist_attack_active = False
        self.fist_attack_timer = 0.0
        self.fist_attack_duration = 0.12
        self.fist_hit_enemies = []
        self.fist_which_hand = 0
        self.swing_combo_index = 0
        self.swing_cleave = False
        self.slam_triggered = False
        self.fist_total_hits = 0  # общий счётчик ударов для мега-удара
        self.fist_is_mega = False  # текущий удар — мега?

        # Волны от кулаков
        self.fist_waves = []

        # Контратака
        self.counter_attack_active = False
        self.counter_attack_timer = 0.0
        self.counter_attack_duration = 0.15
        self.counter_attack_hit_enemies = []
        self.counter_invincible_timer = 0.0

        # Shockwave & electric
        self.shockwaves = []
        self.electric_trails = []

        # Движение
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.current_speed = 0.0
        self.facing_angle = 0.0

        # Неуязвимость
        self.invincible_timer = 0.0
        self.slide_invincible_after_timer = 0.0
        # Вампиризм отключён, пока действует окно неуязвимости + 0.3с после удара
        self.lifesteal_block_timer = 0.0

        # Опыт
        self.level = 1
        self.xp = 0
        self.xp_to_next = XP_BASE_TO_LEVEL
        self.pending_levels = 0

        # Временные
        self.speed_boost_timer = 0.0
        self.speed_boost_multiplier = 1.0
        self.tonic_timers = {}

        self.level_up_rings = []
        self.color = self.player_color
        self.flash_timer = 0.0
        self.body_anim_timer = 0.0
        self.rage_intensity = 0.0

        self.enemies_killed = 0
        self.damage_dealt = 0
        self.time_alive = 0.0

    # ================================================================
    # СТАТЫ
    # ================================================================
    def effective_stat(self, stat):
        item = TONIC_BY_STAT.get(stat)
        return self.stats[stat] + (TONICS[item].bonus if item in self.tonic_timers else 0)

    def update_tonics(self, dt):
        for item in list(self.tonic_timers):
            self.tonic_timers[item] -= dt
            if self.tonic_timers[item] <= 0:
                del self.tonic_timers[item]

    def get_max_hp(self):
        return PLAYER_BASE_HP + self.stats["max_hp"]

    def get_move_speed(self):
        base = PLAYER_BASE_SPEED * (1 + self.stats["move_speed"] / 100)
        if self.speed_boost_timer > 0:
            base *= self.speed_boost_multiplier
        # Адреналин — бонус скорости после получения урона
        if self.adrenaline_timer > 0 and self.stats.get("adrenaline", 0) > 0:
            base *= 1.0 + 0.15 * self.stats["adrenaline"]
        return base

    def get_xp_radius(self):
        return XP_PICKUP_RADIUS_BASE * (1 + self.effective_stat("xp_radius") / 100)

    def get_fist_damage(self):
        base = FIST_BASE_DAMAGE * (1 + self.effective_stat("damage") / 100)
        # Ярость
        if self.stats["fist_rage"] > 0:
            hp_ratio = self.hp / self.max_hp
            if hp_ratio < FIST_RAGE_THRESHOLD:
                rage_progress = 1.0 - (hp_ratio / FIST_RAGE_THRESHOLD)
                rage_bonus = FIST_RAGE_MAX_BONUS * (self.stats["fist_rage"] / 100) * rage_progress
                base *= (1 + rage_bonus / 100)
        return base

    def get_fist_attack_speed(self):
        base = FIST_BASE_ATTACK_SPEED * (1 + self.effective_stat("attack_speed") / 100)
        # Ярость бонус к скорости атаки
        if self.stats["fist_rage"] > 0:
            hp_ratio = self.hp / self.max_hp
            if hp_ratio < FIST_RAGE_THRESHOLD:
                rage_progress = 1.0 - (hp_ratio / FIST_RAGE_THRESHOLD)
                speed_bonus = FIST_RAGE_ATTACK_SPEED_BONUS * (self.stats["fist_rage"] / 100) * rage_progress
                base *= (1 + speed_bonus / 100)
        return base

    def get_fist_range(self):
        return FIST_BASE_RANGE * (1 + self.effective_stat("attack_range") / 100)

    def get_fist_combo_max(self):
        return FIST_COMBO_HITS + self.stats["fist_combo_hits"]

    def get_fist_stun_chance(self):
        return self.effective_stat("fist_stun_chance")

    def get_fist_lifesteal(self):
        return self.effective_stat("fist_lifesteal")

    def get_fist_arc(self, combo_index):
        if combo_index < len(FIST_COMBO_ARC):
            base_arc = FIST_COMBO_ARC[combo_index]
        else:
            base_arc = FIST_COMBO_ARC[-1]
        return base_arc + self.stats["fist_arc_bonus"]

    def get_fist_damage_for_hit(self, combo_index):
        base = self.get_fist_damage()
        if self.fist_is_mega:
            return base * FIST_MEGA_DAMAGE_MULTIPLIER
        if combo_index < len(FIST_COMBO_DAMAGE_MULTIPLIERS):
            return base * FIST_COMBO_DAMAGE_MULTIPLIERS[combo_index]
        return base * FIST_COMBO_DAMAGE_MULTIPLIERS[-1]

    def get_fist_knockback_for_hit(self, combo_index):
        base = FIST_KNOCKBACK
        if self.fist_is_mega:
            return base * FIST_MEGA_KNOCKBACK_MULTIPLIER
        if combo_index < len(FIST_COMBO_KNOCKBACK_MULTIPLIERS):
            return base * FIST_COMBO_KNOCKBACK_MULTIPLIERS[combo_index]
        return base * FIST_COMBO_KNOCKBACK_MULTIPLIERS[-1]

    def get_fist_range_for_hit(self, combo_index):
        base = self.get_fist_range()
        if self.fist_is_mega:
            return base * FIST_MEGA_RANGE_MULTIPLIER
        if combo_index < len(FIST_COMBO_RANGE_MULTIPLIERS):
            return base * FIST_COMBO_RANGE_MULTIPLIERS[combo_index]
        return base * FIST_COMBO_RANGE_MULTIPLIERS[-1]

    def get_slide_initial_speed(self):
        return self.get_move_speed() * SLIDE_INITIAL_SPEED_MULTIPLIER * (1 + self.effective_stat("slide_speed") / 100)

    def get_slide_duration(self):
        return SLIDE_DURATION * (1 + self.stats["slide_duration"] / 100)

    def get_slide_cooldown(self):
        return SLIDE_COOLDOWN * max(0.1, (1 - self.stats["slide_cooldown"] / 100))

    def get_slide_knockback_damage(self):
        base = (SLIDE_BASE_KNOCKBACK_DAMAGE
                + self.slide_current_speed * SLIDE_SPEED_DAMAGE_MULTIPLIER)
        base *= (1 + self.effective_stat("slide_damage") / 100)
        # Слайдер скользит «по-настоящему», у остальных это в основном рывок
        base *= self.hero_data.get("slide_damage_mult", 1.0)
        return base

    def get_slide_knockback_radius(self):
        return SLIDE_KNOCKBACK_RADIUS + self.size + self.stats["slide_knockback_radius"]

    def get_slide_turn_speed(self):
        return SLIDE_TURN_SPEED * (1 + self.effective_stat("slide_turn_speed") / 100)

    def get_slide_max_charges(self):
        return 1 + self.stats["slide_charges"]

    def get_armor(self):
        return self.effective_stat("armor")

    def get_crit_chance(self):
        return self.effective_stat("crit_chance") + self.stats["luck"]

    def get_crit_multiplier(self):
        return 1.0 + self.stats["crit_multiplier"] / 100

    def get_xp_multiplier(self):
        return 1.0 + self.effective_stat("xp_multiplier") / 100

    def get_heal_effectiveness(self):
        return 1.0 + self.stats["heal_effectiveness"] / 100

    def get_combo_xp_bonus(self):
        return min(self.combo_count * COMBO_XP_BONUS_PER_STACK, COMBO_MAX_MULTIPLIER)

    def get_rage_intensity(self):
        if self.stats["fist_rage"] <= 0:
            return 0.0
        hp_ratio = self.hp / self.max_hp
        if hp_ratio >= FIST_RAGE_THRESHOLD:
            return 0.0
        return 1.0 - (hp_ratio / FIST_RAGE_THRESHOLD)

    # ================================================================
    # UPDATE
    # ================================================================
    def update(self, dt, keys, mouse_pos, camera):
        self.update_tonics(dt)
        self.time_alive += dt
        self.body_anim_timer += dt
        cast_locked = self.ult_cast_timer > 0 or self.ultimate_action_lock
        self.ult_cast_timer = max(0.0, self.ult_cast_timer - dt)
        if self.ult_cast_timer < 1e-7:
            self.ult_cast_timer = 0.0
        self.ult_cooldown_timer = max(0.0, self.ult_cooldown_timer - dt)

        new_max = self.get_max_hp()
        if new_max != self.max_hp:
            hp_diff = new_max - self.max_hp
            self.max_hp = new_max
            self.hp = min(self.hp + max(0, hp_diff), self.max_hp)

        self.slide_max_charges = self.get_slide_max_charges()

        if self.stats["hp_regen"] > 0:
            self.hp = min(self.hp + self.stats["hp_regen"] * dt, self.max_hp)

        # Таймеры
        for attr in ['invincible_timer', 'slide_invincible_after_timer',
                      'flash_timer', 'speed_boost_timer', 'counter_invincible_timer',
                      'lifesteal_block_timer']:
            val = getattr(self, attr)
            if val > 0:
                setattr(self, attr, val - dt)

        if self.combo_count > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0
                self.combo_timer = 0.0

        if self.counter_attack_active:
            self.counter_attack_timer -= dt
            if self.counter_attack_timer <= 0:
                self.counter_attack_active = False
                self.counter_attack_hit_enemies = []

        if self.slide_charges < self.slide_max_charges:
            self.slide_cooldown_timer -= dt
            if self.slide_cooldown_timer <= 0:
                self.slide_charges = min(self.slide_charges + 1, self.slide_max_charges)
                if self.slide_charges < self.slide_max_charges:
                    self.slide_cooldown_timer = self.get_slide_cooldown()

        # Level-up кольца
        self.level_up_rings = [(r + LEVEL_UP_RING_SPEED * dt, lt - dt, mlt)
                               for r, lt, mlt in self.level_up_rings
                               if lt - dt > 0 and r + LEVEL_UP_RING_SPEED * dt < LEVEL_UP_RING_MAX_RADIUS]

        # Shockwaves
        self.shockwaves = [(wx, wy, wr + SHOCKWAVE_SPEED * dt, wmr, wd)
                           for wx, wy, wr, wmr, wd in self.shockwaves
                           if wr + SHOCKWAVE_SPEED * dt < wmr]

        # Electric trails
        self.electric_trails = [(tx, ty, tt - dt)
                                for tx, ty, tt in self.electric_trails
                                if tt - dt > 0]

        # Fist waves
        for wave in self.fist_waves:
            wave.update(dt)
        self.fist_waves = [w for w in self.fist_waves if w.alive]

        # ── Новые механики апгрейдов ──

        # Орбитальные клинки — вращение
        blade_count = self.stats.get("orbital_blade_count", 0)
        if blade_count > 0:
            self.orbital_blades_angle += 3.0 * dt  # оборот ~2 секунды
            # Уменьшаем кулдауны попаданий
            for eid in list(self.orbital_blade_hit_enemies.keys()):
                self.orbital_blade_hit_enemies[eid] -= dt
                if self.orbital_blade_hit_enemies[eid] <= 0:
                    del self.orbital_blade_hit_enemies[eid]

        # Щит — регенерация
        shield_max = self.stats.get("shield_max", 0)
        if shield_max > 0:
            if self.shield_hp < shield_max:
                self.shield_regen_timer += dt
                if self.shield_regen_timer >= 3.0:  # через 3 секунды после урона
                    regen_rate = shield_max * 0.15  # 15% в секунду
                    self.shield_hp = min(shield_max, self.shield_hp + regen_rate * dt)

        # Адреналин — таймер затухания
        if self.adrenaline_timer > 0:
            self.adrenaline_timer -= dt
            self.adrenaline_active = True
        else:
            self.adrenaline_active = False

        # Гигантский рост — масштабирование размера
        giant_lvl = self.stats.get("giant_growth", 0)
        if giant_lvl > 0:
            self.size = self.base_size + giant_lvl * 5  # +5 за уровень
            self.giant_growth_active = True
        else:
            self.size = self.base_size
            self.giant_growth_active = False

        # Time Warp флаг (обработка замедления — в main.py)
        self.time_warp_active = self.stats.get("time_warp", 0) > 0

        self.rage_intensity = self.get_rage_intensity()

        # Направление
        world_mouse_x, world_mouse_y = camera.reverse(mouse_pos[0], mouse_pos[1])
        dx = world_mouse_x - self.x
        dy = world_mouse_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            self.facing_angle = math.atan2(dy, dx)

        if cast_locked:
            # Ultimate wind-up is a committed pose: no walk, slide, dash, or
            # fist input may move the player until the cast resolves.
            self.is_sliding = False
            self.slide_current_speed = 0.0
            self.velocity_x = self.velocity_y = 0.0
            self.current_speed = 0.0
            self.fist_attack_active = False
        else:
            slide_pressed = keys[self.bindings["bind_slide"]] or (self.bindings["bind_slide"] == pygame.K_SPACE and ((pygame.K_LSHIFT not in self.bindings.values() and keys[pygame.K_LSHIFT]) or (pygame.K_RSHIFT not in self.bindings.values() and keys[pygame.K_RSHIFT])))
            if not slide_pressed:
                if self.is_sliding:
                    self.stop_slide()
                self.slide_was_pressed = False
                self.slide_needs_repress = False
            else:
                if not self.slide_was_pressed and not self.slide_needs_repress:
                    if not self.is_sliding and self.slide_charges > 0:
                        self.start_slide()
                    self.slide_was_pressed = True

            if self.is_sliding:
                self.update_slide(dt, world_mouse_x, world_mouse_y)
            else:
                self.update_movement(dt, keys)

            self.current_speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
            self.update_fist_attack(dt)
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

    def update_movement(self, dt, keys):
        mx, my = 0, 0
        if (keys[self.bindings["bind_up"]] or (self.bindings["bind_up"] == pygame.K_w and pygame.K_UP not in self.bindings.values() and keys[pygame.K_UP])): my -= 1
        if (keys[self.bindings["bind_down"]] or (self.bindings["bind_down"] == pygame.K_s and pygame.K_DOWN not in self.bindings.values() and keys[pygame.K_DOWN])): my += 1
        if (keys[self.bindings["bind_left"]] or (self.bindings["bind_left"] == pygame.K_a and pygame.K_LEFT not in self.bindings.values() and keys[pygame.K_LEFT])): mx -= 1
        if (keys[self.bindings["bind_right"]] or (self.bindings["bind_right"] == pygame.K_d and pygame.K_RIGHT not in self.bindings.values() and keys[pygame.K_RIGHT])): mx += 1
        if mx != 0 and my != 0:
            mx *= 0.7071
            my *= 0.7071
        speed = self.get_move_speed()
        self.velocity_x = mx * speed
        self.velocity_y = my * speed

    # ── Скольжение ──
    def start_slide(self):
        self.is_sliding = True
        self.total_slides_count += 1
        self.slide_timer = 0.0
        self.slide_hit_timers.clear()
        self.slide_charges -= 1
        if self.slide_charges < self.slide_max_charges and self.slide_cooldown_timer <= 0:
            self.slide_cooldown_timer = self.get_slide_cooldown()
        self.slide_angle = self.facing_angle
        self.slide_direction_x = math.cos(self.slide_angle)
        self.slide_direction_y = math.sin(self.slide_angle)
        self.slide_current_speed = self.get_slide_initial_speed()

    def stop_slide(self):
        was_fast = self.is_slide_knockback_active()
        self.is_sliding = False
        self.slide_timer = 0.0
        self.slide_current_speed = 0.0
        self.slide_needs_repress = True
        if self.stats["slide_invincibility_after"] > 0:
            self.slide_invincible_after_timer = self.stats["slide_invincibility_after"]
        if self.stats["slide_shockwave"] > 0 and was_fast:
            damage = self.get_slide_knockback_damage() * SHOCKWAVE_DAMAGE_MULTIPLIER * self.stats["slide_shockwave"]
            self.shockwaves.append((self.x, self.y, 0, SHOCKWAVE_RADIUS, damage))

    def update_slide(self, dt, mx, my):
        self.slide_timer += dt
        duration = self.get_slide_duration()
        progress = min(self.slide_timer / duration, 1.0)
        speed_factor = max(0, 1.0 - progress ** SLIDE_DECELERATION_CURVE)
        self.slide_current_speed = self.get_slide_initial_speed() * speed_factor

        # Кулдауны повторного урона по врагам
        for eid in list(self.slide_hit_timers):
            self.slide_hit_timers[eid] -= dt
            if self.slide_hit_timers[eid] <= 0:
                del self.slide_hit_timers[eid]

        target_angle = math.atan2(my - self.y, mx - self.x)
        angle_diff = target_angle - self.slide_angle
        while angle_diff > math.pi: angle_diff -= 2 * math.pi
        while angle_diff < -math.pi: angle_diff += 2 * math.pi
        max_turn = math.radians(self.get_slide_turn_speed()) * dt
        if abs(angle_diff) > max_turn:
            angle_diff = max_turn if angle_diff > 0 else -max_turn

        self.slide_angle += angle_diff
        self.slide_direction_x = math.cos(self.slide_angle)
        self.slide_direction_y = math.sin(self.slide_angle)
        self.velocity_x = self.slide_direction_x * self.slide_current_speed
        self.velocity_y = self.slide_direction_y * self.slide_current_speed

        if self.stats["slide_electric_trail"] > 0 and self.slide_current_speed > 100:
            self.electric_trails.append((self.x, self.y, ELECTRIC_TRAIL_DURATION))

        if progress >= 1.0:
            self.stop_slide()

    def is_slide_knockback_active(self):
        return self.is_sliding and self.slide_current_speed > self.get_move_speed()

    def is_invincible(self):
        return (self.invincible_timer > 0 or
                self.is_slide_knockback_active() or
                self.slide_invincible_after_timer > 0 or
                self.counter_invincible_timer > 0)

    # ── Кулаки ──
    def update_fist_attack(self, dt):
        attack_speed = self.get_fist_attack_speed()
        cooldown = 1.0 / attack_speed if attack_speed > 0 else 999

        if self.fist_combo_timer > 0:
            self.fist_combo_timer -= dt
            if self.fist_combo_timer <= 0:
                self.fist_combo_index = 0

        if self.fist_attack_active:
            self.fist_attack_timer -= dt
            if self.fist_attack_timer <= 0:
                self.fist_attack_active = False
                self.fist_hit_enemies = []

        self.fist_cooldown_timer -= dt
        if self.fist_cooldown_timer <= 0 and not self.fist_attack_active:
            max_combo = self.get_fist_combo_max()
            current_hit = self.fist_combo_index % max_combo

            self.swing_combo_index = current_hit
            self.slam_triggered = False
            next_hit = self.fist_total_hits + 1
            self.swing_cleave = self.stats["cleave"] > 0 and next_hit % 4 == 0
            self.fist_dodge_cleave = self.dodge_charge
            self.dodge_charge = False

            # Мега-удар?
            self.fist_is_mega = (next_hit % FIST_MEGA_HIT_EVERY == 0)

            self.fist_attack_active = True
            self.fist_attack_timer = self.fist_attack_duration
            self.fist_cooldown_timer = cooldown
            self.fist_hit_enemies = []

            if self.fist_is_mega:
                self.fist_which_hand = 2
            elif current_hit == max_combo - 1:
                self.fist_which_hand = 2
            else:
                self.fist_which_hand = current_hit % 2

            # Волна от удара
            if self.stats["fist_wave"] > 0:
                wave_damage = self.get_fist_damage_for_hit(current_hit) * FIST_WAVE_DAMAGE_RATIO * self.stats["fist_wave"]
                wave = FistWave(
                    self.x + math.cos(self.facing_angle) * self.size,
                    self.y + math.sin(self.facing_angle) * self.size,
                    self.facing_angle, wave_damage,
                    FIST_WAVE_SPEED,
                    FIST_WAVE_RANGE + self.stats["fist_wave"] * 30,
                    FIST_WAVE_WIDTH + self.stats["fist_wave"] * 10
                )
                self.fist_waves.append(wave)

    def record_fist_contact(self, enemy):
        # A sweep may connect with several enemies across multiple frames.
        if not self.fist_hit_enemies:
            self.fist_total_hits += 1
            self.fist_combo_index = (self.swing_combo_index + 1) % self.get_fist_combo_max()
            self.fist_combo_timer = FIST_COMBO_WINDOW
        self.fist_hit_enemies.append(enemy)

    def get_fist_attack_area(self):
        if not self.fist_attack_active:
            return None
        max_combo = self.get_fist_combo_max()
        current_hit = self.swing_combo_index

        arc = 360 if self.fist_is_mega else self.get_fist_arc(current_hit)
        damage = self.get_fist_damage_for_hit(current_hit)
        attack_range = self.get_fist_range_for_hit(current_hit)
        knockback = self.get_fist_knockback_for_hit(current_hit)
        is_finisher = self.fist_is_mega or (current_hit == max_combo - 1)

        cleave = self.fist_dodge_cleave or self.swing_cleave
        if cleave:
            arc = 360
            attack_range += 24

        return {
            "x": self.x, "y": self.y, "cleave": cleave,
            "range": attack_range, "angle": self.facing_angle,
            "arc": math.radians(arc / 2), "damage": damage,
            "knockback": knockback, "combo_index": current_hit,
            "is_finisher": is_finisher, "is_mega": self.fist_is_mega,
            "hand": self.fist_which_hand,
        }

    # ── Контратака ──
    def trigger_counter_attack(self):
        if self.stats["fist_counter_attack"] <= 0:
            return
        self.counter_attack_active = True
        self.counter_attack_timer = self.counter_attack_duration
        self.counter_attack_hit_enemies = []
        self.counter_invincible_timer = COUNTER_ATTACK_INVINCIBILITY

    def get_counter_attack_area(self):
        if not self.counter_attack_active:
            return None
        return {"x": self.x, "y": self.y,
                "range": self.get_fist_range() * COUNTER_ATTACK_RANGE_MULTIPLIER,
                "damage": self.get_fist_damage() * COUNTER_ATTACK_DAMAGE_MULTIPLIER * (self.stats["fist_counter_attack"] / 100)}

    # ── Комбо ──
    def add_combo(self):
        self.combo_count += 1
        # A kill refreshes the ordinary window, but never cuts bomb time short.
        base_window = COMBO_TIMEOUT + self.stats["combo_grace"]
        if self.combo_timer <= base_window:
            self.combo_window = self.combo_timer = base_window
        if self.combo_count > self.combo_max_reached:
            self.combo_max_reached = self.combo_count

    def extend_active_combo(self, seconds):
        if self.combo_count > 0:
            self.combo_timer += seconds
            self.combo_window = self.combo_timer
            return True
        return False

    # ── Урон ──
    def take_damage(self, damage):
        # The cinematic cast is a committed, protected animation window; hits
        # are ignored outright so shields/thorns/status effects are untouched.
        if self.ult_cast_timer > 0:
            return 0
        if self.is_invincible():
            return 0
        if rng_module.random() * 100 < self.stats["block_chance"]:
            return 0

        # Удар прошёл: вампиризм не работает всё время неуязвимости + 0.3с
        self.lifesteal_block_timer = (PLAYER_INVINCIBILITY_AFTER_HIT
                                      + self.stats["hit_grace"] + 0.3)

        # Адреналин при получении урона
        if self.stats.get("adrenaline", 0) > 0:
            self.adrenaline_timer = 3.0

        # Сброс таймера регена щита
        self.shield_regen_timer = 0.0

        # Энерго-щит гасит урон первей HP
        self.shield_absorbed = False
        if self.shield_hp > 0:
            self.shield_absorbed = True
            if damage <= self.shield_hp:
                self.shield_hp -= damage
                # Ядовитые шипы + обычные шипы
                return self.stats["thorns"] + self.stats.get("poison_thorns", 0) * 8
            else:
                damage -= self.shield_hp
                self.shield_hp = 0

        actual_damage = max(1, damage - self.get_armor())
        self.hp -= actual_damage
        self.invincible_timer = PLAYER_INVINCIBILITY_AFTER_HIT + self.stats["hit_grace"]
        self.flash_timer = self.invincible_timer
        # Ядовитые шипы наносят 8 урона за уровень + обычные шипы
        thorns_damage = self.stats["thorns"] + self.stats.get("poison_thorns", 0) * 8
        self.trigger_counter_attack()
        if self.hp <= 0:
            self.hp = 0
        return thorns_damage

    def heal(self, amount):
        self.hp = min(self.hp + amount * self.get_heal_effectiveness(), self.max_hp)

    def lifesteal(self, damage_dealt):
        ls = self.get_fist_lifesteal()
        if ls > 0 and self.lifesteal_block_timer <= 0:
            heal_amount = damage_dealt * ls / 100
            self.hp = min(self.hp + heal_amount, self.max_hp)
            return heal_amount
        return 0

    def is_alive(self):
        return self.hp > 0

    # ── XP ──
    def gain_xp(self, amount):
        combo_bonus = 1.0 + self.get_combo_xp_bonus() / 100
        amount = int(amount * self.get_xp_multiplier() * combo_bonus)
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.pending_levels += 1
            self.xp_to_next = int(XP_BASE_TO_LEVEL * (XP_GROWTH ** (self.level - 1)))
            self.level_up_rings.append((0, LEVEL_UP_RING_LIFETIME, LEVEL_UP_RING_LIFETIME))

    def try_reset_slide_cooldown(self):
        chance = self.stats["slide_kill_reset_chance"]
        if chance > 0 and rng_module.random() * 100 < chance:
            self.slide_charges = min(self.slide_charges + 1, self.slide_max_charges)
            return True
        return False

    # ================================================================
    # ОТРИСОВКА
    # ================================================================
    def draw(self, screen, camera):
        sx, sy = camera.apply(self.x, self.y)
        sx, sy = int(sx), int(sy)

        # Ultimate wind-up: orbiting sigils and a pulsing field telegraph that
        # grows brighter as the cast approaches its release.
        if self.ult_cast_timer > 0 and self.ult_cast_duration > 0:
            progress = 1.0 - self.ult_cast_timer / self.ult_cast_duration
            pulse = .5 + .5 * math.sin(self.body_anim_timer * 24)
            radius = self.size + 12 + int(progress * 24)
            alpha = int(55 + 90 * progress + 35 * pulse)
            aura = pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA)
            pygame.draw.circle(aura, (*self.color, min(200, alpha//2)),
                               (radius+2, radius+2), radius)
            pygame.draw.circle(aura, (*self.color, min(255, alpha)),
                               (radius+2, radius+2), radius, 2)
            screen.blit(aura, (sx-radius-2, sy-radius-2))
            for i in range(3):
                angle = -self.body_anim_timer * (2.5+i*.35) + i*math.tau/3
                orbit = radius + 7 + i*3
                point = (sx+int(math.cos(angle)*orbit), sy+int(math.sin(angle)*orbit))
                pygame.draw.circle(screen, WHITE, point, 2+i%2)

        # Level-up кольца
        for ring_r, ring_lt, ring_mlt in self.level_up_rings:
            a = ring_lt / ring_mlt
            r = int(ring_r)
            if r > 0:
                cv = int(255 * a)
                pygame.draw.circle(screen, (cv, cv, min(255, cv // 2 + 128)), (sx, sy), r, max(1, int(4 * a)))

        # Shockwaves
        for wx, wy, wr, wmr, wd in self.shockwaves:
            wsx, wsy = camera.apply(wx, wy)
            a = 1.0 - wr / wmr
            ri = int(wr)
            if ri > 0:
                cv = int(200 * a)
                pygame.draw.circle(screen, (cv, cv // 2, cv), (int(wsx), int(wsy)), ri, max(1, int(3 * a)))

        # Electric trails
        for tx, ty, tt in self.electric_trails:
            tsx, tsy = camera.apply(tx, ty)
            a = tt / ELECTRIC_TRAIL_DURATION
            r = int(ELECTRIC_TRAIL_RADIUS * a)
            if r > 0:
                es = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(es, (50, 100, int(150 * a), int(40 * a)), (r, r), r)
                pygame.draw.circle(es, (100, 200, 255, int(80 * a)), (r, r), r, 1)
                screen.blit(es, (int(tsx) - r, int(tsy) - r))

        # Fist waves
        for wave in self.fist_waves:
            wave.draw(screen, camera)

        # Мигание
        if self.flash_timer > 0 and int(self.flash_timer * 10) % 2 == 0:
            color = WHITE
        else:
            color = self.color

        # Ярость
        if self.rage_intensity > 0:
            rage_r = self.size + 12 + int(self.rage_intensity * 10)
            rs = pygame.Surface((rage_r * 2, rage_r * 2), pygame.SRCALPHA)
            ra = int(50 * self.rage_intensity * abs(math.sin(self.body_anim_timer * 5)))
            pygame.draw.circle(rs, (255, 30, 0, ra), (rage_r, rage_r), rage_r)
            screen.blit(rs, (sx - rage_r, sy - rage_r))
            rb = self.rage_intensity * 0.6
            color = (min(255, int(color[0] * (1 - rb) + 255 * rb)),
                     int(color[1] * (1 - rb) + 30 * rb),
                     int(color[2] * (1 - rb)))

        # След скольжения
        if self.is_sliding:
            tc = (color[0] // 3, color[1] // 3, color[2] // 3)
            for i in range(4):
                o = (i + 1) * 7
                pygame.draw.circle(screen, tc,
                    (int(sx - self.slide_direction_x * o),
                     int(sy - self.slide_direction_y * o)),
                    max(2, self.size - i * 3))

        # Неуязвимость скольжения
        if self.is_slide_knockback_active():
            pygame.draw.circle(screen, (100, 200, 255), (sx, sy), self.size + 8, 2)

        # Контратака
        if self.counter_attack_active:
            cr = int(self.get_fist_range() * COUNTER_ATTACK_RANGE_MULTIPLIER)
            pygame.draw.circle(screen, RED, (sx, sy), cr, 3)

        # Тень
        if getattr(camera, 'entity_shadows', True):
            if getattr(self, '_shadow_size', None) != self.size:
                self._shadow_size = self.size
                self._shadow_sprite = pygame.Surface((self.size*2+4, 8), pygame.SRCALPHA)
                pygame.draw.ellipse(self._shadow_sprite, (0, 0, 0, 60), self._shadow_sprite.get_rect())
            screen.blit(self._shadow_sprite, (sx-self.size-2, sy+self.size-2))

        # Тело
        pygame.draw.circle(screen, color, (sx, sy), self.size)
        pygame.draw.circle(screen, (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60)),
                          (sx - self.size // 3, sy - self.size // 3), self.size // 3)
        pygame.draw.circle(screen, WHITE, (sx, sy), self.size, 2)

        # Руки
        arm_swing = math.sin(self.body_anim_timer * 8) * 10 if self.current_speed > 10 else 0
        for i, arm_angle in enumerate([
            self.facing_angle + math.pi / 2 + math.radians(arm_swing),
            self.facing_angle - math.pi / 2 - math.radians(arm_swing)
        ]):
            ax = sx + int(math.cos(arm_angle) * (self.size + 4) * 0.7)
            ay = sy + int(math.sin(arm_angle) * (self.size + 4) * 0.7)
            arm_len = 8
            aex = ax + int(math.cos(self.facing_angle) * arm_len)
            aey = ay + int(math.sin(self.facing_angle) * arm_len)

            # Distinct equipment is cosmetic; combat reach and damage stay unchanged.
            ac = {'slider': (85, 225, 235), 'brawler': (230, 83, 70),
                  'spark': (255, 210, 67), 'shadow': (190, 142, 244)}[self.hero_id]
            if self.fist_attack_active:
                if self.fist_which_hand == 2 or self.fist_which_hand == i:
                    ac = ORANGE if self.fist_is_mega else YELLOW
                    extend = 14 if self.fist_is_mega else 10
                    aex = ax + int(math.cos(self.facing_angle) * (arm_len + extend))
                    aey = ay + int(math.sin(self.facing_angle) * (arm_len + extend))
            if self.dodge_charge or (self.fist_attack_active and self.fist_dodge_cleave):
                pygame.draw.circle(screen, CYAN, (aex, aey), 8, 2)
                ac = WHITE
            pygame.draw.line(screen, ac, (ax, ay), (aex, aey), 4)
            if self.hero_id in ('shadow', 'spark'):
                # Shadow carries paired blades; Spark has electric batons.
                length = 16 if self.hero_id == 'shadow' else 12
                dx, dy = math.cos(self.facing_angle), math.sin(self.facing_angle)
                tip = (int(aex + dx * length), int(aey + dy * length))
                pygame.draw.line(screen, (36, 28, 50), (aex, aey), tip, 6)
                pygame.draw.line(screen, ac, (aex, aey), tip, 4)
                pygame.draw.line(screen, WHITE, (aex, aey), tip, 1)
            else:
                radius = 6 if self.hero_id == 'brawler' else 4
                pygame.draw.circle(screen, ac, (aex, aey), radius)
                pygame.draw.circle(screen, WHITE, (aex, aey), radius, 1)

        # Глаза
        for side in [-1, 1]:
            perp = self.facing_angle + side * 0.4
            ex = sx + int(math.cos(perp) * self.size * 0.4)
            ey = sy + int(math.sin(perp) * self.size * 0.4)
            pygame.draw.circle(screen, WHITE, (ex, ey), 4)
            pc = RED if self.rage_intensity > 0.5 else BLACK
            pygame.draw.circle(screen, pc,
                (ex + int(math.cos(self.facing_angle) * 2),
                 ey + int(math.sin(self.facing_angle) * 2)), 2)

        # Удар визуал
        if self.fist_attack_active:
            attack = self.get_fist_attack_area()
            if attack:
                fr = int(attack["range"])
                if attack["cleave"]:
                    pygame.draw.circle(screen, CYAN, (sx, sy), fr, 3)
                    pygame.draw.circle(screen, WHITE, (sx, sy), fr - 4, 1)
                elif attack.get("is_mega"):
                    # МЕГА удар — большое кольцо + звёзды
                    pygame.draw.circle(screen, ORANGE, (sx, sy), fr, 4)
                    pygame.draw.circle(screen, YELLOW, (sx, sy), fr - 5, 2)
                    for j in range(8):
                        a = self.body_anim_timer * 8 + j * math.pi / 4
                        pygame.draw.circle(screen, WHITE,
                            (sx + int(math.cos(a) * (fr - 3)),
                             sy + int(math.sin(a) * (fr - 3))), 4)
                elif attack["is_finisher"]:
                    pygame.draw.circle(screen, ORANGE, (sx, sy), fr, 2)
                    for j in range(6):
                        a = self.body_anim_timer * 5 + j * math.pi / 3
                        pygame.draw.circle(screen, YELLOW,
                            (sx + int(math.cos(a) * (fr - 5)),
                             sy + int(math.sin(a) * (fr - 5))), 3)
                else:
                    fx = sx + int(math.cos(self.facing_angle) * (self.size + 14))
                    fy = sy + int(math.sin(self.facing_angle) * (self.size + 14))
                    pygame.draw.circle(screen, YELLOW, (fx, fy), 8)
                    pygame.draw.circle(screen, ORANGE, (fx, fy), 8, 2)
                    for j in range(3):
                        la = self.facing_angle + math.radians(-20 + j * 20)
                        pygame.draw.line(screen, YELLOW, (fx, fy),
                            (fx + int(math.cos(la) * 12), fy + int(math.sin(la) * 12)), 2)

        # Серия точки
        if self.fist_combo_timer > 0:
            mc = self.get_fist_combo_max()
            ci = self.fist_combo_index
            for i in range(mc):
                dx = sx - (mc - 1) * 5 + i * 10
                dy2 = sy - self.size - 12
                pygame.draw.circle(screen, YELLOW if i < ci else DARK_GRAY, (dx, dy2), 3)

        # Мега счётчик
        mega_progress = self.fist_total_hits % FIST_MEGA_HIT_EVERY
        if mega_progress > 0:
            bar_w = 30
            bar_h = 3
            bx = sx - bar_w // 2
            by = sy - self.size - 18
            ratio = mega_progress / FIST_MEGA_HIT_EVERY
            pygame.draw.rect(screen, DARK_GRAY, (bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, ORANGE, (bx, by, int(bar_w * ratio), bar_h))

        # ── Орбитальные клинки ──
        blade_count = int(self.stats.get("orbital_blade_count", 0))
        if blade_count > 0:
            orbit_r = self.size + 28
            for i in range(blade_count):
                blade_angle = self.orbital_blades_angle + (i * math.pi * 2 / blade_count)
                bx2 = sx + int(math.cos(blade_angle) * orbit_r)
                by2 = sy + int(math.sin(blade_angle) * orbit_r)
                # Клинок — ромб
                blade_pts = [
                    (bx2 + int(math.cos(blade_angle) * 10), by2 + int(math.sin(blade_angle) * 10)),
                    (bx2 + int(math.cos(blade_angle + 1.5) * 5), by2 + int(math.sin(blade_angle + 1.5) * 5)),
                    (bx2 + int(math.cos(blade_angle + math.pi) * 4), by2 + int(math.sin(blade_angle + math.pi) * 4)),
                    (bx2 + int(math.cos(blade_angle - 1.5) * 5), by2 + int(math.sin(blade_angle - 1.5) * 5)),
                ]
                pygame.draw.polygon(screen, CYAN, blade_pts)
                pygame.draw.polygon(screen, WHITE, blade_pts, 1)

        # ── Щит (полоска под HP) ──
        shield_max = self.stats.get("shield_max", 0)
        if shield_max > 0 and self.shield_hp > 0:
            shield_r = self.size + 4
            shield_ratio = self.shield_hp / shield_max
            shield_arc = shield_ratio * math.pi * 2
            # Рисуем дугу щита
            for angle_step in range(int(shield_arc * 20)):
                a = -math.pi / 2 + angle_step / 20.0
                px2 = sx + int(math.cos(a) * shield_r)
                py2 = sy + int(math.sin(a) * shield_r)
                pygame.draw.circle(screen, (50, 150, 255), (px2, py2), 2)

        # ── Адреналин свечение ──
        if self.adrenaline_active:
            adr_r = self.size + 10
            adr_pulse = abs(math.sin(self.body_anim_timer * 8))
            adr_s = pygame.Surface((adr_r * 2, adr_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(adr_s, (255, 150, 0, int(40 * adr_pulse)), (adr_r, adr_r), adr_r)
            screen.blit(adr_s, (sx - adr_r, sy - adr_r))

        # ── Гигантский рост обводка ──
        if self.giant_growth_active:
            pygame.draw.circle(screen, BROWN, (sx, sy), self.size + 2, 3)

        # ── Time Warp аура ──
        if self.time_warp_active:
            tw_r = 120 + self.stats.get("time_warp", 0) * 30
            tw_s = pygame.Surface((tw_r * 2, tw_r * 2), pygame.SRCALPHA)
            tw_alpha = int(20 + 10 * abs(math.sin(self.body_anim_timer * 2)))
            pygame.draw.circle(tw_s, (30, 60, 150, tw_alpha), (tw_r, tw_r), tw_r)
            pygame.draw.circle(tw_s, (50, 100, 200, tw_alpha + 10), (tw_r, tw_r), tw_r, 1)
            screen.blit(tw_s, (sx - tw_r, sy - tw_r))

    def gain_ult_charge(self, amount):
        # Ultimates now require twice as many kills/charge upgrades to refill.
        # Cast lock and the post-cast cooldown are hard gates: charge cannot
        # trickle in while the cooldown is visible.
        if self.ult_cooldown_timer > 0 or self.ult_cast_timer > 0:
            return
        self.ult_charge = min(100.0, self.ult_charge + amount * 0.5)

    def can_use_ult(self):
        return (self.ult_charge >= 100.0 and self.ult_cooldown_timer <= 0
                and self.ult_cast_timer <= 0)

    def resolve_hero_ult(self, hero_id, camera, particle_manager):
        """Apply the caster-specific buffs/impact VFX after its wind-up."""
        if hero_id == "slider":
            # The dash chain handles its own post-ult slide cooldown and speed buff.
            self.invincible_timer = 3.4
            camera.add_shake(15, .55)
            particle_manager.spawn_bomb_particles(self.x, self.y, count=90)
        elif hero_id == "brawler":
            camera.add_shake(24, .8)
            particle_manager.spawn_bomb_particles(self.x, self.y, count=120)
        elif hero_id == "spark":
            camera.add_shake(16, .6)
            particle_manager.spawn_level_up_particles(self.x, self.y, count=100)
        elif hero_id == "shadow":
            camera.add_shake(13, .45)
            self.invincible_timer = 2.5
            self.heal(self.max_hp * .35)
            particle_manager.spawn_death_particles(self.x, self.y, PURPLE, count=70)
        return True