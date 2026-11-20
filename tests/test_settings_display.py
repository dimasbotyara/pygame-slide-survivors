"""Settings persistence, scaled input, runtime effects and frozen radar regressions."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from main import Game
from particles import ParticleManager
from preferences import TABS
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from settings_manager import SettingsManager
from translations import set_language, t
from heroes import HEROES
from ui import settings_rect, settings_tab_rect


def press(key, **kwargs):
    return pygame.event.Event(pygame.KEYDOWN, key=key, **kwargs)


class SettingsDisplayTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.file = Path(self.folder.name)/'settings.json'
        settings_patch = patch('settings_manager.SETTINGS_FILE', self.file)
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        self.game = Game(world_seed=42)
        self.addCleanup(set_language, 'ru')

    def test_resize_letterboxing_and_mapped_click(self):
        g = self.game
        g.prepare_events([pygame.event.Event(pygame.VIDEORESIZE, w=1000, h=800)])
        self.assertEqual(g.display.window.get_size(), (1000, 800))
        self.assertGreater(g.display.viewport.y, 0)
        self.assertEqual(g.display.logical_pos(g.display.viewport.center), (640, 360))
        logical = settings_tab_rect(2).center
        r = g.display.viewport
        physical = (r.x+logical[0]*r.w/SCREEN_WIDTH, r.y+logical[1]*r.h/SCREEN_HEIGHT)
        events = g.prepare_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=physical)])
        g.update_settings(events)
        self.assertEqual(g.settings_tab, 2)
        self.assertEqual(g.screen.get_size(), (1280, 720))
        self.assertEqual(SettingsManager().get('resolution'), (1000, 800))
        g.present()

    def test_resolution_fullscreen_and_keyboard_shortcut(self):
        g = self.game
        g.settings_tab, g.settings_selection = 0, 1
        with patch.object(g.display, 'apply') as apply:
            g.update_settings([press(pygame.K_RIGHT)])
            self.assertEqual(g.settings_manager.get('resolution'), (1600, 900))
            apply.assert_called_once()
        with patch.object(g.display, 'apply') as apply:
            events = g.prepare_events([press(pygame.K_RETURN, mod=pygame.KMOD_ALT)])
            self.assertFalse(events)
            self.assertTrue(g.settings_manager.get('fullscreen'))
            apply.assert_called_once()

    def test_display_failure_has_safe_fallback(self):
        g = self.game
        g.settings_manager.set('fullscreen', True)
        window = g.display.window
        with patch('pygame.display.set_mode', side_effect=[pygame.error('unsupported'), window]):
            g.display.apply()
        self.assertFalse(g.settings_manager.get('fullscreen'))
        self.assertEqual(g.settings_manager.get('resolution'), (1280, 720))
        self.assertTrue(g.display.error)

    def test_focus_loss_pauses_but_does_not_resume_automatically(self):
        g = self.game
        g.start_new_game()
        g.prepare_events([pygame.event.Event(pygame.WINDOWFOCUSLOST)])
        self.assertEqual(g.state, 'paused')
        g.prepare_events([pygame.event.Event(pygame.WINDOWFOCUSGAINED)])
        self.assertEqual(g.state, 'paused')

    def test_settings_validation_and_migration(self):
        self.file.write_text(json.dumps({'language': 'en', 'screen_shake': False,
                                       'fps_limit': -1, 'resolution': [0, 'bad'],
                                       'particle_density': 'huge', 'minimap': 'no'}))
        cfg = SettingsManager()
        self.assertEqual(cfg.get('language'), 'en')
        self.assertFalse(cfg.get('screen_shake'))
        self.assertEqual(cfg.get('fps_limit'), 60)
        self.assertEqual(cfg.get('resolution'), (1280, 720))
        self.assertEqual(cfg.get('particle_density'), 2)
        self.assertTrue(cfg.get('minimap'))
        self.assertTrue(cfg.get('minimap_biomes'))

    def test_every_tab_is_translated_renders_and_changes_only_selected_option(self):
        g = self.game
        for lang in ('ru', 'en'):
            set_language(lang)
            for tab, (name, rows) in enumerate(TABS):
                g.settings_tab = tab
                self.assertNotEqual(t('TAB_'+name), 'TAB_'+name)
                g.draw_settings()
                for i, (key, choices) in enumerate(rows):
                    self.assertNotEqual(t('OPT_'+key), 'OPT_'+key)
                    if key in ('resolution', 'fullscreen'):
                        continue
                    g.settings_selection = i
                    before = dict(g.settings_manager.settings)
                    g.update_settings([press(pygame.K_RIGHT)])
                    self.assertNotEqual(g.settings_manager.get(key), before[key])
                    for other in before:
                        if other != key:
                            self.assertEqual(g.settings_manager.get(other), before[other])
            self.assertLess(settings_rect(7).bottom, 620)

    def test_particle_density_budget_disable_and_notification_queue(self):
        pm = ParticleManager()
        pm.density = 1
        pm.spawn_hit_particles(0, 0, count=10)
        self.assertEqual(len(pm.particles), 10)
        pm.particles.clear()
        pm.density = 3
        pm.spawn_hit_particles(0, 0, count=10)
        self.assertEqual(len(pm.particles), 30)
        pm.budget = 35
        pm.spawn_bomb_particles(0, 0, count=1000)
        self.assertEqual(len(pm.particles), 35)
        pm.particles.clear()
        pm.density = 0
        pm.spawn_slide_particles(0, 0, 1, 0)
        self.assertFalse(pm.particles)
        for i in range(10):
            pm.add_message(str(i))
        self.assertEqual(len(pm.messages), 4)
        pm.add_message('9')
        self.assertEqual(len(pm.messages), 4)
        pm.notifications_enabled = False
        pm.add_message('not shown')
        self.assertEqual(len(pm.messages), 4)

    def test_runtime_settings_camera_and_particle_switches(self):
        g = self.game
        g.start_new_game()
        g.settings_manager.settings.update(camera_smoothing=0, camera_lookahead=0, view_culling=False,
                                           particle_density=0, notifications=False, damage_numbers=False)
        g.apply_runtime_settings()
        self.assertEqual(g.camera.lerp_speed, 0)
        self.assertEqual(g.camera.look_ahead_distance, 0)
        self.assertFalse(g.camera.culling_enabled)
        self.assertEqual(g.particle_manager.density, 0)
        self.assertFalse(g.particle_manager.notifications_enabled)
        self.assertFalse(g.particle_manager.damage_numbers_enabled)

    def test_minimap_only_advances_with_game_time(self):
        g = self.game
        g.start_new_game()
        def radar(ticks, game_time):
            g.screen.fill('black')
            with patch('pygame.time.get_ticks', return_value=ticks):
                g.ui.draw_minimap(g.screen, g.player, [], [], [], False, g.world, game_time)
            return pygame.image.tostring(g.screen, 'RGB')
        a = radar(1000, 3)
        self.assertEqual(a, radar(9000, 3))
        self.assertNotEqual(a, radar(9000, 3.5))

    def test_biome_entry_only_names_the_biome(self):
        g = self.game
        g.start_new_game()
        g.update_playing(.01, [])
        biome_name = t('BIOME_'+g.world.biome_at(g.player.x, g.player.y).key)
        self.assertIn(biome_name, [m.text for m in g.particle_manager.messages])
        g.particle_manager.messages.clear()
        g.biome_key = None
        g.settings_manager.settings['biome_notifications'] = False
        g.update_playing(.01, [])
        self.assertNotIn(biome_name, [m.text for m in g.particle_manager.messages])

    def test_ultimate_text_fits_bar_for_every_hero_and_language(self):
        for lang in ('ru', 'en'):
            set_language(lang)
            for hero in HEROES.values():
                text = t(hero['ult_id']+'_name')+': 99%'
                rendered = self.game.ui.fitted_text(text, 'white', 152, 12, 13)
                self.assertLessEqual(rendered.get_width(), 152)
                self.assertLessEqual(rendered.get_height(), 12)
