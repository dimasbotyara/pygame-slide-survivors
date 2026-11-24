# main.py — v4 — Полная версия без сокращений
# Мега-кулаки, волны, XP pull, ground slam pull, электрослед, все системы

import pygame
import sys
import math
import random
from settings import *
from abilities import IceTrail, PulseAuras
from camera import Camera
from player import Player
from enemies import Enemy, Boss, EnemyProjectile, EnemySpawner
from upgrades import UpgradeManager
from particles import ParticleManager, Particle
from items import XPOrb, DroppedItem, roll_drop
from world import World
from wildlife import HabitatFade
from spatial import EnemyGrid
from consumables import TONICS
from ui import (UI, menu_inputs, menu_rect, pause_rect, hero_rect, upgrade_rect,
                language_rect, settings_rect, settings_value_left_rect,
                settings_value_right_rect, result_rect, hero_arrow_rect)
from highscores import add_highscore
from settings_manager import SettingsManager
from display_manager import DisplayManager
from game_icon import make_icon
from preferences import TABS, BINDINGS, valid_value
from ui import NUMBER_KEYS, settings_tab_rect, reset_button_rect, reset_confirm_rect, reset_cancel_rect
from translations import t
from heroes import HEROES, HERO_KEYS
from achievements import AchievementManager
from bestiary import Bestiary, guide_rect
from ultimates import CorpseProjectile, fracture_lines, lightning_segments



