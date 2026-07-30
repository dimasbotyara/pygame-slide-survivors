# main.py — v4 — Полная версия без сокращений
# Мега-кулаки, волны, XP pull, ground slam pull, электрослед, все системы

import pygame
import sys
import math
import random
from settings import *
from camera import Camera
from player import Player
from enemies import Enemy, Boss, EnemyProjectile, EnemySpawner
from upgrades import UpgradeManager
from particles import ParticleManager, Particle
from items import XPOrb, DroppedItem, roll_drop
from world import World
from ui import UI
from highscores import add_highscore
from settings_manager import SettingsManager
from translations import t
from heroes import HEROES, HERO_KEYS
from achievements import AchievementManager



class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Менеджер настроек и достижений
        self.settings_manager = SettingsManager()
        self.achievement_manager = AchievementManager()

        # UI
        self.ui = UI()

        # Состояние игры
        if self.settings_manager.get("first_launch", True):
            self.state = "language_select"
        else:
            self.state = "menu"

        self.selected_hero_index = 0
        self.lang_selection = 0
        self.menu_selection = 0
        self.settings_selection = 0
        self.settings_previous_state = "menu"
        self.pause_selection = 0
        self.game_over_selection = 0
        self.new_record_pos = -1

        # Игровые объекты
        self.player = None
        self.camera = None
        self.world = None
        self.enemies = []
        self.enemy_projectiles = []
        self.xp_orbs = []
        self.dropped_items = []
        self.spawner = None
        self.upgrade_manager = None
        self.particle_manager = None
        self.game_time = 0.0
        self.game_messages = []

        # Боссы
        self.active_bosses = []

        # Корпусы для некроманта
        self.corpse_positions = []
        self.max_corpses = 50

        # Следы скольжения
        self.slide_trail_timer = 0.0

        # Трекинг ground slam (один раз за удар)
        self.ground_slam_done_this_attack = False
        self.last_fist_attack_id = 0

    # ================================================================
    # ГЛАВНЫЙ ЦИКЛ
    # ================================================================
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # защита от скачков

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    break

            if not self.running:
                break

            if self.state == "language_select":
                self.update_language_select(events)
                self.draw_language_select()
            elif self.state == "hero_select":
                self.update_hero_select(events)
                self.draw_hero_select()
            elif self.state == "achievements":
                self.update_achievements(events)
                self.draw_achievements()
            elif self.state == "menu":
                self.update_menu(events)
                self.draw_menu()
            elif self.state == "settings":
                self.update_settings(events)
                self.draw_settings()
            elif self.state == "controls":
                self.update_controls(events)
                self.draw_controls()
            elif self.state == "highscores":
                self.update_highscores(events)
                self.draw_highscores()
            elif self.state == "playing":
                self.update_playing(dt, events)
                self.draw_playing()
            elif self.state == "paused":
                self.update_paused(events)
                self.draw_paused()
            elif self.state == "upgrading":
                self.update_upgrading(events)
                self.draw_upgrading()
            elif self.state == "game_over":
                self.update_game_over(events)
                self.draw_game_over()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ================================================================
    # ИНИЦИАЛИЗАЦИЯ НОВОЙ ИГРЫ
    # ================================================================
    def start_new_game(self):
        """Начать новую игру — сбросить все объекты"""
        hero_id = HERO_KEYS[self.selected_hero_index]
        self.player = Player(0, 0, hero_id=hero_id)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera.shake_enabled = self.settings_manager.get("screen_shake", True)
        self.world = World()
        self.enemies = []
        self.enemy_projectiles = []
        self.xp_orbs = []
        self.dropped_items = []
        self.spawner = EnemySpawner()
        self.upgrade_manager = UpgradeManager()
        self.particle_manager = ParticleManager()
        self.particle_manager.damage_numbers_enabled = self.settings_manager.get("damage_numbers", True)
        self.game_time = 0.0
        self.game_messages = []
        self.active_bosses = []
        self.corpse_positions = []
        self.slide_trail_timer = 0.0
        self.new_record_pos = -1
        self.ground_slam_done_this_attack = False
        self.last_fist_attack_id = 0
        self.state = "playing"

    # ================================================================
    # ВЫБОР ЯЗЫКА ПРИ ПЕРВОМ ЗАПУСКЕ
    # ================================================================
    def update_language_select(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.lang_selection = (self.lang_selection - 1) % 2
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.lang_selection = (self.lang_selection + 1) % 2
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    lang = "ru" if self.lang_selection == 0 else "en"
                    self.settings_manager.set("language", lang)
                    self.settings_manager.set("first_launch", False)
                    self.state = "menu"
                    self.menu_selection = 0

    def draw_language_select(self):
        self.ui.draw_language_select_screen(self.screen, self.lang_selection)

    # ================================================================
    # ВЫБОР ПЕРСОНАЖА
    # ================================================================
    def update_hero_select(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected_hero_index = (self.selected_hero_index - 1) % len(HERO_KEYS)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected_hero_index = (self.selected_hero_index + 1) % len(HERO_KEYS)
                elif event.key == pygame.K_RETURN:
                    self.start_new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def draw_hero_select(self):
        self.ui.draw_hero_select_screen(self.screen, self.selected_hero_index)

    # ================================================================
    # ДОСТИЖЕНИЯ
    # ================================================================
    def update_achievements(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def draw_achievements(self):
        self.ui.draw_achievements_screen(self.screen, self.achievement_manager)

    # ================================================================
    # ГЛАВНОЕ МЕНЮ
    # ================================================================
    def update_menu(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.menu_selection = (self.menu_selection - 1) % 7
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_selection = (self.menu_selection + 1) % 7
                elif event.key == pygame.K_RETURN:
                    if self.menu_selection == 0:
                        self.start_new_game()
                    elif self.menu_selection == 1:
                        self.state = "hero_select"
                    elif self.menu_selection == 2:
                        self.state = "achievements"
                    elif self.menu_selection == 3:
                        self.settings_previous_state = "menu"
                        self.settings_selection = 0
                        self.state = "settings"
                    elif self.menu_selection == 4:
                        self.state = "controls"
                    elif self.menu_selection == 5:
                        self.state = "highscores"
                    elif self.menu_selection == 6:
                        self.running = False

    def draw_menu(self):
        self.ui.draw_main_menu(self.screen, self.menu_selection, self.selected_hero_index)

    # ================================================================
    # ЭКРАН НАСТРОЕК
    # ================================================================
    def update_settings(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.settings_manager.save()
                    self.state = getattr(self, "settings_previous_state", "menu")
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.settings_selection = (self.settings_selection - 1) % 5
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.settings_selection = (self.settings_selection + 1) % 5
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_a, pygame.K_d, pygame.K_SPACE):
                    if self.settings_selection == 0:
                        cur_lang = self.settings_manager.get("language", "ru")
                        new_lang = "en" if cur_lang == "ru" else "ru"
                        self.settings_manager.set("language", new_lang)
                    elif self.settings_selection == 1:
                        cur = self.settings_manager.get("screen_shake", True)
                        self.settings_manager.set("screen_shake", not cur)
                        if self.camera:
                            self.camera.shake_enabled = not cur
                    elif self.settings_selection == 2:
                        cur = self.settings_manager.get("damage_numbers", True)
                        self.settings_manager.set("damage_numbers", not cur)
                        if self.particle_manager:
                            self.particle_manager.damage_numbers_enabled = not cur
                    elif self.settings_selection == 3:
                        cur = self.settings_manager.get("minimap", True)
                        self.settings_manager.set("minimap", not cur)
                    elif self.settings_selection == 4:
                        self.settings_manager.save()
                        self.state = getattr(self, "settings_previous_state", "menu")

    def draw_settings(self):
        self.ui.draw_settings_screen(self.screen, self.settings_selection, self.settings_manager)

    # ================================================================
    # ЭКРАН УПРАВЛЕНИЯ
    # ================================================================
    def update_controls(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = getattr(self, "settings_previous_state", "menu")

    def draw_controls(self):
        self.ui.draw_controls_screen(self.screen)

    # ================================================================
    # РЕКОРДЫ
    # ================================================================
    def update_highscores(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def draw_highscores(self):
        self.ui.draw_highscores_screen(self.screen)

    # ================================================================
    # ПАУЗА
    # ================================================================
    def update_paused(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.state = "playing"
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.pause_selection = (self.pause_selection - 1) % 3
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_selection = (self.pause_selection + 1) % 3
                elif event.key == pygame.K_RETURN:
                    if self.pause_selection == 0:
                        self.state = "playing"
                    elif self.pause_selection == 1:
                        self.settings_previous_state = "paused"
                        self.settings_selection = 0
                        self.state = "settings"
                    elif self.pause_selection == 2:
                        self.state = "menu"
                        self.menu_selection = 0

    def draw_paused(self):
        self.draw_playing()
        self.ui.draw_pause(self.screen, self.pause_selection)

    # ================================================================
    # GAME OVER
    # ================================================================
    def update_game_over(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.game_over_selection = (self.game_over_selection - 1) % 2
                elif event.key == pygame.K_DOWN:
                    self.game_over_selection = (self.game_over_selection + 1) % 2
                elif event.key == pygame.K_RETURN:
                    if self.game_over_selection == 0:
                        self.start_new_game()
                    elif self.game_over_selection == 1:
                        self.state = "menu"
                        self.menu_selection = 0

    def draw_game_over(self):
        self.draw_playing()
        self.ui.draw_game_over(
            self.screen, self.player, self.game_time,
            self.game_over_selection, self.new_record_pos
        )

    # ================================================================
    # ЭКРАН ВЫБОРА УЛУЧШЕНИЙ
    # ================================================================
    def update_upgrading(self, events):
        um = self.upgrade_manager
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    um.selected_index = (um.selected_index - 1) % len(um.choices)
                elif event.key == pygame.K_RIGHT:
                    um.selected_index = (um.selected_index + 1) % len(um.choices)
                elif event.key == pygame.K_RETURN:
                    self._apply_upgrade_choice(um.selected_index)
                elif event.key == pygame.K_1 and len(um.choices) >= 1:
                    self._apply_upgrade_choice(0)
                elif event.key == pygame.K_2 and len(um.choices) >= 2:
                    self._apply_upgrade_choice(1)
                elif event.key == pygame.K_3 and len(um.choices) >= 3:
                    self._apply_upgrade_choice(2)

    def _apply_upgrade_choice(self, index):
        """Применить выбранное улучшение"""
        um = self.upgrade_manager
        upgrade = um.select_upgrade(index, self.player)
        if upgrade:
            self.particle_manager.add_message(t("MSG_UPGRADE_OBTAINED", upgrade.name), CYAN)
            self.check_pending_levels()

    def check_pending_levels(self):
        """Проверить, есть ли ещё уровни для выбора"""
        if self.player.pending_levels > 0:
            self.player.pending_levels -= 1
            luck = self.player.stats["luck"]
            hero_id = getattr(self.player, 'hero_id', 'slider')
            self.upgrade_manager.generate_choices(CHOICES_PER_LEVEL, luck, hero_id=hero_id)
        else:
            self.state = "playing"

    def draw_upgrading(self):
        self.draw_playing()
        self.ui.draw_upgrade_screen(
            self.screen,
            self.upgrade_manager.choices,
            self.upgrade_manager.selected_index,
            self.player
        )

    # ================================================================
    # ОСНОВНОЙ ИГРОВОЙ ПРОЦЕСС
    # ================================================================
    def update_playing(self, dt, events):
        """Обновление всей игровой логики"""

        # Проверка паузы, ультимейта и dash-атаки из событий
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.state = "paused"
                    self.pause_selection = 0
                    return
                elif event.key == pygame.K_q:
                    self.trigger_hero_ult()
            # Dash-атака по ЛКМ, ульт по ПКМ
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.player.try_dash_attack():
                        self.camera.add_shake(SHAKE_BOSS_HIT)
                        self.particle_manager.add_message(t("MSG_DASH"), ORANGE)
                elif event.button == 3:
                    self.trigger_hero_ult()

        self.game_time += dt

        # Ввод
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Обновить игрока
        self.player.update(dt, keys, mouse_pos, self.camera)

        # Ограничить игрока ареной босса
        self.enforce_boss_arena()

        # Обновить камеру (с look-ahead по направлению движения)
        self.camera.update(self.player.x, self.player.y, dt,
                          target_vx=self.player.velocity_x,
                          target_vy=self.player.velocity_y)

        # Следы скольжения на земле
        if self.player.is_sliding and self.player.slide_current_speed > 50:
            self.slide_trail_timer += dt
            if self.slide_trail_timer >= 0.03:
                self.slide_trail_timer = 0
                speed_ratio = min(1.0, self.player.slide_current_speed / self.player.get_slide_initial_speed())
                self.world.add_slide_trail(
                    self.player.x, self.player.y,
                    self.player.slide_angle, speed_ratio
                )
                # Частицы скольжения
                self.particle_manager.spawn_slide_particles(
                    self.player.x, self.player.y,
                    self.player.slide_direction_x,
                    self.player.slide_direction_y
                )

        # Обновить мир (следы, декорации)
        self.world.update(dt)

        # Спавн врагов
        self.game_messages.clear()
        self.spawner.update(dt, self.player.x, self.player.y,
                           self.enemies, self.game_messages)

        # Передать сообщения от спавнера
        for msg in self.game_messages:
            color = RED if "БОСС" in msg else YELLOW
            self.particle_manager.add_message(msg, color)
            if "БОСС" in msg:
                self.camera.add_shake(SHAKE_BOSS_SPAWN)

        # Обновить список живых боссов
        self.active_bosses = [
            e for e in self.enemies
            if getattr(e, 'is_boss', False) and e.alive
        ]

        # Обновить врагов
        self.update_enemies(dt)

        # Обновить снаряды врагов
        self.update_enemy_projectiles(dt)

        # Некроманты — воскрешение
        self.update_necromancers()

        # ════════════════════════════════════════════
        # ВСЕ ПРОВЕРКИ СТОЛКНОВЕНИЙ
        # ════════════════════════════════════════════
        self.check_fist_attacks()
        self.check_fist_waves()
        self.check_ground_slam()
        self.check_dash_attack()
        self.check_slide_knockback()
        self.check_counter_attack()
        self.check_enemy_contact_damage()
        self.check_shockwave_damage()
        self.check_electric_trail_damage(dt)

        # XP притягивание от кулаков
        self.check_fist_xp_pull()

        # Обновить XP сферы
        self.update_xp_orbs(dt)

        # Обновить предметы на земле
        self.update_items(dt)

        # Ауры
        self.apply_aura_damage(dt)
        self.apply_aura_slow(dt)

        # Деспавн далёких объектов
        self.despawn_far_enemies()

        # Очистка старых корпусов
        self.cleanup_corpses()

        # Обновить частицы
        self.particle_manager.update(dt)

        # Проверить повышение уровня
        if self.player.pending_levels > 0:
            self.player.pending_levels -= 1
            luck = self.player.stats["luck"]
            hero_id = getattr(self.player, 'hero_id', 'slider')
            self.upgrade_manager.generate_choices(CHOICES_PER_LEVEL, luck, hero_id=hero_id)
            self.state = "upgrading"
            self.particle_manager.spawn_level_up_particles(
                self.player.x, self.player.y
            )
            self.particle_manager.add_message(t("MSG_LEVEL_UP", self.player.level), YELLOW)

        # Проверить достижения
        if self.player.enemies_killed >= 1:
            self.achievement_manager.unlock("first_kill", self.particle_manager)
        if self.player.enemies_killed >= 500:
            self.achievement_manager.unlock("kills_500", self.particle_manager)
        if self.player.total_slides_count >= 50:
            self.achievement_manager.unlock("slide_master", self.particle_manager)
        if self.player.combo_count >= 50:
            self.achievement_manager.unlock("combo_50", self.particle_manager)
        if self.player.level >= 20:
            self.achievement_manager.unlock("level_20", self.particle_manager)
        if self.game_time >= 300:
            self.achievement_manager.unlock("survive_5min", self.particle_manager)

        # Проверить смерть игрока
        if not self.player.is_alive():
            self.new_record_pos = add_highscore(
                self.game_time, self.player.level, self.player.enemies_killed
            )
            self.state = "game_over"
            self.game_over_selection = 0

    def trigger_hero_ult(self):
        """Активация ультимативной способности текущего героя"""
        if self.player.trigger_hero_ult(self.player.hero_id, self.enemies, self.camera, self.particle_manager):
            self.achievement_manager.unlock("ult_used", self.particle_manager)

    # ================================================================
    # БОСС-АРЕНА
    # ================================================================
    def enforce_boss_arena(self):
        """Не дать игроку и врагам выйти за пределы арены босса"""
        for boss in self.active_bosses:
            if not getattr(boss, 'arena_active', False) or not boss.alive:
                continue

            # ── Ограничить игрока ──
            dx = self.player.x - boss.arena_center_x
            dy = self.player.y - boss.arena_center_y
            dist = math.sqrt(dx * dx + dy * dy)
            limit = BOSS_ARENA_RADIUS - self.player.size

            if dist > limit and dist > 0:
                nx = dx / dist
                ny = dy / dist
                self.player.x = boss.arena_center_x + nx * limit
                self.player.y = boss.arena_center_y + ny * limit

                # Отразить скольжение при столкновении со стеной
                if self.player.is_sliding:
                    dot = self.player.velocity_x * nx + self.player.velocity_y * ny
                    self.player.velocity_x -= 2 * dot * nx
                    self.player.velocity_y -= 2 * dot * ny
                    self.player.slide_direction_x = -nx
                    self.player.slide_direction_y = -ny
                    self.player.slide_angle = math.atan2(-ny, -nx)

            # ── Ограничить врагов ──
            for enemy in self.enemies:
                if enemy is boss or not enemy.alive:
                    continue

                edx = enemy.x - boss.arena_center_x
                edy = enemy.y - boss.arena_center_y
                edist = math.sqrt(edx * edx + edy * edy)
                elimit = BOSS_ARENA_RADIUS - enemy.size

                if edist > elimit and edist > 0:
                    enx = edx / edist
                    eny = edy / edist
                    enemy.x = boss.arena_center_x + enx * elimit
                    enemy.y = boss.arena_center_y + eny * elimit

    # ================================================================
    # ОБНОВЛЕНИЕ ВРАГОВ
    # ================================================================
    def update_enemies(self, dt):
        """Обновить всех врагов"""
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            # Стан — враг не двигается и не атакует
            if getattr(enemy, 'stun_timer', 0) > 0:
                enemy.stun_timer -= dt
                enemy.velocity_x = 0
                enemy.velocity_y = 0
                # Визуал мигания при стане
                if int(enemy.stun_timer * 8) % 2 == 0:
                    enemy.flash_timer = 0.05
                continue

            enemy.update(dt, self.player.x, self.player.y, self.enemies)

            # Стрельба (для стрелков)
            if getattr(enemy, 'shoot_range', 0) > 0:
                if enemy.should_shoot(self.player.x, self.player.y):
                    self.spawn_enemy_projectile(enemy)

        # Удалить мёртвых
        self.enemies = [e for e in self.enemies if e.alive]

    def spawn_enemy_projectile(self, enemy):
        """Создать снаряд врага-стрелка"""
        dx = self.player.x - enemy.x
        dy = self.player.y - enemy.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
        else:
            dir_x, dir_y = 1, 0

        projectile = EnemyProjectile(
            enemy.x, enemy.y,
            dir_x, dir_y,
            enemy.shoot_speed,
            enemy.damage
        )
        self.enemy_projectiles.append(projectile)

    # ================================================================
    # НЕКРОМАНТЫ
    # ================================================================
    def update_necromancers(self):
        """Обработка воскрешения убитых врагов некромантами"""
        for enemy in self.enemies:
            if not enemy.alive or enemy.enemy_type != "necromancer":
                continue
            if not enemy.should_revive():
                continue

            # Найти ближайший корпус
            best_corpse = None
            best_dist = float('inf')

            for i, (cx, cy, ctype, ctime) in enumerate(self.corpse_positions):
                dx = cx - enemy.x
                dy = cy - enemy.y
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < enemy.revive_radius and dist < best_dist:
                    best_dist = dist
                    best_corpse = i

            if best_corpse is not None:
                cx, cy, ctype, ctime = self.corpse_positions.pop(best_corpse)

                # Воскресить с 50% HP
                revived = Enemy(cx, cy, ctype, self.spawner.difficulty_multiplier)
                revived.hp = revived.max_hp * 0.5
                self.enemies.append(revived)

                # Эффект
                self.particle_manager.spawn_death_particles(cx, cy, PURPLE, count=10)

    # ================================================================
    # СНАРЯДЫ ВРАГОВ
    # ================================================================
    def update_enemy_projectiles(self, dt):
        """Обновить снаряды врагов и проверить столкновение с игроком"""
        for proj in self.enemy_projectiles:
            proj.update(dt)

            if proj.alive:
                dx = self.player.x - proj.x
                dy = self.player.y - proj.y
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < self.player.size + proj.size:
                    thorns = self.player.take_damage(proj.damage)
                    proj.alive = False

                    if self.player.hp > 0:
                        self.particle_manager.spawn_hit_particles(
                            self.player.x, self.player.y, RED
                        )
                        self.particle_manager.add_damage_number(
                            self.player.x, self.player.y,
                            proj.damage, color=RED
                        )
                        self.camera.add_shake(SHAKE_PLAYER_HIT)

        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.alive]

    # ================================================================
    # УНИВЕРСАЛЬНАЯ ФУНКЦИЯ НАНЕСЕНИЯ УРОНА ВРАГУ
    # ================================================================
    def deal_damage_to_enemy(self, enemy, base_damage, from_angle=None,
                              knockback_force=0, knockback_dir_x=0, knockback_dir_y=0,
                              can_crit=True, can_stun=True, can_lifesteal=True,
                              particle_color=None, particle_count=5,
                              source="fist"):
        """
        Единая логика нанесения урона врагу.
        Обрабатывает: крит, стан, вампиризм, откид, частицы, убийство.
        Возвращает (killed, actual_damage, is_crit)
        """
        damage = base_damage
        is_crit = False

        # Крит
        if can_crit and random.random() * 100 < self.player.get_crit_chance():
            damage *= self.player.get_crit_multiplier()
            is_crit = True

        # Нанести урон
        killed = enemy.take_damage(damage, from_angle)
        self.player.damage_dealt += damage

        # Откидывание
        if knockback_force > 0:
            enemy.apply_knockback(
                knockback_dir_x * knockback_force,
                knockback_dir_y * knockback_force
            )

        # Стан (от кулаков)
        if can_stun and source == "fist":
            stun_chance = self.player.get_fist_stun_chance()
            if stun_chance > 0 and random.random() * 100 < stun_chance:
                if not hasattr(enemy, 'stun_timer'):
                    enemy.stun_timer = 0
                enemy.stun_timer = FIST_STUN_DURATION

                # Визуал стана — текст
                self.particle_manager.add_damage_number(
                    enemy.x, enemy.y - 15, 0, color=YELLOW
                )

                # Звёздочки стана
                for i in range(4):
                    angle = i * math.pi / 2
                    self.particle_manager.particles.append(
                        Particle(
                            enemy.x, enemy.y - 10,
                            math.cos(angle) * 40,
                            math.sin(angle) * 40 - 30,
                            YELLOW, 0.8, 3
                        )
                    )

        # Вампиризм (от кулаков)
        if can_lifesteal and source == "fist":
            healed = self.player.lifesteal(damage)
            if healed > 0.5:
                self.particle_manager.spawn_heal_particles(
                    self.player.x, self.player.y, count=3
                )

        # Частицы попадания
        p_color = particle_color or enemy.color
        self.particle_manager.spawn_hit_particles(
            enemy.x, enemy.y, p_color, count=particle_count
        )

        # Число урона
        self.particle_manager.add_damage_number(
            enemy.x, enemy.y, damage, is_crit
        )

        # Убийство
        if killed:
            self.on_enemy_killed(enemy)

        return killed, damage, is_crit

    # ================================================================
    # АТАКА КУЛАКАМИ
    # ================================================================
    def check_fist_attacks(self):
        """Проверить попадания кулаков по врагам"""
        attack = self.player.get_fist_attack_area()
        if attack is None:
            return

        # Трекинг для ground slam (один раз за удар)
        attack_id = self.player.fist_total_hits
        if attack_id != self.last_fist_attack_id:
            self.last_fist_attack_id = attack_id
            self.ground_slam_done_this_attack = False

        attack_x = attack["x"]
        attack_y = attack["y"]
        attack_range = attack["range"]
        attack_angle = attack["angle"]
        attack_arc = attack["arc"]
        base_damage = attack["damage"]
        knockback = attack["knockback"]
        is_finisher = attack["is_finisher"]
        is_mega = attack.get("is_mega", False)

        # Количество целей
        max_targets = 1 + self.player.stats["target_count"]
        if is_finisher:
            max_targets += 3  # финальный удар бьёт больше
        if is_mega:
            max_targets += 5  # мега-удар бьёт ещё больше

        targets_hit = 0

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy in self.player.fist_hit_enemies:
                continue
            if targets_hit >= max_targets:
                break

            # Расстояние до врага
            dx = enemy.x - attack_x
            dy = enemy.y - attack_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > attack_range + enemy.size:
                continue

            # Проверка дуги (финальный/мега = 360°, пропускаем проверку)
            if attack_arc < math.pi:
                angle_to_enemy = math.atan2(dy, dx)
                angle_diff = angle_to_enemy - attack_angle
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                if abs(angle_diff) > attack_arc:
                    continue

            # Направление откидывания
            if dist > 0:
                kb_dx = dx / dist
                kb_dy = dy / dist
            else:
                rand_angle = random.random() * math.pi * 2
                kb_dx = math.cos(rand_angle)
                kb_dy = math.sin(rand_angle)

            # Угол атаки для щитовика
            from_angle = math.atan2(-dy, -dx)

            # Настройки частиц
            p_count = 15 if is_mega else (10 if is_finisher else 5)
            p_color = ORANGE if (is_mega or is_finisher) else None

            # Нанести урон
            killed, actual_damage, is_crit = self.deal_damage_to_enemy(
                enemy, base_damage, from_angle,
                knockback_force=knockback,
                knockback_dir_x=kb_dx, knockback_dir_y=kb_dy,
                particle_count=p_count, particle_color=p_color,
                source="fist"
            )

            self.player.fist_hit_enemies.append(enemy)
            targets_hit += 1

            # Тряска камеры для особых ударов
            if is_mega:
                self.camera.add_shake(SHAKE_MEGA_HIT)
            elif is_finisher:
                self.camera.add_shake(SHAKE_UPPERCUT)

    # ================================================================
    # ВОЛНЫ ОТ КУЛАКОВ (Fist Waves)
    # ================================================================
    def check_fist_waves(self):
        """Проверить столкновения волн от ударов кулаков с врагами"""
        for wave in self.player.fist_waves:
            if not wave.alive:
                continue

            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if enemy in wave.hit_enemies:
                    continue

                dx = enemy.x - wave.x
                dy = enemy.y - wave.y

                # Проецируем позицию врага на направление волны
                # dot — расстояние вдоль направления волны
                dot = dx * wave.dir_x + dy * wave.dir_y
                if dot < -enemy.size or dot > enemy.size + 20:
                    continue

                # perp — перпендикулярное расстояние от линии волны
                perp = abs(dx * (-wave.dir_y) + dy * wave.dir_x)

                # Ширина волны уменьшается с расстоянием
                alpha = 1.0 - wave.distance_traveled / wave.max_range
                half_width = wave.width * alpha * 0.5

                if perp < half_width + enemy.size:
                    # Попадание!
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 0:
                        kb_dx = dx / dist
                        kb_dy = dy / dist
                    else:
                        kb_dx = wave.dir_x
                        kb_dy = wave.dir_y

                    self.deal_damage_to_enemy(
                        enemy, wave.damage, None,
                        knockback_force=100,
                        knockback_dir_x=kb_dx, knockback_dir_y=kb_dy,
                        can_stun=False, can_lifesteal=False,
                        particle_color=YELLOW, particle_count=4,
                        source="wave"
                    )
                    wave.hit_enemies.append(enemy)

    # ================================================================
    # УДАР ПО ЗЕМЛЕ (Ground Slam)
    # ================================================================
    def check_ground_slam(self):
        """
        AoE удар при финальном ударе серии кулаков.
        Притягивает врагов к игроку перед нанесением урона.
        """
        if self.player.stats["fist_ground_slam"] <= 0:
            return

        attack = self.player.get_fist_attack_area()
        if attack is None:
            return
        if not attack["is_finisher"]:
            return
        if self.ground_slam_done_this_attack:
            return

        # Только в начале удара (первый кадр)
        if self.player.fist_attack_timer < self.player.fist_attack_duration * 0.8:
            return

        self.ground_slam_done_this_attack = True

        slam_level = self.player.stats["fist_ground_slam"]
        slam_radius = GROUND_SLAM_RADIUS + slam_level * 25
        slam_damage = self.player.get_fist_damage() * GROUND_SLAM_DAMAGE_MULTIPLIER * slam_level

        # Тряска камеры
        self.camera.add_shake(SHAKE_GROUND_SLAM)

        # Визуальное кольцо
        self.player.level_up_rings.append((0, 0.5, 0.5))

        # Частицы земли
        for i in range(20 + slam_level * 8):
            angle = random.random() * math.pi * 2
            speed = random.uniform(100, 300)
            color = random.choice([BROWN, DARK_GRAY, GRAY, ORANGE])
            particle = Particle(
                self.player.x, self.player.y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                color,
                random.uniform(0.3, 0.8),
                random.randint(3, 7)
            )
            self.particle_manager.particles.append(particle)

        # Обработать каждого врага в радиусе
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > slam_radius + enemy.size:
                continue

            # Притягивание врагов перед ударом
            if dist > 0 and GROUND_SLAM_PULL_FORCE > 0:
                pull_x = -dx / dist * GROUND_SLAM_PULL_FORCE
                pull_y = -dy / dist * GROUND_SLAM_PULL_FORCE
                enemy.apply_knockback(pull_x, pull_y)

            # Урон уменьшается с расстоянием (60%-100%)
            distance_factor = 1.0 - (dist / (slam_radius + enemy.size)) * 0.4
            actual_damage = slam_damage * distance_factor

            # Направление откидывания (после притягивания)
            if dist > 0:
                kb_dx = dx / dist
                kb_dy = dy / dist
            else:
                rand_angle = random.random() * math.pi * 2
                kb_dx = math.cos(rand_angle)
                kb_dy = math.sin(rand_angle)

            self.deal_damage_to_enemy(
                enemy, actual_damage, None,
                knockback_force=FIST_KNOCKBACK * 2.5,
                knockback_dir_x=kb_dx, knockback_dir_y=kb_dy,
                can_stun=True, can_lifesteal=False,
                particle_color=BROWN, particle_count=8,
                source="slam"
            )

    # ================================================================
    # XP ПРИТЯГИВАНИЕ ОТ КУЛАКОВ
    # ================================================================
    def check_fist_xp_pull(self):
        """Кулаки притягивают ближайшие XP сферы при ударе"""
        if self.player.stats["fist_xp_pull"] <= 0:
            return
        if not self.player.fist_attack_active:
            return

        pull_radius = FIST_XP_PULL_RADIUS * self.player.stats["fist_xp_pull"]

        for orb in self.xp_orbs:
            if orb.being_collected:
                continue

            dx = self.player.x - orb.x
            dy = self.player.y - orb.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < pull_radius:
                orb.being_collected = True

    # ================================================================
    # DASH-АТАКА
    # ================================================================
    def check_dash_attack(self):
        """Проверить попадания dash-атаки (после скольжения + ЛКМ)"""
        attack = self.player.get_dash_attack_area()
        if attack is None:
            return

        attack_x = attack["x"]
        attack_y = attack["y"]
        attack_range = attack["range"]
        base_damage = attack["damage"]

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy in self.player.dash_attack_hit_enemies:
                continue

            dx = enemy.x - attack_x
            dy = enemy.y - attack_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > attack_range + enemy.size:
                continue

            # Направление откидывания
            if dist > 0:
                kb_dx = dx / dist
                kb_dy = dy / dist
            else:
                rand_angle = random.random() * math.pi * 2
                kb_dx = math.cos(rand_angle)
                kb_dy = math.sin(rand_angle)

            from_angle = math.atan2(-dy, -dx)

            self.deal_damage_to_enemy(
                enemy, base_damage, from_angle,
                knockback_force=FIST_KNOCKBACK * 2.5,
                knockback_dir_x=kb_dx, knockback_dir_y=kb_dy,
                particle_color=ORANGE, particle_count=12,
                source="dash"
            )
            self.player.dash_attack_hit_enemies.append(enemy)

    # ================================================================
    # СКОЛЬЖЕНИЕ — ОТКИДЫВАНИЕ
    # ================================================================
    def check_slide_knockback(self):
        """Проверить откидывание врагов при скольжении"""
        if not self.player.is_slide_knockback_active():
            return

        knockback_radius = self.player.get_slide_knockback_radius()
        knockback_damage = self.player.get_slide_knockback_damage()

        for enemy in self.enemies:
            if not enemy.alive:
                continue

            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist >= knockback_radius + enemy.size:
                continue

            # Направление откидывания
            if dist > 0:
                kb_dx = dx / dist
                kb_dy = dy / dist
            else:
                rand_angle = random.random() * math.pi * 2
                kb_dx = math.cos(rand_angle)
                kb_dy = math.sin(rand_angle)

            from_angle = math.atan2(-dy, -dx)

            self.deal_damage_to_enemy(
                enemy, knockback_damage, from_angle,
                knockback_force=SLIDE_KNOCKBACK_FORCE,
                knockback_dir_x=kb_dx, knockback_dir_y=kb_dy,
                can_stun=False, can_lifesteal=False,
                particle_color=CYAN, particle_count=8,
                source="slide"
            )

    # ================================================================
    # КОНТРАТАКА
    # ================================================================
    def check_counter_attack(self):
        """Проверить контратаку (автоматический удар при получении урона)"""
        area = self.player.get_counter_attack_area()
        if area is None:
            return

        counter_x = area["x"]
        counter_y = area["y"]
        counter_range = area["range"]
        counter_damage = area["damage"]

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy in self.player.counter_attack_hit_enemies:
                continue

            dx = enemy.x - counter_x
            dy = enemy.y - counter_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > counter_range + enemy.size:
                continue

            # Направление откидывания
            if dist > 0:
                kb_dx = dx / dist
                kb_dy = dy / dist
            else:
                kb_dx, kb_dy = 1, 0

            self.deal_damage_to_enemy(
                enemy, counter_damage, None,
                knockback_force=FIST_KNOCKBACK * 2,
                knockback_dir_x=kb_dx, knockback_dir_y=kb_dy,
                can_stun=True, can_lifesteal=True,
                particle_color=SILVER, particle_count=8,
                source="fist"
            )
            self.player.counter_attack_hit_enemies.append(enemy)

    # ================================================================
    # УДАРНАЯ ВОЛНА СКОЛЬЖЕНИЯ (Shockwave)
    # ================================================================
    def check_shockwave_damage(self):
        """Проверить урон от ударных волн при остановке скольжения"""
        for wave in self.player.shockwaves:
            wx, wy, wr, wmr, wd = wave

            for enemy in self.enemies:
                if not enemy.alive:
                    continue

                dx = enemy.x - wx
                dy = enemy.y - wy
                dist = math.sqrt(dx * dx + dy * dy)

                # Волна — это расширяющееся кольцо
                ring_inner = max(0, wr - 15)
                ring_outer = wr + 15

                if not (ring_inner <= dist <= ring_outer + enemy.size):
                    continue

                # Проверить, не ударяли ли уже этого врага этой волной
                wave_id = id(wave)
                if not hasattr(enemy, '_hit_waves'):
                    enemy._hit_waves = set()
                if wave_id in enemy._hit_waves:
                    continue
                enemy._hit_waves.add(wave_id)

                # Направление откидывания
                if dist > 0:
                    kb_dx = dx / dist
                    kb_dy = dy / dist
                else:
                    kb_dx, kb_dy = 1, 0

                self.deal_damage_to_enemy(
                    enemy, wd, None,
                    knockback_force=200,
                    knockback_dir_x=kb_dx, knockback_dir_y=kb_dy,
                    can_stun=False, can_lifesteal=False,
                    particle_color=PURPLE, particle_count=4,
                    source="shockwave"
                )

    # ================================================================
    # ЭЛЕКТРИЧЕСКИЙ СЛЕД
    # ================================================================
    def check_electric_trail_damage(self, dt):
        """Урон от электрических следов скольжения"""
        if self.player.stats["slide_electric_trail"] <= 0:
            return

        trail_level = self.player.stats["slide_electric_trail"]
        trail_dps = ELECTRIC_TRAIL_DAMAGE * trail_level
        damage_per_frame = trail_dps * dt

        for tx, ty, tt in self.player.electric_trails:
            alpha = tt / ELECTRIC_TRAIL_DURATION
            current_radius = ELECTRIC_TRAIL_RADIUS * alpha

            for enemy in self.enemies:
                if not enemy.alive:
                    continue

                dx = enemy.x - tx
                dy = enemy.y - ty
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < current_radius + enemy.size:
                    killed = enemy.take_damage(damage_per_frame)

                    # Периодические молнии (визуал)
                    if random.random() < 0.03:
                        self.particle_manager.spawn_hit_particles(
                            enemy.x, enemy.y, CYAN, count=3
                        )
                        # Маленькая молния-частица
                        self.particle_manager.particles.append(
                            Particle(
                                enemy.x, enemy.y,
                                random.uniform(-80, 80),
                                random.uniform(-80, 80),
                                (100, 200, 255), 0.2, 2
                            )
                        )

                    if killed:
                        self.on_enemy_killed(enemy)

    # ================================================================
    # КОНТАКТНЫЙ УРОН ВРАГОВ
    # ================================================================
    def check_enemy_contact_damage(self):
        """Проверить контактный урон от врагов к игроку"""
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if not enemy.can_deal_damage():
                continue

            # Оглушённый враг не атакует
            if getattr(enemy, 'stun_timer', 0) > 0:
                continue

            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            dist = math.sqrt(dx * dx + dy * dy)
            contact_dist = self.player.size + enemy.size

            if dist < contact_dist:
                thorns_damage = self.player.take_damage(enemy.damage)
                enemy.reset_hit_cooldown()

                # Шипы — ответный урон
                if thorns_damage > 0 and self.player.stats["thorns"] > 0:
                    killed = enemy.take_damage(thorns_damage)
                    self.particle_manager.add_damage_number(
                        enemy.x, enemy.y, thorns_damage, color=GRAY
                    )
                    if killed:
                        self.on_enemy_killed(enemy)

                # Визуал получения урона
                if self.player.flash_timer > 0:
                    self.particle_manager.spawn_hit_particles(
                        self.player.x, self.player.y, RED, count=8
                    )
                    self.particle_manager.add_damage_number(
                        self.player.x, self.player.y,
                        enemy.damage, color=RED
                    )
                    self.camera.add_shake(SHAKE_PLAYER_HIT)

    # ================================================================
    # СМЕРТЬ ВРАГА
    # ================================================================
    def on_enemy_killed(self, enemy):
        """Обработка убийства врага"""
        self.player.enemies_killed += 1
        self.player.add_combo()
        self.player.gain_ult_charge(3.0)

        # Частицы смерти
        death_particles = 15
        if getattr(enemy, 'is_boss', False):
            death_particles = 40
            self.camera.add_shake(SHAKE_BOSS_DEATH)
            self.particle_manager.add_message(t("MSG_BOSS_DEFEATED"), GOLD)
            self.achievement_manager.unlock("boss_slayer", self.particle_manager)
        else:
            # Маленький shake при большом комбо
            if self.player.combo_count > 10 and self.player.combo_count % 10 == 0:
                self.camera.add_shake(2)

        self.particle_manager.spawn_death_particles(
            enemy.x, enemy.y, enemy.color, count=death_particles
        )

        # Выпадение опыта
        xp_orb = XPOrb(enemy.x, enemy.y, enemy.xp_reward)
        self.xp_orbs.append(xp_orb)

        # Шанс сброса КД скольжения
        self.player.try_reset_slide_cooldown()

        # Шанс дропа предмета
        drop_bonus = self.player.stats["drop_chance"]
        item_type = roll_drop(drop_bonus)
        if item_type:
            item = DroppedItem(enemy.x, enemy.y, item_type)
            self.dropped_items.append(item)

        # Взрывник — взрыв при смерти
        if getattr(enemy, 'should_explode', False):
            self.handle_explosion(enemy)

        # Сохранить корпус для некроманта
        if not getattr(enemy, 'is_boss', False):
            self.corpse_positions.append((
                enemy.x, enemy.y,
                enemy.enemy_type,
                self.game_time
            ))

    def handle_explosion(self, exploder):
        """Обработка взрыва взрывника при смерти"""
        ex, ey = exploder.x, exploder.y
        radius = exploder.explode_radius
        damage = exploder.explode_damage

        # Частицы взрыва
        self.particle_manager.spawn_bomb_particles(ex, ey, count=25)
        self.camera.add_shake(SHAKE_BOSS_HIT)

        # Урон игроку
        dx = self.player.x - ex
        dy = self.player.y - ey
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < radius + self.player.size:
            self.player.take_damage(damage)
            self.particle_manager.add_damage_number(
                self.player.x, self.player.y, damage, color=ORANGE
            )
            # Откинуть игрока от взрыва
            if dist > 0:
                push_force = 300
                self.player.velocity_x += (dx / dist) * push_force
                self.player.velocity_y += (dy / dist) * push_force

        # Урон другим врагам
        for other in self.enemies:
            if other is exploder or not other.alive:
                continue

            odx = other.x - ex
            ody = other.y - ey
            odist = math.sqrt(odx * odx + ody * ody)

            if odist < radius + other.size:
                killed = other.take_damage(damage * 0.5)
                if odist > 0:
                    other.apply_knockback(
                        (odx / odist) * 200,
                        (ody / odist) * 200
                    )
                if killed:
                    self.on_enemy_killed(other)

    # ================================================================
    # ОБНОВЛЕНИЕ XP СФЕР
    # ================================================================
    def update_xp_orbs(self, dt):
        """Обновить XP сферы и проверить сбор"""
        pickup_radius = self.player.get_xp_radius()

        for orb in self.xp_orbs:
            collected = orb.update(dt, self.player.x, self.player.y, pickup_radius)
            if collected:
                self.player.gain_xp(orb.xp)
                self.particle_manager.spawn_xp_particles(
                    self.player.x, self.player.y
                )

        self.xp_orbs = [o for o in self.xp_orbs if o.alive]

    # ================================================================
    # ОБНОВЛЕНИЕ ПРЕДМЕТОВ
    # ================================================================
    def update_items(self, dt):
        """Обновить предметы на земле"""
        for item in self.dropped_items:
            result = item.update(dt, self.player.x, self.player.y)
            if result:
                self.apply_item_effect(result)

        self.dropped_items = [i for i in self.dropped_items if i.alive]

    def apply_item_effect(self, item_type):
        """Применить эффект подобранного предмета"""
        if item_type == "heal":
            heal_amount = HEAL_AMOUNT * self.player.get_heal_effectiveness()
            self.player.heal(heal_amount)
            self.particle_manager.spawn_heal_particles(
                self.player.x, self.player.y
            )
            self.particle_manager.add_message(t("MSG_HEALTH_RESTORED"), GREEN)

        elif item_type == "magnet":
            # Собрать все XP на карте
            for orb in self.xp_orbs:
                orb.being_collected = True
            self.particle_manager.add_message(t("MSG_MAGNET"), PURPLE)

        elif item_type == "bomb":
            # Убить всех видимых врагов (кроме боссов)
            killed_count = 0
            for enemy in self.enemies:
                if not enemy.alive:
                    continue

                # Боссу — фиксированный урон вместо убийства
                if getattr(enemy, 'is_boss', False):
                    boss_damage = enemy.max_hp * 0.1
                    enemy.take_damage(boss_damage)
                    self.particle_manager.add_damage_number(
                        enemy.x, enemy.y, int(boss_damage), color=ORANGE
                    )
                    continue

                if self.camera.is_visible(enemy.x, enemy.y, margin=50):
                    enemy.alive = False
                    killed_count += 1

                    # Опыт
                    xp_orb = XPOrb(enemy.x, enemy.y, enemy.xp_reward)
                    self.xp_orbs.append(xp_orb)

                    # Частицы
                    self.particle_manager.spawn_death_particles(
                        enemy.x, enemy.y, enemy.color
                    )

            self.player.enemies_killed += killed_count
            self.particle_manager.spawn_bomb_particles(
                self.player.x, self.player.y
            )
            self.particle_manager.add_message(
                t("MSG_BOMB", killed_count), RED
            )
            self.camera.add_shake(SHAKE_BOMB)

        elif item_type == "speed_boost":
            self.player.speed_boost_timer = SPEED_BOOST_DURATION
            self.player.speed_boost_multiplier = SPEED_BOOST_MULTIPLIER
            self.particle_manager.add_message(t("MSG_SPEED_BOOST"), CYAN)

    # ================================================================
    # АУРА УРОНА
    # ================================================================
    def apply_aura_damage(self, dt):
        """Постоянный урон вокруг игрока"""
        aura_dps = self.player.stats["aura_damage"]
        if aura_dps <= 0:
            return

        aura_radius = 80
        damage_this_frame = aura_dps * dt

        for enemy in self.enemies:
            if not enemy.alive:
                continue

            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < aura_radius + enemy.size:
                killed = enemy.take_damage(damage_this_frame)

                # Периодические частицы
                if random.random() < 0.05:
                    self.particle_manager.spawn_hit_particles(
                        enemy.x, enemy.y, ORANGE, count=2
                    )

                if killed:
                    self.on_enemy_killed(enemy)

    # ================================================================
    # АУРА ЗАМЕДЛЕНИЯ
    # ================================================================
    def apply_aura_slow(self, dt):
        """Замедление врагов рядом с игроком"""
        slow_percent = self.player.stats["aura_slow"]
        if slow_percent <= 0:
            return

        slow_radius = 100
        slow_factor = 1.0 - min(0.8, slow_percent / 100)

        for enemy in self.enemies:
            if not enemy.alive:
                continue

            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < slow_radius + enemy.size:
                enemy.velocity_x *= slow_factor
                enemy.velocity_y *= slow_factor

    # ================================================================
    # ДЕСПАВН ДАЛЁКИХ ОБЪЕКТОВ
    # ================================================================
    def despawn_far_enemies(self):
        """Удалить врагов и XP сферы, которые слишком далеко"""
        new_enemies = []
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            # Боссы НЕ деспавнятся!
            if getattr(enemy, 'no_despawn', False):
                new_enemies.append(enemy)
                continue

            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= ENEMY_DESPAWN_RADIUS:
                new_enemies.append(enemy)

        self.enemies = new_enemies

        # Деспавн далёких XP сфер
        new_orbs = []
        for orb in self.xp_orbs:
            dx = orb.x - self.player.x
            dy = orb.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < ENEMY_DESPAWN_RADIUS + 200:
                new_orbs.append(orb)
        self.xp_orbs = new_orbs

    # ================================================================
    # ОЧИСТКА КОРПУСОВ
    # ================================================================
    def cleanup_corpses(self):
        """Удалить старые корпусы для некроманта"""
        # Ограничить количество
        if len(self.corpse_positions) > self.max_corpses:
            self.corpse_positions = self.corpse_positions[-self.max_corpses:]

        # Удалить корпусы старше 30 секунд
        self.corpse_positions = [
            c for c in self.corpse_positions
            if self.game_time - c[3] < 30.0
        ]

    # ================================================================
    # ОТРИСОВКА ИГРЫ
    # ================================================================
    def draw_playing(self):
        """Нарисовать весь игровой мир"""
        self.screen.fill(BLACK)

        # Мир (фон, тайлы, декорации, следы)
        self.world.draw(self.screen, self.camera, self.game_time)

        # Корпусы (крестики на земле)
        self.draw_corpses()

        # Арена босса (под объектами)
        for boss in self.active_bosses:
            if hasattr(boss, 'draw_arena'):
                boss.draw_arena(self.screen, self.camera)

        # Ауры игрока
        self.draw_auras()

        # XP сферы
        for orb in self.xp_orbs:
            orb.draw(self.screen, self.camera)

        # Предметы
        for item in self.dropped_items:
            item.draw(self.screen, self.camera)

        # Стан-эффект над врагами (под спрайтами врагов)
        for enemy in self.enemies:
            if getattr(enemy, 'stun_timer', 0) > 0:
                self.draw_stun_effect(enemy)

        # Враги
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera)

        # Снаряды врагов
        for proj in self.enemy_projectiles:
            proj.draw(self.screen, self.camera)

        # Игрок
        self.player.draw(self.screen, self.camera)

        # Частицы и числа урона
        self.particle_manager.draw(
            self.screen, self.camera,
            self.ui.font_small, self.ui.font
        )

        # HUD
        active_boss = self.active_bosses[0] if self.active_bosses else None
        self.ui.draw_hud(
            self.screen, self.player,
            self.game_time, len(self.enemies),
            active_boss=active_boss
        )

        # Мини-карта
        if self.settings_manager.get("minimap", True):
            bosses_alive = len(self.active_bosses) > 0
            self.ui.draw_minimap(
                self.screen, self.player,
                self.enemies, self.xp_orbs,
                self.dropped_items, bosses_alive
            )

        # Вспышка экрана (поверх всего)
        self.camera.draw_flash(self.screen)

    def draw_stun_effect(self, enemy):
        """Крутящиеся звёздочки над оглушённым врагом"""
        sx, sy = self.camera.apply(enemy.x, enemy.y)
        sx, sy = int(sx), int(sy)

        # Пропустить если за экраном
        if sx < -50 or sx > SCREEN_WIDTH + 50 or sy < -50 or sy > SCREEN_HEIGHT + 50:
            return

        t = self.game_time * 3
        star_count = 3
        orbit_radius = enemy.size + 5

        for i in range(star_count):
            angle = t + i * (math.pi * 2 / star_count)
            star_x = sx + int(math.cos(angle) * orbit_radius)
            star_y = sy - enemy.size - 8 + int(math.sin(angle * 0.5) * 3)

            # Рисуем маленькую 5-конечную звёздочку
            points = []
            for j in range(5):
                star_angle = angle + j * math.pi * 2 / 5 - math.pi / 2
                radius = 4 if j % 2 == 0 else 2
                points.append((
                    star_x + int(math.cos(star_angle) * radius),
                    star_y + int(math.sin(star_angle) * radius)
                ))
            if len(points) >= 3:
                pygame.draw.polygon(self.screen, YELLOW, points)

    def draw_corpses(self):
        """Нарисовать крестики на месте убитых врагов (для некроманта)"""
        for cx, cy, ctype, ctime in self.corpse_positions:
            sx, sy = self.camera.apply(cx, cy)
            sx, sy = int(sx), int(sy)

            if sx < -10 or sx > SCREEN_WIDTH + 10 or sy < -10 or sy > SCREEN_HEIGHT + 10:
                continue

            # Прозрачность зависит от возраста
            age = self.game_time - ctime
            alpha = max(0, 1.0 - age / 30.0)
            intensity = int(60 * alpha)

            if intensity > 5:
                color = (intensity, intensity // 2, intensity // 2)
                pygame.draw.line(self.screen, color,
                               (sx - 3, sy - 3), (sx + 3, sy + 3), 1)
                pygame.draw.line(self.screen, color,
                               (sx + 3, sy - 3), (sx - 3, sy + 3), 1)

    def draw_auras(self):
        """Нарисовать визуальные ауры игрока"""
        # Аура урона
        if self.player.stats["aura_damage"] > 0:
            sx, sy = self.camera.apply(self.player.x, self.player.y)
            aura_radius = 80
            aura_surface = pygame.Surface(
                (aura_radius * 2, aura_radius * 2), pygame.SRCALPHA
            )
            pulse = abs(math.sin(self.game_time * 3))
            alpha = int(20 + 15 * pulse)
            pygame.draw.circle(
                aura_surface, (255, 100, 0, alpha),
                (aura_radius, aura_radius), aura_radius
            )
            pygame.draw.circle(
                aura_surface, (255, 100, 0, alpha + 30),
                (aura_radius, aura_radius), aura_radius, 2
            )
            self.screen.blit(
                aura_surface,
                (int(sx) - aura_radius, int(sy) - aura_radius)
            )

        # Аура замедления
        if self.player.stats["aura_slow"] > 0:
            sx, sy = self.camera.apply(self.player.x, self.player.y)
            aura_radius = 100
            aura_surface = pygame.Surface(
                (aura_radius * 2, aura_radius * 2), pygame.SRCALPHA
            )
            pulse = abs(math.sin(self.game_time * 2))
            alpha = int(15 + 10 * pulse)
            pygame.draw.circle(
                aura_surface, (50, 100, 255, alpha),
                (aura_radius, aura_radius), aura_radius
            )
            pygame.draw.circle(
                aura_surface, (50, 100, 255, alpha + 20),
                (aura_radius, aura_radius), aura_radius, 2
            )
            self.screen.blit(
                aura_surface,
                (int(sx) - aura_radius, int(sy) - aura_radius)
            )


# ================================================================
# ТОЧКА ВХОДА
# ================================================================
if __name__ == "__main__":
    game = Game()
    game.run()