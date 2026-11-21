"""Hero transitions remain available on low menu settings; dash HUD stays quiet."""
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
from settings_manager import SettingsManager
from translations import TRANSLATIONS
from ui import hero_arrow_rect


class HeroAnimationTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name)/'settings.json'
        override = patch('settings_manager.SETTINGS_FILE', self.path)
        override.start()
        self.addCleanup(override.stop)
        self.game = Game(42)
        self.game.state = 'menu'

    def card_pixels(self):
        return pygame.image.tostring(self.game.screen.subsurface((749, 260, 373, 220)), 'RGB')

    def test_old_low_settings_enable_hero_animation_independently(self):
        self.path.write_text(json.dumps({'menu_animations': False}))
        settings = SettingsManager()
        self.assertFalse(settings.get('menu_animations'))
        self.assertTrue(settings.get('hero_animations'))
        settings.set('hero_animations', False)
        self.assertFalse(SettingsManager().get('hero_animations'))

    def test_transition_is_visible_and_finishes_with_menu_animations_off(self):
        g = self.game
        g.settings_manager.settings['menu_animations'] = False
        with patch('pygame.time.get_ticks', return_value=1000):
            g.draw_menu()
            g.update_menu([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
            g.draw_menu()
            animated_start = self.card_pixels()
            g.settings_manager.settings['hero_animations'] = False
            g.draw_menu()
            self.assertNotEqual(animated_start, self.card_pixels())
        g.settings_manager.settings['hero_animations'] = True
        with patch('pygame.time.get_ticks', return_value=1130):
            g.draw_menu()
            animated_midpoint = self.card_pixels()
            g.settings_manager.settings['hero_animations'] = False
            g.draw_menu()
            self.assertNotEqual(animated_midpoint, self.card_pixels())
        g.settings_manager.settings['hero_animations'] = True
        with patch('pygame.time.get_ticks', return_value=1400):
            g.draw_menu()
            complete = self.card_pixels()
            g.settings_manager.settings['hero_animations'] = False
            g.draw_menu()
            self.assertEqual(complete, self.card_pixels())
        self.assertIsNone(g.player)

    def test_arrow_click_wraps_and_animates_in_both_directions(self):
        g = self.game
        with patch('pygame.time.get_ticks', return_value=1000):
            g.draw_menu()
        for step, expected, ticks in [(-1, 3, 1100), (1, 0, 1500)]:
            with patch('pygame.time.get_ticks', return_value=ticks):
                g.update_menu([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                  pos=hero_arrow_rect(step).center)])
                g.draw_menu()
                self.assertEqual(g.selected_hero_index, expected)
                self.assertEqual(g.ui._hero_direction, step)
                self.assertEqual(g.ui._hero_started, ticks)

    def test_arrow_buttons_never_move_during_hero_transition(self):
        g = self.game
        g.settings_manager.set('theme', 'cyan')  # keep palette fixed while testing motion
        g.ui.mouse_pos = lambda: (0, 0)
        def arrow_pixels():
            return tuple(pygame.image.tostring(
                g.screen.subsurface(hero_arrow_rect(step)), 'RGB') for step in (-1, 1))
        with patch('pygame.time.get_ticks', return_value=1000):
            g.draw_menu()
            before = arrow_pixels()
            g.update_menu([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
            g.draw_menu()
            self.assertEqual(before, arrow_pixels())
        with patch('pygame.time.get_ticks', return_value=1130):
            g.draw_menu()
            self.assertEqual(before, arrow_pixels())
        with patch('pygame.time.get_ticks', return_value=1400):
            g.draw_menu()
            self.assertEqual(before, arrow_pixels())
        # The animated content rect must not overlap either arrow button.
        card = pygame.Rect(661, 202, 549, 405)
        content = pygame.Rect(card.x + 104, 260, card.w - 208, 220)
        for step in (-1, 1):
            self.assertFalse(content.colliderect(hero_arrow_rect(step)))

    def test_dash_window_has_no_hud_hint_and_attack_still_works(self):
        g = self.game
        g.start_new_game()
        p = g.player
        with patch('pygame.time.get_ticks', return_value=1000):
            g.screen.fill('black')
            g.ui.draw_hud(g.screen, p, 0, 0)
            before = pygame.image.tostring(g.screen, 'RGB')
            p.dash_attack_window_timer = .2
            p.dash_attack_triggered = False
            g.screen.fill('black')
            g.ui.draw_hud(g.screen, p, 0, 0)
            self.assertEqual(before, pygame.image.tostring(g.screen, 'RGB'))
        for language in TRANSLATIONS.values():
            self.assertNotIn('DASH_HINT', language)
            self.assertIn('CTRL_DASH_DESC', language)
        self.assertTrue(p.try_dash_attack())
        self.assertTrue(p.dash_attack_active)
        self.assertIsNotNone(p.get_dash_attack_area())