class Game:
    def __init__(self, world_seed=None):
        self.world_seed = world_seed
        pygame.init()
        pygame.display.set_caption(TITLE)
        pygame.display.set_icon(make_icon())
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Менеджер настроек и достижений
        self.settings_manager = SettingsManager()
        self.display = DisplayManager(self.settings_manager)
        self.achievement_manager = AchievementManager()

        # UI
        self.ui = UI()
        self.ui.settings = self.settings_manager
        self.ui.mouse_pos = self.display.mouse_pos

        # Состояние игры
        if self.settings_manager.get("first_launch", True):
            self.state = "language_select"
        else:
            self.state = "menu"

        self.selected_hero_index = HERO_KEYS.index(self.settings_manager.get("selected_hero", "slider"))
        self.ult_uses_run = 0
        self.bosses_killed_run = 0
        self.ultimate_cast_pending = False
        self.ultimate_cast_hero = None
        self.ultimate_cast_duration = 0.0
        self.ult_zoom_strength = 0.0
        self.ult_afterglow_timer = 0.0
        self.ultimate_bodies = []
        self.ultimate_rings = []
        self.earthquake_cracks = []
        self.earthquake_crack_timer = 0.0
        self.earthquake_crack_duration = 15.0
        self.storm_zones = []
        self.spark_storm_timer = 0.0
        self.spark_storm_duration = 10.0
        self.spark_storm_tick = 0.0
        self.rain_drops = []
        self.slider_ultimate = None
        self.shadow_ult_blades = []
        self.crack_overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.storm_overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.spark_glow_surface = pygame.Surface((232, 232), pygame.SRCALPHA)
        self.lightning_bolts = []
        self.shadow_slashes = []
        self.bestiary = None
        self.hero_cursor = 0
        self.surrendered = False
        self.lang_selection = 0
        self.menu_selection = 0
        self.settings_tab = 0
        self.settings_selection = 0
        self.settings_previous_state = "menu"
        self.reset_confirmation = False
        self.binding_capture = None
        self.reset_error = False
        self.pause_selection = 0
        self.game_over_selection = 0
        self.new_record_pos = -1

        # Игровые объекты
        self.player = None
        self.camera = None
        self.world = None
        self.enemies = []
        self.habitat_fades = []
        self.enemy_projectiles = []
        self.pending_explosions = []
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

    # ================================================================
    # ГЛАВНЫЙ ЦИКЛ
    # ================================================================
    def run(self):
        while self.running:
            dt = self.clock.tick(self.settings_manager.get("fps_limit", FPS)) / 1000.0
            dt = min(dt, 0.05)  # защита от скачков

            previous_state = self.state
            previous_frame = self.transition_snapshot()
            events = self.prepare_events(pygame.event.get())
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
            elif self.state == "bestiary":
                self.update_bestiary(events)
                self.draw_bestiary()
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

            if previous_frame is not None and self.state != previous_state and (self.state == "menu" or previous_state == "menu"):
                self.ui.begin_transition(previous_frame)
            if self.settings_manager.get("menu_animations"):
                self.ui.draw_transition(self.screen)
            self.present()

        pygame.quit()
        sys.exit()

    def transition_snapshot(self):
        if self.settings_manager.get('menu_animations') and self.state not in ('playing', 'upgrading'):
            return self.screen.copy()
        return None

    def prepare_events(self, events):
        for event in events:
            focus_lost = event.type == pygame.WINDOWFOCUSLOST or (
                event.type == pygame.ACTIVEEVENT and getattr(event, 'gain', 1) == 0
                and getattr(event, 'state', 0) & 2)
            if focus_lost and self.state == 'playing' and self.settings_manager.get('pause_unfocused'):
                self.state = 'paused'
        return self.display.events(events)

    def present(self):
        if self.settings_manager.get('show_fps'):
            text = self.ui.mono.render(f"{self.clock.get_fps():.0f} FPS", True, self.ui.theme_accent)
            rect = text.get_rect(midtop=(SCREEN_WIDTH//2, 76))
            pygame.draw.rect(self.screen, self.ui.INK, rect.inflate(16, 6), border_radius=4)
            self.screen.blit(text, rect)
        self.display.present(self.screen)

    def apply_runtime_settings(self):
        cfg = self.settings_manager
        if self.player:
            self.player.bindings = {key: cfg.get(key) for key in BINDINGS}
        if self.camera:
            self.camera.culling_enabled = cfg.get("view_culling")
            self.camera.entity_shadows = cfg.get("entity_shadows")
            self.camera.shake_enabled = cfg.get('screen_shake')
            if not self.camera.shake_enabled:
                self.camera.shake_timer = 0
                self.camera.shake_offset_x = self.camera.shake_offset_y = 0
            self.camera.lerp_speed = cfg.get('camera_smoothing')
            self.camera.look_ahead_distance = cfg.get('camera_lookahead')
        if self.particle_manager:
            pm = self.particle_manager
            pm.damage_numbers_enabled = cfg.get('damage_numbers')
            pm.density = cfg.get('particle_density')
            pm.budget = cfg.get('particle_budget')
            pm.notifications_enabled = cfg.get('notifications')
            pm.message_duration = cfg.get('notification_duration')
            pm.culling_enabled = cfg.get('view_culling')
            if not pm.damage_numbers_enabled:
                pm.damage_numbers.clear()
            if not pm.notifications_enabled:
                pm.messages.clear()
            if pm.density == 0:
                pm.particles.clear()
            del pm.particles[pm.budget:]

    # ================================================================
    # ИНИЦИАЛИЗАЦИЯ НОВОЙ ИГРЫ
    # ================================================================
    def start_new_game(self):
        """Начать новую игру — сбросить все объекты"""
        self.surrendered = False
        self.ult_uses_run = 0
        self.bosses_killed_run = 0
        self.ultimate_cast_pending = False
        self.ultimate_cast_hero = None
        self.ultimate_cast_duration = 0.0
        self.ult_zoom_strength = 0.0
        self.ult_afterglow_timer = 0.0
        self.ultimate_bodies.clear()
        self.ultimate_rings.clear()
        self.earthquake_cracks.clear()
        self.earthquake_crack_timer = 0.0
        self.earthquake_crack_duration = 15.0
        self.storm_zones.clear()
        self.spark_storm_timer = 0.0
        self.spark_storm_tick = 0.0
        self.rain_drops.clear()
        self.slider_ultimate = None
        self.shadow_ult_blades.clear()
        self.lightning_bolts.clear()
        self.shadow_slashes.clear()
        hero_id = HERO_KEYS[self.selected_hero_index]
        self.player = Player(0, 0, hero_id=hero_id)
        self.player.bindings = {key: self.settings_manager.get(key) for key in BINDINGS}
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera.shake_enabled = self.settings_manager.get("screen_shake", True)
        self.world = World(seed=self.world_seed)
        self.ice_trail = IceTrail()
        self.pulse_auras = PulseAuras()
        self.enemies = []
        self.habitat_fades = []
        self.enemy_projectiles = []
        self.pending_explosions = []
        self.xp_orbs = []
        self.dropped_items = []
        self.spawner = EnemySpawner(self.world)
        self.upgrade_manager = UpgradeManager()
        self.particle_manager = ParticleManager()
        self.apply_runtime_settings()
        self.game_time = 0.0
        self.game_messages = []
        self.active_bosses = []
        self.corpse_positions = []
        self.slide_trail_timer = 0.0
        self.new_record_pos = -1
        self.state = "playing"

    # ================================================================
    # ВЫБОР ЯЗЫКА ПРИ ПЕРВОМ ЗАПУСКЕ
    # ================================================================
    def update_language_select(self, events):
        rects = [language_rect(i) for i in range(2)]
        for hovered, key in menu_inputs(events, rects):
            if hovered is not None:
                self.lang_selection = hovered
            if key is None:
                continue
            if key in (pygame.K_UP, pygame.K_w):
                self.lang_selection = (self.lang_selection - 1) % 2
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.lang_selection = (self.lang_selection + 1) % 2
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                lang = "ru" if self.lang_selection == 0 else "en"
                self.settings_manager.set("language", lang)
                self.settings_manager.set("first_launch", False)
                self.state = "menu"
                self.menu_selection = 0
                return

    def draw_language_select(self):
        self._sync_theme()
        self.ui.draw_language_select_screen(self.screen, self.lang_selection)

    # ================================================================
    # ВЫБОР ПЕРСОНАЖА
    # ================================================================
    def update_hero_select(self, events):
        rects = [hero_rect(i) for i in range(len(HERO_KEYS))]
        for hovered, key in menu_inputs(events, rects):
            if hovered is not None:
                self.hero_cursor = hovered
            if key is None:
                continue
            if key in (pygame.K_LEFT, pygame.K_a):
                self.hero_cursor = (self.hero_cursor - 1) % len(HERO_KEYS)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.hero_cursor = (self.hero_cursor + 1) % len(HERO_KEYS)
            elif key == pygame.K_RETURN:
                self.selected_hero_index = self.hero_cursor
                self.settings_manager.set("selected_hero", HERO_KEYS[self.selected_hero_index])
                self.menu_selection = 0
                self.state = "menu"
                return
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
                return

    def draw_hero_select(self):
        self._sync_theme()
        self.ui.draw_hero_select_screen(self.screen, self.hero_cursor)

    # ================================================================
    # ДОСТИЖЕНИЯ
    # ================================================================
    def update_achievements(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    self.ui.achievement_dragging = False
                    return
                if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                    self.ui.achievement_scroll += 198 if event.key == pygame.K_PAGEDOWN else 66
                elif event.key in (pygame.K_UP, pygame.K_PAGEUP):
                    self.ui.achievement_scroll -= 198 if event.key == pygame.K_PAGEUP else 66
            self.ui.handle_achievement_event(event)

    def _sync_theme(self):
        self.ui.apply_theme(self.selected_hero_index, self.settings_manager.get('theme', 'hero'))
        if self.particle_manager is not None:
            import ui as ui_module
            accent = self.ui.theme_accent
            self.particle_manager.theme_palette = (
                accent, ui_module.PANEL, ui_module.EDGE, ui_module.PAPER
            )

    def draw_achievements(self):
        self._sync_theme()
        self.ui.draw_achievements_screen(self.screen, self.achievement_manager)

    # ================================================================
    # ГЛАВНОЕ МЕНЮ
    # ================================================================
    def update_menu(self, events):
        for event in events:
            if ((event.type == pygame.KEYDOWN and event.key in (pygame.K_b, pygame.K_8, pygame.K_KP8)) or
                    (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and guide_rect().collidepoint(event.pos))):
                if self.bestiary is None:
                    self.bestiary = Bestiary()
                self.state = 'bestiary'
                return
        rects = [menu_rect(i) for i in range(7)]
        arrows = [(hero_arrow_rect(-1), pygame.K_LEFT), (hero_arrow_rect(1), pygame.K_RIGHT)]
        for hovered, key in menu_inputs(events, rects, extra_buttons=arrows):
            if hovered is not None:
                self.menu_selection = hovered
            if key is None:
                continue
            if key in (pygame.K_LEFT, pygame.K_RIGHT):
                step = 1 if key == pygame.K_RIGHT else -1
                self.selected_hero_index = (self.selected_hero_index + step) % len(HERO_KEYS)
                self.settings_manager.set("selected_hero", HERO_KEYS[self.selected_hero_index])
            elif key in (pygame.K_UP, pygame.K_w):
                self.menu_selection = (self.menu_selection - 1) % 7
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selection = (self.menu_selection + 1) % 7
            elif key == pygame.K_RETURN:
                if self.menu_selection == 0:
                    self.start_new_game()
                elif self.menu_selection == 1:
                    self.hero_cursor = self.selected_hero_index
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
                return

    def update_bestiary(self, events):
        if self.bestiary.handle(events):
            self.state = 'menu'

    def draw_bestiary(self):
        self._sync_theme()
        self.bestiary.draw(self.screen, self.ui)

    def draw_menu(self):
        self._sync_theme()
        self.ui.draw_main_menu(self.screen, self.menu_selection, self.selected_hero_index)

    # ================================================================
    # ЭКРАН НАСТРОЕК
    # ================================================================
    def _change_setting(self, row_index, direction):
        rows = TABS[self.settings_tab][1]
        name, choices = rows[row_index]
        if name in BINDINGS:
            self.binding_capture = name
            return
        current = self.settings_manager.get(name)
        index = choices.index(current) if current in choices else 0
        self.settings_manager.set(name, choices[(index + direction) % len(choices)])
        if name in ('fullscreen', 'resolution'):
            self.display.apply()
        self.apply_runtime_settings()

    def delete_user_data(self):
        # Only delete files owned by the game; never recursively remove a directory.
        import achievements, highscores, settings_manager
        errors = []
        for path in (settings_manager.SETTINGS_FILE, achievements.ACHIEVEMENTS_FILE,
                     highscores.HIGHSCORES_FILE):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            except OSError as exc:
                errors.append(exc)
        if errors:
            self.reset_confirmation = False
            self.reset_error = True
        else:
            self.running = False

    def update_settings(self, events):
        for event in events:
            if self.binding_capture is not None:
                if event.type == pygame.KEYDOWN:
                    key = event.key
                    if key == pygame.K_ESCAPE:
                        self.binding_capture = None
                    elif valid_value(self.binding_capture, key):
                        current = self.settings_manager.get(self.binding_capture)
                        other = next((k for k in BINDINGS if k != self.binding_capture and self.settings_manager.get(k) == key), None)
                        if other:
                            self.settings_manager.settings[other] = current
                        self.settings_manager.set(self.binding_capture, key)
                        self.apply_runtime_settings()
                        self.binding_capture = None
                continue
            if self.reset_confirmation:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.reset_confirmation = False
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.delete_user_data()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if reset_cancel_rect().collidepoint(event.pos):
                        self.reset_confirmation = False
                    elif reset_confirm_rect().collidepoint(event.pos):
                        self.delete_user_data()
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and reset_button_rect().collidepoint(event.pos):
                self.reset_confirmation = True
                self.reset_error = False
                continue
            if event.type == pygame.KEYDOWN and event.key in NUMBER_KEYS:
                index = NUMBER_KEYS[event.key]
                if index < len(TABS):
                    self.settings_tab, self.settings_selection = index, 0
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.settings_tab = (self.settings_tab + (-1 if getattr(event, 'mod', 0) & pygame.KMOD_SHIFT else 1)) % len(TABS)
                self.settings_selection = 0
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                tab = next((i for i in range(len(TABS)) if settings_tab_rect(i).collidepoint(event.pos)), None)
                if tab is not None:
                    self.settings_tab, self.settings_selection = tab, 0
                    continue
            rows = TABS[self.settings_tab][1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hit_row = next((i for i in range(len(rows)) if settings_rect(i).collidepoint(event.pos)), None)
                if hit_row is not None:
                    self.settings_selection = hit_row
                    if settings_value_left_rect(hit_row).collidepoint(event.pos):
                        self._change_setting(hit_row, -1)
                    elif settings_value_right_rect(hit_row).collidepoint(event.pos):
                        self._change_setting(hit_row, 1)
                    elif TABS[self.settings_tab][1][hit_row][0] in BINDINGS:
                        self.binding_capture = TABS[self.settings_tab][1][hit_row][0]
                    # The arrows are explicit controls; clicking elsewhere on a
                    # setting row only focuses it and cannot accidentally cycle it.
                    continue
            for hovered, key in menu_inputs([event], [settings_rect(i) for i in range(len(rows))]):
                if hovered is not None:
                    self.settings_selection = hovered
                if key == pygame.K_ESCAPE:
                    self.settings_manager.save()
                    self.state = self.settings_previous_state
                    return
                if key in (pygame.K_UP, pygame.K_w):
                    self.settings_selection = (self.settings_selection-1) % (len(rows)+1)
                elif key in (pygame.K_DOWN, pygame.K_s):
                    self.settings_selection = (self.settings_selection+1) % (len(rows)+1)
                elif self.settings_selection == len(rows):
                    if key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset_confirmation = True
                        self.reset_error = False
                elif key in (pygame.K_LEFT, pygame.K_a):
                    self._change_setting(self.settings_selection, -1)
                elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_RETURN, pygame.K_SPACE):
                    self._change_setting(self.settings_selection, 1)

    def draw_settings(self):
        self._sync_theme()
        self.ui.draw_settings_screen(self.screen, self.settings_selection, self.settings_manager, self.settings_tab, self.binding_capture)
        if self.display.error:
            text = self.ui.body.render(t('DISPLAY_FALLBACK'), True, (255, 170, 100))
            self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH//2, 605)))
        if self.reset_error:
            text = self.ui.body.render(t('RESET_ERROR'), True, (255, 130, 120))
            self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH//2, 605)))
        if self.reset_confirmation:
            shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 190))
            self.screen.blit(shade, (0, 0))
            panel = pygame.Rect(300, 260, 680, 220)
            pygame.draw.rect(self.screen, self.ui.PANEL, panel, border_radius=10)
            pygame.draw.rect(self.screen, (235, 100, 90), panel, 2, border_radius=10)
            from ui import word_lines
            for i, line in enumerate(word_lines(self.ui.body, t('RESET_WARNING'), 620)):
                text = self.ui.body.render(line, True, self.ui.PAPER)
                self.screen.blit(text, text.get_rect(center=(640, 300 + i*27)))
            for rect, key, color in ((reset_confirm_rect(), 'RESET_CONFIRM', (152, 54, 55)),
                                     (reset_cancel_rect(), 'RESET_CANCEL', self.ui.EDGE)):
                pygame.draw.rect(self.screen, color, rect, border_radius=6)
                text = self.ui.body.render(t(key), True, self.ui.PAPER)
                self.screen.blit(text, text.get_rect(center=rect.center))

    # ================================================================
    # ЭКРАН УПРАВЛЕНИЯ
    # ================================================================
    def update_controls(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "menu"

    def draw_controls(self):
        self._sync_theme()
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
        self._sync_theme()
        self.ui.draw_highscores_screen(self.screen)

    # ================================================================
    # ПАУЗА
    # ================================================================
    def update_paused(self, events):
        rects = [pause_rect(i) for i in range(4)]
        for hovered, key in menu_inputs(events, rects):
            if hovered is not None:
                self.pause_selection = hovered
            if key is None:
                continue
            if key in (pygame.K_ESCAPE, self.settings_manager.get("bind_pause")):
                self.state = "playing"
                return
            elif key in (pygame.K_UP, pygame.K_w):
                self.pause_selection = (self.pause_selection - 1) % 4
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.pause_selection = (self.pause_selection + 1) % 4
            elif key == pygame.K_RETURN:
                if self.pause_selection == 0:
                    self.state = "playing"
                elif self.pause_selection == 1:
                    self.settings_previous_state = "paused"
                    self.settings_selection = 0
                    self.state = "settings"
                elif self.pause_selection == 2:
                    self.finish_run(surrendered=True)
                    return
                elif self.pause_selection == 3:
                    self.state = "menu"
                    self.menu_selection = 0
                return

    def draw_paused(self):
        self._sync_theme()
        self.draw_playing()
        self.ui.draw_pause(self.screen, self.pause_selection)

    # ================================================================
    # GAME OVER
    # ================================================================
    def update_game_over(self, events):
        rects = [result_rect(i) for i in range(2)]
        for hovered, key in menu_inputs(events, rects):
            if hovered is not None:
                self.game_over_selection = hovered
            if key is None:
                continue
            if key == pygame.K_UP:
                self.game_over_selection = (self.game_over_selection - 1) % 2
            elif key == pygame.K_DOWN:
                self.game_over_selection = (self.game_over_selection + 1) % 2
            elif key == pygame.K_RETURN:
                if self.game_over_selection == 0:
                    self.start_new_game()
                elif self.game_over_selection == 1:
                    self.state = "menu"
                    self.menu_selection = 0
                return

    def draw_game_over(self):
        self._sync_theme()
        self.draw_playing()
        self.ui.draw_game_over(
            self.screen, self.player, self.game_time,
            self.game_over_selection, self.new_record_pos, self.surrendered
        )

    # ================================================================
    # ЭКРАН ВЫБОРА УЛУЧШЕНИЙ
    # ================================================================
    def update_upgrading(self, events):
        um = self.upgrade_manager
        rects = [upgrade_rect(i, len(um.choices)) for i in range(len(um.choices))]
        for hovered, key in menu_inputs(events, rects):
            if hovered is not None:
                um.selected_index = hovered
            if key is None:
                continue
            if key == pygame.K_LEFT:
                um.selected_index = (um.selected_index - 1) % len(um.choices)
            elif key == pygame.K_RIGHT:
                um.selected_index = (um.selected_index + 1) % len(um.choices)
            elif key == pygame.K_RETURN:
                self._apply_upgrade_choice(um.selected_index)
                return

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
        self._sync_theme()
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

        # Проверка паузы и ультимейта из событий
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, self.settings_manager.get("bind_pause")):
                    self.state = "paused"
                    self.pause_selection = 0
                    return
                elif event.key == self.settings_manager.get("bind_ultimate"):
                    self.trigger_hero_ult()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.trigger_hero_ult()

        self.game_time += dt

        # Ввод
        keys = pygame.key.get_pressed()
        mouse_pos = self.display.mouse_pos()

        # Обновить игрока
        move_start = self.player.x, self.player.y
        self.player.update(dt, keys, mouse_pos, self.camera)
        self._update_ultimate_cast(dt)
        self._update_slider_ultimate(dt)

        # Ограничить игрока ареной босса
        self.enforce_boss_arena()

        self.ice_trail.update(dt, self.player, move_start)
        if self.player.is_sliding:
            for enemy in self.enemies:
                if enemy.check_slide_escape(self.player, move_start) and not self.player.dodge_charge:
                    self.player.dodge_charge = True
                    self.particle_manager.add_message(t("MSG_PERFECT_DODGE"), CYAN)

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
                if self.settings_manager.get("slide_particles"):
                    self.particle_manager.spawn_slide_particles(
                        self.player.x, self.player.y,
                        self.player.slide_direction_x,
                        self.player.slide_direction_y
                    )

        # Обновить мир (следы, декорации)
        self.world.update(dt)
        # Спавн врагов (во время босса — за пределами арены)
        self.game_messages.clear()
        self.spawner.update(dt, self.player.x, self.player.y,
                           self.enemies, self.game_messages,
                           arena=self.active_boss_arena())

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
        self._update_ultimate_effects(dt)

        # Обновить снаряды врагов
        self.update_explosion_fuses(dt)
        self.update_enemy_projectiles(dt)

        # Некроманты — воскрешение
        self.update_necromancers()

        # ════════════════════════════════════════════
        # ВСЕ ПРОВЕРКИ СТОЛКНОВЕНИЙ
        # ════════════════════════════════════════════
        self.check_fist_attacks()
        self.check_fist_waves()
        self.check_ground_slam()
        self.check_slide_knockback()
        self.check_counter_attack()
        self.check_enemy_attacks(dt)
        self.check_shockwave_damage()
        self.check_electric_trail_damage(dt)

        # XP притягивание от кулаков
        self.check_fist_xp_pull()

        # Обновить XP сферы
        self.update_xp_orbs(dt)

        # Обновить предметы на земле
        self.update_items(dt)

        # Ауры
        self.pulse_auras.update(dt, self.player, self.enemies, self.deal_damage_to_enemy)
        self.apply_aura_damage(dt)
        self.apply_aura_slow(dt)

        # Деспавн далёких объектов
        self.despawn_far_enemies()

        # Очистка старых корпусов
        self.cleanup_corpses()

        # Обновить частицы
        self.particle_manager.update(dt)

        # Улучшения можно забирать даже посреди ульта Слайдера: экран выбора
        # ставит полёт на паузу и возобновляет его после выбора.
        if self.player.pending_levels > 0 and not self.ultimate_cast_pending:
            self.player.pending_levels -= 1
            luck = self.player.stats["luck"]
            hero_id = getattr(self.player, 'hero_id', 'slider')
            self.upgrade_manager.generate_choices(CHOICES_PER_LEVEL, luck, hero_id=hero_id)
            self.state = "upgrading"
            self.particle_manager.spawn_level_up_particles(
                self.player.x, self.player.y
            )
            self.particle_manager.add_message(t("MSG_LEVEL_UP", self.player.level), YELLOW)

        # Run milestones are checked centrally so all catalogue entries have
        # real unlock conditions and thresholds can be extended safely.
        metrics = {
            'kills': self.player.enemies_killed,
            'slides': self.player.total_slides_count,
            'combo': getattr(self.player, 'combo_max_reached', self.player.combo_count),
            'level': self.player.level,
            'time': self.game_time,
            'ult': self.ult_uses_run,
            'bosses': self.bosses_killed_run,
        }
        milestones = {
            'first_kill': ('kills', 1), 'kills_10': ('kills', 10),
            'kills_50': ('kills', 50), 'kills_100': ('kills', 100),
            'kills_500': ('kills', 500), 'kills_1000': ('kills', 1000),
            'slide_10': ('slides', 10), 'slide_master': ('slides', 50),
            'slide_250': ('slides', 250), 'slide_1000': ('slides', 1000),
            'combo_25': ('combo', 25), 'combo_50': ('combo', 50),
            'combo_100': ('combo', 100), 'level_5': ('level', 5),
            'level_10': ('level', 10), 'level_20': ('level', 20),
            'survive_1min': ('time', 60), 'survive_5min': ('time', 300),
            'survive_10min': ('time', 600), 'ult_10': ('ult', 10),
            'ult_25': ('ult', 25), 'boss_5': ('bosses', 5), 'boss_10': ('bosses', 10),
        }
        for achievement, (metric, threshold) in milestones.items():
            if metrics[metric] >= threshold:
                self.achievement_manager.unlock(achievement, self.particle_manager)
        if self.game_time >= 60:
            self.achievement_manager.unlock(f"{self.player.hero_id}_path", self.particle_manager)

        # Проверить смерть игрока
        if not self.player.is_alive():
            self.finish_run()

    def finish_run(self, surrendered=False):
        if self.state == "game_over":
            return
        self.surrendered = surrendered
        self.new_record_pos = add_highscore(self.game_time, self.player.level, self.player.enemies_killed)
        self.state = "game_over"
        self.game_over_selection = 0

    def trigger_hero_ult(self):
        """Start the selected hero's committed, cinematic ultimate wind-up."""
        if self.ultimate_cast_pending or not self.player.can_use_ult():
            return False
        hero_id = self.player.hero_id
        hero = HEROES[hero_id]
        self.ultimate_cast_hero = hero_id
        self.ultimate_cast_duration = hero['ult_cast_time']
        self.ultimate_cast_pending = True
        self.player.ult_charge = 0.0
        self.player.ult_cast_duration = self.ultimate_cast_duration
        self.player.ult_cast_timer = self.ultimate_cast_duration
        # Plant the hero in place immediately; the wind-up is a deliberate risk.
        self.player.is_sliding = False
        self.player.slide_current_speed = 0.0
        self.player.velocity_x = self.player.velocity_y = 0.0
        self.player.fist_attack_active = False
        self.camera.add_shake(2, self.ultimate_cast_duration)
        return True

    def _ring(self, x, y, radius, color, duration=.62):
        self.ultimate_rings.append({'x': x, 'y': y, 'radius': radius,
                                    'age': 0.0, 'duration': duration, 'color': color})

    def _resolve_hero_ult(self, hero_id):
        """Resolve one distinct, hero-specific ultimate at the end of its cast."""
        player = self.player
        x, y = player.x, player.y
        ult_name = t(HEROES[hero_id]['ult_id'] + '_name')
        self.particle_manager.add_message(t('ULT_ACTIVATED', ult_name), self.ui.theme_accent)
        player.resolve_hero_ult(hero_id, self.camera, self.particle_manager)

        if hero_id == 'slider':
            # Automatically ricochet through nearby foes, then return to the
            # exact cast position. Three echo clones scatter in other
            # directions and converge back into the hero on the return.
            radius = 760
            targets = [e for e in self.enemies if e.alive
                       and math.hypot(e.x-x, e.y-y) <= radius + e.size]

            def make_flyer(fx, fy, heading, dmg_mult):
                return {'x': fx, 'y': fy, 'heading': heading, 'dmg_mult': dmg_mult,
                        'target': None, 'visited': set(), 'last_target': None}

            hero_flyer = make_flyer(x, y, player.facing_angle, 1.0)
            clones = []
            for i in range(3):
                # Три клона летят в разные стороны, слайдер — в свою, отличную от них
                heading = player.facing_angle + math.tau * (i + 1) / 4
                clone = make_flyer(x, y, heading, 0.7)
                clone.update({'merged': False, 'scale': 1.0})
                clones.append(clone)
            self.slider_ultimate = {
                'origin': (x, y), 'timer': 2.0, 'returning': False,
                'hero': hero_flyer, 'clones': clones,
            }
            player.ultimate_action_lock = True
            player.is_sliding = False
            player.slide_current_speed = 0.0
            player.velocity_x = player.velocity_y = 0.0
            self._ring(x, y, radius, (96, 231, 226), 1.0)
            if not targets:
                # Keep the cooldown, but refund half of the spent meter.
                player.ult_charge = 50.0

        elif hero_id == 'brawler':
            # Earthquake: radial damage cracks the ground and killed foes become
            # physical ragdolls that can echo-slam into additional enemies.
            radius = 455
            damage = 285 + player.get_fist_damage()*2.5
            crack_radius = radius * 2.5
            self.earthquake_cracks = fracture_lines(
                x, y, int(self.game_time*1000)+int(x+y), radius=crack_radius
            )
            self.earthquake_crack_timer = self.earthquake_crack_duration
            self._ring(x, y, radius, (239, 185, 89), .85)
            for enemy in list(self.enemies):
                if not enemy.alive:
                    continue
                ex, ey = enemy.x, enemy.y
                dx, dy = ex-x, ey-y
                dist = math.hypot(dx, dy)
                if dist > radius + enemy.size:
                    continue
                nx, ny = (dx/dist, dy/dist) if dist else (1, 0)
                killed, actual, _ = self.deal_damage_to_enemy(
                    enemy, damage, knockback_force=650, knockback_dir_x=nx, knockback_dir_y=ny,
                    can_crit=False, can_stun=False, can_lifesteal=False,
                    particle_color=(239, 185, 89), particle_count=18, source='ult'
                )
                if killed:
                    angle = math.atan2(ny, nx) + random.uniform(-.55, .55)
                    speed = random.uniform(560, 920)
                    if len(self.ultimate_bodies) < 48:
                        self.ultimate_bodies.append(CorpseProjectile(
                            ex, ey, math.cos(angle)*speed, math.sin(angle)*speed,
                            enemy.color, enemy.size, 105 + actual*.38
                        ))
                else:
                    enemy.stun_timer = max(getattr(enemy, 'stun_timer', 0), 2.1)

        elif hero_id == 'spark':
            # Chain Storm jumps from target to target and leaves active storm rifts.
            remaining = [e for e in self.enemies if e.alive]
            current = (x, y)
            strikes = []
            for index in range(12):
                candidates = [e for e in remaining
                              if math.dist(current, (e.x, e.y)) <= (620 if index == 0 else 350)]
                if not candidates:
                    break
                target = min(candidates, key=lambda e: math.dist(current, (e.x, e.y)))
                remaining.remove(target)
                point = (target.x, target.y)
                segments = lightning_segments(current, point, int(self.game_time*10000)+index)
                self.lightning_bolts.append({'segments': segments, 'timer': .34, 'duration': .34,
                                             'impact': point})
                self.deal_damage_to_enemy(
                    target, 175 + player.get_fist_damage()*.85,
                    can_crit=False, can_stun=False, can_lifesteal=False,
                    particle_color=(250, 189, 47), particle_count=15, source='ult',
                    magnetize_xp=True
                )
                if target.alive:
                    target.stun_timer = max(getattr(target, 'stun_timer', 0), .65)
                strikes.append(point)
                current = point
            if not strikes:
                # A spectacular cast should still leave a visible footprint in an empty arena.
                for i in range(6):
                    angle = i*math.tau/6 + self.game_time*.4
                    point = (x+math.cos(angle)*210, y+math.sin(angle)*210)
                    segments = lightning_segments((x, y), point, i+int(self.game_time*1000))
                    self.lightning_bolts.append({'segments': segments, 'timer': .34, 'duration': .34,
                                                 'impact': point})
                    strikes.append(point)
            for point in strikes[::2][:6]:
                self.storm_zones.append({'x': point[0], 'y': point[1], 'radius': 84,
                                         'timer': 3.4, 'tick': .2, 'phase': 0.0})
            self._ring(x, y, 310, (250, 189, 47), .65)
            self.spark_storm_timer = self.spark_storm_duration
            self.spark_storm_tick = 0.0
            # Капли дождя живут в мировых координатах: при движении игрока
            # дождь остаётся на месте в мире, а не прилипает к экрану.
            self.rain_drops = [
                [x + random.uniform(-SCREEN_WIDTH * 0.62, SCREEN_WIDTH * 0.62),
                 y + random.uniform(-SCREEN_HEIGHT * 0.62, SCREEN_HEIGHT * 0.62),
                 random.uniform(420, 760), random.uniform(12, 24)]
                for _ in range(150)
            ]

        elif hero_id == 'shadow':
            # Twin blades orbit in opposite directions; the second joins 0.2s later.
            self.shadow_ult_blades = [
                {'angle': 0.0, 'direction': 1, 'delay': 0.0, 'turns': 0.0,
                 'hit_cooldowns': {}},
                {'angle': math.pi, 'direction': -1, 'delay': .2, 'turns': 0.0,
                 'hit_cooldowns': {}},
            ]
            self._ring(x, y, 110, (203, 166, 247), .55)

    def _angle_delta(self, a, b):
        d = a - b
        while d > math.pi:
            d -= math.tau
        while d < -math.pi:
            d += math.tau
        return d

    def _slider_flyer_step(self, f, dt):
        """Одна фигура ульта Слайдера (герой или клон): рикошет по врагам.

        Возвращает True, если рядом не осталось целей."""
        x, y = f['x'], f['y']
        nearby = [e for e in self.enemies if e.alive
                  and math.hypot(e.x-x, e.y-y) <= 820 + e.size]
        target = f['target']
        if target is None or not target.alive:
            candidates = [e for e in nearby if id(e) not in f['visited']]
            if not candidates:
                if nearby:
                    f['visited'].clear()
                    candidates = nearby[:]
                else:
                    return True
            if len(candidates) > 1:
                alternatives = [e for e in candidates if id(e) != f['last_target']]
                if alternatives:
                    candidates = alternatives
            # Каждый летит в свою сторону: предпочитаем цели впереди себя
            forward = [e for e in candidates
                       if abs(self._angle_delta(
                           math.atan2(e.y-y, e.x-x), f['heading'])) <= math.pi/2]
            if forward:
                candidates = forward
            target = random.choice(candidates)
            f['target'] = target

        if target is not None and target.alive:
            start = (x, y)
            dx, dy = target.x-x, target.y-y
            distance = math.hypot(dx, dy)
            travel = min(distance, SLIDER_ULT_SPEED * dt)
            if distance > 1e-6:
                x += dx / distance * travel
                y += dy / distance * travel
                f['heading'] = math.atan2(dy, dx)
            end = (x, y)
            f['x'], f['y'] = x, y
            if travel > 0:
                self.shadow_slashes.append({
                    'segments': lightning_segments(start, end,
                        int(self.game_time*10000)+random.randrange(10000), 4),
                    'timer': .13, 'duration': .13,
                    'color': (96, 231, 226),
                })
                # Hit anything the fast ricochet crosses, with no dash cooldown.
                sx, sy = end[0]-start[0], end[1]-start[1]
                length_sq = sx*sx + sy*sy or 1.0
                crossed = []
                for enemy in nearby:
                    if id(enemy) in f['visited']:
                        continue
                    t = max(0.0, min(1.0,
                        ((enemy.x-start[0])*sx+(enemy.y-start[1])*sy)/length_sq))
                    px, py = start[0]+sx*t, start[1]+sy*t
                    gap = math.hypot(enemy.x-px, enemy.y-py)
                    if gap <= enemy.size + self.player.size + 24:
                        crossed.append((t, enemy))
                for _, enemy in sorted(crossed, key=lambda pair: pair[0]):
                    if not enemy.alive:
                        continue
                    f['visited'].add(id(enemy))
                    f['last_target'] = id(enemy)
                    nx, ny = enemy.x-start[0], enemy.y-start[1]
                    norm = math.hypot(nx, ny) or 1.0
                    self.deal_damage_to_enemy(
                        enemy, (145 + self.player.get_fist_damage()*1.45) * f['dmg_mult'],
                        knockback_force=360, knockback_dir_x=nx/norm,
                        knockback_dir_y=ny/norm, can_crit=False,
                        can_stun=False, can_lifesteal=False,
                        particle_color=(96, 231, 226), particle_count=8, source='ult'
                    )
            if distance <= travel + 2:
                f['visited'].add(id(target))
                f['last_target'] = id(target)
                f['target'] = None
                if f['dmg_mult'] >= 1.0:
                    self.camera.add_shake(4, .08)
        return False

    def _update_slider_ultimate(self, dt):
        state = self.slider_ultimate
        if state is None:
            return
        player = self.player
        hero_flyer = state['hero']
        clones = state['clones']

        if not state['returning']:
            state['timer'] -= dt
            if state['timer'] <= 0:
                state['returning'] = True
            else:
                hero_done = self._slider_flyer_step(hero_flyer, dt)
                player.x, player.y = hero_flyer['x'], hero_flyer['y']
                player.facing_angle = hero_flyer['heading']
                for clone in clones:
                    self._slider_flyer_step(clone, dt)
                if hero_done:
                    # Рядом не осталось целей — вся команда возвращается
                    state['returning'] = True

        if state['returning']:
            ox, oy = state['origin']
            dx, dy = ox-player.x, oy-player.y
            distance = math.hypot(dx, dy)
            travel = min(distance, SLIDER_ULT_SPEED * dt)
            if distance > 1e-6:
                player.x += dx / distance * travel
                player.y += dy / distance * travel
            # Клоны догоняют героя, вжимаются в него и пропадают
            all_merged = True
            for clone in clones:
                if clone.get('merged'):
                    continue
                cdx, cdy = player.x-clone['x'], player.y-clone['y']
                cdist = math.hypot(cdx, cdy)
                ctravel = min(cdist, SLIDER_ULT_SPEED * dt * 1.2)
                if cdist > 1e-6:
                    clone['x'] += cdx / cdist * ctravel
                    clone['y'] += cdy / cdist * ctravel
                    clone['heading'] = math.atan2(cdy, cdx)
                clone['scale'] = max(0.12, min(1.0, cdist / 260.0))
                if cdist <= ctravel + 30:
                    clone['merged'] = True
                    self._ring(clone['x'], clone['y'], 42, (96, 231, 226), .32)
                else:
                    all_merged = False
            if distance <= travel + 1 and all_merged:
                player.x, player.y = ox, oy
                player.velocity_x = player.velocity_y = 0.0
                player.ultimate_action_lock = False
                player.slide_charges = 0
                player.slide_cooldown_timer = player.get_slide_cooldown()
                player.speed_boost_timer = 5.0
                player.speed_boost_multiplier = 1.55
                self.slider_ultimate = None

    def _update_spark_storm(self, dt):
        if self.spark_storm_timer <= 0:
            return
        self.spark_storm_timer = max(0.0, self.spark_storm_timer-dt)
        self.spark_storm_tick -= dt
        # Дождь в мировых координатах: капли падают в мире и не держатся за экраном
        px, py = self.player.x, self.player.y
        for drop in self.rain_drops:
            drop[0] -= 165 * dt
            drop[1] += drop[2] * dt
            if drop[1] > py + SCREEN_HEIGHT * 0.62 or drop[0] < px - SCREEN_WIDTH * 0.62:
                drop[0] = px + random.uniform(-SCREEN_WIDTH * 0.2, SCREEN_WIDTH * 0.72)
                drop[1] = py - random.uniform(SCREEN_HEIGHT * 0.42, SCREEN_HEIGHT * 0.62)
                drop[2] = random.uniform(420, 760)
        if self.spark_storm_tick <= 0:
            self.spark_storm_tick += .42
            targets = [e for e in self.enemies if e.alive
                       and math.hypot(e.x-self.player.x, e.y-self.player.y) <= 580]
            if targets:
                target = random.choice(targets)
                start, end = (self.player.x, self.player.y), (target.x, target.y)
                self.lightning_bolts.append({
                    'segments': lightning_segments(start, end,
                        int(self.game_time*10000)+random.randrange(10000)),
                    'timer': .3, 'duration': .3,
                    'impact': end,
                })
                self.deal_damage_to_enemy(
                    target, 72 + self.player.get_fist_damage()*.45,
                    can_crit=False, can_stun=False, can_lifesteal=False,
                    particle_color=(250, 220, 110), particle_count=8, source='ult',
                    magnetize_xp=True
                )
                if target.alive:
                    target.stun_timer = max(getattr(target, 'stun_timer', 0), .2)

    def _draw_spark_storm_weather(self):
        if self.spark_storm_timer <= 0:
            return
        elapsed = self.spark_storm_duration - self.spark_storm_timer
        fade_in = min(1.0, elapsed / .8)
        fade_out = min(1.0, self.spark_storm_timer / 1.4)
        intensity = min(fade_in, fade_out)
        overlay = self.storm_overlay_surface
        overlay.fill((4, 7, 15, int(226 * intensity)))
        self.screen.blit(overlay, (0, 0))
        rain_color = (int(55+95*intensity), int(70+107*intensity),
                      int(88+117*intensity))
        for x, y, speed, length in self.rain_drops:
            # Long, near-vertical streaks with a slight wind slant read clearly as rain.
            # Капли в мировых координатах — рисуем через камеру.
            sx, sy = self.camera.apply(x, y)
            if sx < -30 or sx > SCREEN_WIDTH + 30 or sy < -40 or sy > SCREEN_HEIGHT + 40:
                continue
            pygame.draw.line(self.screen, rain_color,
                             (int(sx), int(sy)), (int(sx-3), int(sy+length)), 1)

    def _draw_spark_player_glow(self):
        """Игрок светится во время ульта Спарка."""
        casting = self.player.ult_cast_timer > 0 and self.player.hero_id == 'spark'
        if self.spark_storm_timer <= 0 and not casting:
            return
        sx, sy = self.camera.apply(self.player.x, self.player.y)
        pulse = .5 + .5 * math.sin(self.game_time * 6.0)
        glow = self.spark_glow_surface
        glow.fill((0, 0, 0, 0))
        cx = cy = glow.get_width() // 2
        for radius, alpha in ((104, 26), (82, 40), (60, 62), (40, 92)):
            r = int(radius * (0.86 + 0.14 * pulse))
            pygame.draw.circle(glow, (255, 220, 90, alpha), (cx, cy), r)
        self.screen.blit(glow, (sx - cx, sy - cy))

    def _update_shadow_ult_blades(self, dt):
        if not self.shadow_ult_blades:
            return
        speed = math.tau * 2.5  # Four complete turns in 1.6 seconds.
        for blade in self.shadow_ult_blades:
            blade['delay'] = max(0.0, blade['delay']-dt)
            if blade['delay'] > 0 or blade['turns'] >= 4.0:
                continue
            delta = min(speed*dt, (4.0-blade['turns'])*math.tau)
            blade['angle'] += blade['direction'] * delta
            blade['turns'] += delta/math.tau
            if blade['turns'] >= 4.0 - 1e-8:
                blade['turns'] = 4.0
            for enemy_id in list(blade['hit_cooldowns']):
                blade['hit_cooldowns'][enemy_id] -= dt
                if blade['hit_cooldowns'][enemy_id] <= 0:
                    del blade['hit_cooldowns'][enemy_id]
            axis_x, axis_y = math.cos(blade['angle']), math.sin(blade['angle'])
            start = (self.player.x + axis_x*36, self.player.y + axis_y*36)
            end = (self.player.x + axis_x*158, self.player.y + axis_y*158)
            blade_x, blade_y = end[0]-start[0], end[1]-start[1]
            blade_length_sq = blade_x*blade_x + blade_y*blade_y
            for enemy in self.enemies:
                if not enemy.alive or id(enemy) in blade['hit_cooldowns']:
                    continue
                along = max(0.0, min(1.0,
                    ((enemy.x-start[0])*blade_x+(enemy.y-start[1])*blade_y)
                    / blade_length_sq))
                closest_x = start[0] + blade_x*along
                closest_y = start[1] + blade_y*along
                if math.hypot(enemy.x-closest_x, enemy.y-closest_y) > enemy.size+13:
                    continue
                damage = self.player.get_fist_damage()*1.8
                self.deal_damage_to_enemy(
                    enemy, damage, can_crit=False, can_stun=False,
                    can_lifesteal=False, particle_color=(203, 166, 247),
                    particle_count=7, source='ult'
                )
                healed = self.player.lifesteal(damage)
                if healed > .5:
                    self.particle_manager.spawn_heal_particles(
                        self.player.x, self.player.y, count=3
                    )
                blade['hit_cooldowns'][id(enemy)] = .22
        if all(blade['turns'] >= 4.0 for blade in self.shadow_ult_blades):
            self.shadow_ult_blades.clear()

    def _update_ultimate_cast(self, dt):
        if self.ultimate_cast_pending:
            progress = 1.0 - self.player.ult_cast_timer / self.ultimate_cast_duration
            self.ult_zoom_strength = math.sin(max(0.0, min(1.0, progress)) * math.pi / 2)
            if self.player.ult_cast_timer <= 0:
                hero_id = self.ultimate_cast_hero
                self.ultimate_cast_pending = False
                self.ultimate_cast_hero = None
                # Lock charge before resolving impacts: kills caused by the
                # ultimate itself must not refill the meter during cooldown.
                self.player.ult_cooldown_timer = 10.0
                self._resolve_hero_ult(hero_id)
                self.ult_afterglow_timer = .9
                self.ult_zoom_strength = 1.0
                self.ult_uses_run += 1
                self.achievement_manager.unlock('ult_used', self.particle_manager)
            return
        if self.ult_afterglow_timer > 0:
            self.ult_afterglow_timer = max(0.0, self.ult_afterglow_timer - dt)
            self.ult_zoom_strength = math.sin(
                (self.ult_afterglow_timer / .9) * math.pi / 2
            )
        else:
            self.ult_zoom_strength = 0.0

    def _update_ultimate_effects(self, dt):
        for ring in self.ultimate_rings:
            ring['age'] += dt
        self.ultimate_rings = [r for r in self.ultimate_rings if r['age'] < r['duration']]
        for bolt in self.lightning_bolts:
            bolt['timer'] -= dt
        self.lightning_bolts = [b for b in self.lightning_bolts if b['timer'] > 0]
        for slash in self.shadow_slashes:
            slash['timer'] -= dt
        self.shadow_slashes = [s for s in self.shadow_slashes if s['timer'] > 0]
        self.earthquake_crack_timer = max(0.0, self.earthquake_crack_timer-dt)
        self._update_spark_storm(dt)
        self._update_shadow_ult_blades(dt)

        for zone in self.storm_zones:
            zone['timer'] -= dt
            zone['tick'] -= dt
            zone['phase'] += dt
            if zone['tick'] <= 0:
                zone['tick'] += .45
                for enemy in list(self.enemies):
                    if not enemy.alive:
                        continue
                    if math.hypot(enemy.x-zone['x'], enemy.y-zone['y']) <= zone['radius']+enemy.size:
                        self.deal_damage_to_enemy(
                            enemy, 46, can_crit=False, can_stun=False, can_lifesteal=False,
                            particle_color=(250, 189, 47), particle_count=4, source='ult',
                            magnetize_xp=True
                        )
                        if enemy.alive:
                            enemy.stun_timer = max(getattr(enemy, 'stun_timer', 0), .12)
        self.storm_zones = [z for z in self.storm_zones if z['timer'] > 0]

        for body in self.ultimate_bodies:
            body.update(dt)
            if not body.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive or id(enemy) in body.hit_targets:
                    continue
                if math.hypot(enemy.x-body.x, enemy.y-body.y) > body.radius+enemy.size:
                    continue
                body.hit_targets.add(id(enemy))
                body.hits_left -= 1
                speed = math.hypot(body.vx, body.vy) or 1
                nx, ny = body.vx/speed, body.vy/speed
                self.deal_damage_to_enemy(
                    enemy, body.damage, knockback_force=270,
                    knockback_dir_x=nx, knockback_dir_y=ny,
                    can_crit=False, can_stun=False, can_lifesteal=False,
                    particle_color=body.color, particle_count=12, source='ult'
                )
                if enemy.alive:
                    enemy.stun_timer = max(getattr(enemy, 'stun_timer', 0), .34)
                self.camera.add_shake(5, .12)
                break
            if body.hits_left <= 0:
                body.alive = False
        self.ultimate_bodies = [b for b in self.ultimate_bodies if b.alive]

    def _draw_ultimate_world_effects(self):
        if self.earthquake_crack_timer > 0:
            # Stay nearly black for most of 15 seconds, then fade smoothly.
            fade_start = 3.0
            fade = min(1.0, self.earthquake_crack_timer / fade_start)
            alpha = int(235 * fade)
            overlay = self.crack_overlay_surface
            overlay.fill((0, 0, 0, 0))
            for start, end in self.earthquake_cracks:
                a = self.camera.apply(*start)
                b = self.camera.apply(*end)
                pygame.draw.line(overlay, (8, 7, 9, alpha), a, b, 7)
                pygame.draw.line(overlay, (24, 18, 19, int(170*fade)), a, b, 3)
            self.screen.blit(overlay, (0, 0))
        for ring in self.ultimate_rings:
            progress = min(1.0, ring['age']/ring['duration'])
            radius = max(2, int(ring['radius']*progress))
            center = self.camera.apply(ring['x'], ring['y'])
            pygame.draw.circle(self.screen, ring['color'], center, radius, max(2, int(5*(1-progress))))
        for zone in self.storm_zones:
            center = self.camera.apply(zone['x'], zone['y'])
            pulse = .82 + .18*math.sin(zone['phase']*12)
            radius = int(zone['radius']*pulse)
            pygame.draw.circle(self.screen, (116, 85, 35), center, radius, 6)
            pygame.draw.circle(self.screen, (250, 189, 47), center, radius-5, 2)
            pygame.draw.circle(self.screen, (226, 168, 50), center, max(4, radius//4), 1)
        # Эхо-клоны ульта Слайдера
        state = self.slider_ultimate
        if state:
            for clone in state['clones']:
                if clone.get('merged'):
                    continue
                scale = clone.get('scale', 1.0)
                cx_, cy_ = self.camera.apply(clone['x'], clone['y'])
                cx_, cy_ = int(cx_), int(cy_)
                radius = max(3, int(self.player.size * 0.9 * scale))
                trail = 26 + radius
                pygame.draw.line(self.screen, (72, 178, 176), (cx_, cy_),
                                 self.camera.apply(clone['x'] - math.cos(clone['heading']) * trail,
                                                   clone['y'] - math.sin(clone['heading']) * trail), 2)
                pygame.draw.circle(self.screen, (18, 60, 66), (cx_, cy_), radius + 3)
                pygame.draw.circle(self.screen, (96, 231, 226), (cx_, cy_), radius)
                pygame.draw.circle(self.screen, (235, 255, 255), (cx_, cy_),
                                   max(2, radius // 2), 2)
        for effects, base in ((self.lightning_bolts, (250, 224, 127)),
                              (self.shadow_slashes, (203, 166, 247))):
            for effect in effects:
                ratio = effect['timer']/effect['duration']
                tint = tuple(int(c*ratio) for c in effect.get('color', base))
                for start, end in effect['segments']:
                    pygame.draw.line(self.screen, (28, 25, 30), self.camera.apply(*start), self.camera.apply(*end), 6)
                    pygame.draw.line(self.screen, tint, self.camera.apply(*start), self.camera.apply(*end), 3)
                # Область удара молнии подсвечивается
                impact = effect.get('impact')
                if impact:
                    ix, iy = self.camera.apply(*impact)
                    radius = int(16 + 26 * (1 - ratio))
                    glow = tuple(min(255, int(c * (0.3 + 0.7 * ratio)))
                                 for c in (255, 236, 140))
                    pygame.draw.circle(self.screen, glow, (int(ix), int(iy)), radius, 3)
                    pygame.draw.circle(self.screen, (255, 250, 220), (int(ix), int(iy)),
                                       max(2, radius // 3))
        for blade in self.shadow_ult_blades:
            if blade['delay'] > 0 or blade['turns'] >= 4.0:
                continue
            axis_x, axis_y = math.cos(blade['angle']), math.sin(blade['angle'])
            side_x, side_y = -axis_y, axis_x
            origin_x, origin_y = self.player.x, self.player.y

            def blade_point(radius, width):
                return self.camera.apply(origin_x + axis_x*radius + side_x*width,
                                         origin_y + axis_y*radius + side_y*width)

            silhouette = [blade_point(34, -10), blade_point(106, -14),
                          blade_point(158, 0), blade_point(106, 14),
                          blade_point(34, 10)]
            inner = [blade_point(42, -5), blade_point(106, -8),
                     blade_point(148, 0), blade_point(106, 8),
                     blade_point(42, 5)]
            pygame.draw.polygon(self.screen, (39, 20, 53), silhouette)
            pygame.draw.polygon(self.screen, (157, 112, 220), inner)
            pygame.draw.line(self.screen, (244, 231, 255),
                             blade_point(42, 0), blade_point(148, 0), 2)
            pygame.draw.line(self.screen, (221, 190, 255),
                             blade_point(48, -5), blade_point(106, -8), 2)
        for body in self.ultimate_bodies:
            body.draw(self.screen, self.camera)

    def _apply_ultimate_camera_effect(self):
        strength = max(0.0, min(1.0, self.ult_zoom_strength))
        if strength <= 0:
            return
        zoom = 1.0 + .115*strength
        width, height = round(SCREEN_WIDTH*zoom), round(SCREEN_HEIGHT*zoom)
        frame = pygame.transform.smoothscale(self.screen.copy(), (width, height))
        focus_x, focus_y = self.camera.apply(self.player.x, self.player.y)
        self.screen.fill(BLACK)
        self.screen.blit(frame, (round(focus_x*(1-zoom)), round(focus_y*(1-zoom))))

    def _draw_ultimate_vignette(self):
        strength = max(0.0, min(1.0, self.ult_zoom_strength))
        if strength <= .01:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        hero_colors = {'spark': (24, 18, 7), 'shadow': (17, 10, 27),
                       'brawler': (28, 11, 8), 'slider': (7, 20, 23)}
        color = hero_colors.get(self.player.hero_id, (8, 12, 20))
        max_alpha = int(135*strength)
        for band in range(10):
            inset_x, inset_y = band*24, band*16
            alpha = int(max_alpha*((10-band)/10)**1.65)
            if alpha <= 0:
                continue
            pygame.draw.rect(overlay, (*color, alpha), (inset_x, inset_y, SCREEN_WIDTH-2*inset_x, 18))
            pygame.draw.rect(overlay, (*color, alpha), (inset_x, SCREEN_HEIGHT-inset_y-18, SCREEN_WIDTH-2*inset_x, 18))
            pygame.draw.rect(overlay, (*color, alpha), (inset_x, inset_y, 18, SCREEN_HEIGHT-2*inset_y))
            pygame.draw.rect(overlay, (*color, alpha), (SCREEN_WIDTH-inset_x-18, inset_y, 18, SCREEN_HEIGHT-2*inset_y))
        self.screen.blit(overlay, (0, 0))

    # ================================================================
    # БОСС-АРЕНА
    # ================================================================
    def enforce_boss_arena(self):
        """Не дать игроку выйти за пределы арены босса.

        Враги при этом ходят свободно: монстры появляются за ареной
        и могут спокойно вступать на неё."""
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

    def active_boss_arena(self):
        """Активная арена босса (центр и радиус) или None."""
        for boss in self.enemies:
            if (getattr(boss, 'is_boss', False) and boss.alive
                    and getattr(boss, 'arena_active', False)):
                return (boss.arena_center_x, boss.arena_center_y, BOSS_ARENA_RADIUS)
        return None

    # ================================================================
    # ОБНОВЛЕНИЕ ВРАГОВ
    # ================================================================
    def check_habitat(self, enemy):
        if enemy.home_biome and self.world.biome_at(enemy.x, enemy.y).key != enemy.home_biome:
            # Environmental removal: no kill callbacks, corpse, fuse, combo or loot.
            enemy.alive = False
            enemy.hp = 0
            self.habitat_fades.append(HabitatFade(enemy))
            self.habitat_fades = self.habitat_fades[-128:]
            return False
        return True

    def update_enemies(self, dt):
        """Обновить всех врагов"""
        self.habitat_fades = [effect for effect in self.habitat_fades if effect.update(dt)]
        neighbors = EnemyGrid(self.enemies)
        for enemy in self.enemies:
            if not enemy.alive or not self.check_habitat(enemy):
                continue

            # Стан — враг не двигается и не атакует
            if getattr(enemy, 'stun_timer', 0) > 0:
                enemy.windup_left = 0.0
                enemy.stun_timer -= dt
                enemy.velocity_x = 0
                enemy.velocity_y = 0
                enemy.walk_frame = 0
                # Визуал мигания при стане
                if int(enemy.stun_timer * 8) % 2 == 0:
                    enemy.flash_timer = 0.05
                continue

            enemy.on_ice = bool(self.ice_trail.patches) and self.ice_trail.covers(enemy)
            enemy.update(dt, self.player.x, self.player.y, neighbors)
            neighbors.update(enemy)
            self.check_habitat(enemy)

        # Удалить мёртвых
        self.enemies = [e for e in self.enemies if e.alive]

    def spawn_enemy_projectile(self, enemy):
        for offset in enemy.shot_offsets:
            angle = enemy.aim_angle + offset
            self.enemy_projectiles.append(EnemyProjectile(
                enemy.x, enemy.y, math.cos(angle), math.sin(angle),
                enemy.shoot_speed, enemy.damage
            ))

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
        level = self.player.stats["stasis_aura"]
        for proj in self.enemy_projectiles:
            inside = level and math.hypot(proj.x-self.player.x, proj.y-self.player.y) <= STASIS_RADIUS
            proj.update(dt, max(0.25, 1 - level * 0.2) if inside else 1.0)

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
                              source="fist", magnetize_xp=False):
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
                    self.particle_manager.emit(
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
            # Врождённая пассивка Слайдера: убийство скольжением лечит
            if source in ("slide", "shockwave") and self.player.hero_id == "slider":
                self.player.heal(SLIDER_PASSIVE_SLIDE_KILL_HEAL)
                self.particle_manager.spawn_heal_particles(
                    self.player.x, self.player.y, count=3
                )
            self.on_enemy_killed(enemy, magnetize_xp=magnetize_xp)

        return killed, damage, is_crit

    # ================================================================
    # АТАКА КУЛАКАМИ
    # ================================================================
    def check_fist_attacks(self):
        """Проверить попадания кулаков по врагам"""
        attack = self.player.get_fist_attack_area()
        if attack is None:
            return

        attack_x = attack["x"]
        attack_y = attack["y"]
        attack_range = attack["range"]
        attack_angle = attack["angle"]
        attack_arc = attack["arc"]
        base_damage = attack["damage"]
        # Прорубающий удар бьёт всех вокруг, но слабее обычного
        if attack["cleave"]:
            base_damage *= CLEAVE_DAMAGE_MULTIPLIER
        knockback = attack["knockback"]
        is_finisher = attack["is_finisher"]
        is_mega = attack.get("is_mega", False)

        # Количество целей
        max_targets = 1 + self.player.stats["target_count"]
        if is_finisher:
            max_targets += 3  # финальный удар бьёт больше
        if is_mega:
            max_targets += 5  # мега-удар бьёт ещё больше

        targets_hit = len(self.player.fist_hit_enemies)

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy in self.player.fist_hit_enemies:
                continue
            if not attack["cleave"] and targets_hit >= max_targets:
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

            self.player.record_fist_contact(enemy)
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
        if self.player.slam_triggered or not self.player.fist_hit_enemies:
            return
        self.player.slam_triggered = True

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
            self.particle_manager.emit(particle)

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
            # Один враг получает урон от одного скольжения не чаще раза в SLIDE_HIT_COOLDOWN
            if self.player.slide_hit_timers.get(id(enemy), 0) > 0:
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
            self.player.slide_hit_timers[id(enemy)] = SLIDE_HIT_COOLDOWN

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
                        self.particle_manager.emit(
                            Particle(
                                enemy.x, enemy.y,
                                random.uniform(-80, 80),
                                random.uniform(-80, 80),
                                (100, 200, 255), 0.2, 2
                            )
                        )

                    if killed:
                        self.on_enemy_killed(enemy, magnetize_xp=True)

    # ================================================================
    # КОНТАКТНЫЙ УРОН ВРАГОВ
    # ================================================================
    def check_enemy_attacks(self, dt):
        for enemy in self.enemies:
            impact = enemy.advance_attack(dt, self.player)
            if impact == "shot":
                self.spawn_enemy_projectile(enemy)
            elif impact == "hit":
                thorns_damage = self.player.take_damage(enemy.damage)

                # Шипы — ответный урон
                if thorns_damage > 0:
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
    def on_enemy_killed(self, enemy, magnetize_xp=False):
        """Обработка убийства врага"""
        # Врождённая пассивка Спарка: шанс примагнить опыт и предмет с убийства
        if not magnetize_xp and self.player.hero_id == "spark":
            magnetize_xp = random.random() * 100 < SPARK_PASSIVE_MAGNET_CHANCE
        self.player.enemies_killed += 1
        self.player.add_combo()
        self.player.gain_ult_charge(3.0 + self.player.stats["ult_per_kill"])

        # Частицы смерти
        death_particles = 15
        if getattr(enemy, 'is_boss', False):
            self.bosses_killed_run += 1
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

        # Выпадение опыта (умершие от молнии магнитят опыт к игроку)
        xp_orb = XPOrb(enemy.x, enemy.y, enemy.xp_reward)
        if magnetize_xp:
            xp_orb.being_collected = True
        self.xp_orbs.append(xp_orb)

        # Шанс сброса КД скольжения
        self.player.try_reset_slide_cooldown()

        # Шанс дропа предмета
        drop_bonus = self.player.stats["drop_chance"]
        item_type = roll_drop(drop_bonus)
        if item_type:
            item = DroppedItem(enemy.x, enemy.y, item_type)
            if magnetize_xp:
                item.pulled = True
            self.dropped_items.append(item)

        # Взрывник — взрыв при смерти
        if getattr(enemy, 'should_explode', False):
            self.pending_explosions.append((enemy, EXPLOSION_FUSE))

        # Сохранить корпус для некроманта
        if not getattr(enemy, 'is_boss', False):
            self.corpse_positions.append((
                enemy.x, enemy.y,
                enemy.enemy_type,
                self.game_time
            ))

    def update_explosion_fuses(self, dt):
        pending, self.pending_explosions = self.pending_explosions, []
        for enemy, remaining in pending:
            if remaining <= dt:
                self.handle_explosion(enemy)
            else:
                self.pending_explosions.append((enemy, remaining - dt))

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
            result = item.update(dt, self.player.x, self.player.y,
                                 pull=self.slider_ultimate is not None)
            if result:
                self.apply_item_effect(result)

        self.dropped_items = [i for i in self.dropped_items if i.alive]

    def apply_item_effect(self, item_type):
        """Применить эффект подобранного предмета"""
        if item_type in TONICS:
            tonic = TONICS[item_type]
            # Врождённая пассивка Шэдоу: временные улучшения длятся дольше
            self.player.tonic_timers[item_type] = tonic.seconds + self.player.temp_duration_bonus()
            self.particle_manager.add_message(t('TONIC_' + item_type, tonic.bonus, tonic.seconds), tonic.color)
        elif item_type == "heal":
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
            message = t("MSG_BOMB", killed_count)
            if self.player.extend_active_combo(BOMB_COMBO_EXTENSION):
                message += " " + t("MSG_COMBO_EXTENDED", int(BOMB_COMBO_EXTENSION))
            # Каждое убийство бомбой даёт очки комбо
            for _ in range(killed_count):
                self.player.add_combo()
            self.particle_manager.add_message(message, RED)
            self.camera.add_shake(SHAKE_BOMB)

        elif item_type == "speed_boost":
            # Врождённая пассивка Шэдоу: временные улучшения длятся дольше
            self.player.speed_boost_timer = (SPEED_BOOST_DURATION
                                             + self.player.stats["boost_duration"]
                                             + self.player.temp_duration_bonus())
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
        # Во время босса ориентируемся на центр арены: монстры появляются
        # за её пределами и не должны исчезать сразу после спавна.
        arena = self.active_boss_arena()
        if arena is not None:
            ref_x, ref_y, _ = arena
            limit = BOSS_ARENA_RADIUS + 700
        else:
            ref_x, ref_y = self.player.x, self.player.y
            limit = ENEMY_DESPAWN_RADIUS

        new_enemies = []
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            # Боссы НЕ деспавнятся!
            if getattr(enemy, 'no_despawn', False):
                new_enemies.append(enemy)
                continue

            dx = enemy.x - ref_x
            dy = enemy.y - ref_y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= limit:
                new_enemies.append(enemy)

        self.enemies = new_enemies

        # Деспавн далёких XP сфер
        new_orbs = []
        for orb in self.xp_orbs:
            if orb.being_collected:
                new_orbs.append(orb)
                continue
            dx = orb.x - ref_x
            dy = orb.y - ref_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < limit + 200:
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
    def visible(self, obj):
        if not self.settings_manager.get('view_culling'):
            return True
        x, y = self.camera.apply(obj.x, obj.y)
        margin = max(160, getattr(obj, 'size', 0)*4)
        return -margin <= x <= SCREEN_WIDTH+margin and -margin <= y <= SCREEN_HEIGHT+margin

    def draw_playing(self):
        """Нарисовать весь игровой мир"""
        self._sync_theme()
        self.screen.fill(BLACK)

        # Мир (фон, тайлы, декорации, следы)
        self.world.draw(self.screen, self.camera, self.game_time, self.settings_manager)

        # Корпусы (крестики на земле)
        self.draw_corpses()

        # Арена босса (под объектами)
        for boss in self.active_bosses:
            if hasattr(boss, 'draw_arena'):
                boss.draw_arena(self.screen, self.camera)

        # Ауры игрока
        self.ice_trail.draw(self.screen, self.camera)
        self.draw_auras()
        self.pulse_auras.draw(self.screen, self.camera, self.player, self.game_time)

        # XP сферы
        for orb in self.xp_orbs:
            if self.visible(orb):
                orb.draw(self.screen, self.camera)

        # Предметы
        for item in self.dropped_items:
            if self.visible(item):
                item.draw(self.screen, self.camera)

        # Стан-эффект над врагами (под спрайтами врагов)
        for enemy in self.enemies:
            if getattr(enemy, 'stun_timer', 0) > 0:
                self.draw_stun_effect(enemy)

        for source, remaining in self.pending_explosions:
            center = self.camera.apply(source.x, source.y)
            pygame.draw.circle(self.screen, ORANGE, center, source.explode_radius, 2)
            pygame.draw.circle(self.screen, RED, center,
                               int(source.explode_radius * (1 - remaining / EXPLOSION_FUSE)), 3)
        for enemy in self.enemies:
            enemy.draw_windup(self.screen, self.camera)

        # Враги
        for enemy in self.enemies:
            if self.visible(enemy):
                enemy.draw(self.screen, self.camera)

        # Visual-only environmental deaths are never combat entities.
        for effect in self.habitat_fades:
            if self.visible(effect):
                effect.draw(self.screen, self.camera)

        # Снаряды врагов
        for proj in self.enemy_projectiles:
            if self.visible(proj):
                proj.draw(self.screen, self.camera)

        # Render-only culling: entities continue updating off-screen.
        # Игрок
        self.player.draw(self.screen, self.camera)
        self._draw_spark_storm_weather()
        self._draw_spark_player_glow()
        self._draw_ultimate_world_effects()

        # Частицы и числа урона
        self.particle_manager.draw(
            self.screen, self.camera,
            self.ui.font_small, self.ui.font
        )

        if self.settings_manager.get('crosshair'):
            x, y = self.display.mouse_pos()
            pygame.draw.circle(self.screen, WHITE, (x, y), 7, 1)
            pygame.draw.line(self.screen, self.ui.theme_accent, (x-11, y), (x-4, y), 1)
            pygame.draw.line(self.screen, self.ui.theme_accent, (x+4, y), (x+11, y), 1)

        # Keep HUD, minimap, and notification frame fixed while the world
        # layer breathes in around the player during the cinematic.
        self._apply_ultimate_camera_effect()

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
                self.dropped_items, bosses_alive, self.world, self.game_time
            )

        # Вспышка экрана (поверх всего)
        if self.settings_manager.get("screen_flashes"):
            self.camera.draw_flash(self.screen)
        self._draw_ultimate_vignette()

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
    import argparse
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument('--seed', type=int, help='Reproduce world terrain with this seed')
    try:
        game = Game(world_seed=parser.parse_args().seed)
        game.run()
    except KeyboardInterrupt:
        pygame.quit()