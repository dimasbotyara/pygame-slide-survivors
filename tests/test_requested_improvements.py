"""Regression tests for settings, guide filters and presentation changes."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from bestiary import Bestiary, TABS, TAB_FILTERS
from main import Game
from heroes import HERO_KEYS
from ui import reset_button_rect, reset_cancel_rect, reset_confirm_rect
from typography import FACES, ROOT
from world import World


def click(rect):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)


def key(code):
    return pygame.event.Event(pygame.KEYDOWN, key=code)


class Improvements(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.settings, self.achievements, self.scores = (root / x for x in ('settings.json', 'achievements.json', 'highscores.json'))
        for target, path in [('settings_manager.SETTINGS_FILE', self.settings),
                             ('achievements.ACHIEVEMENTS_FILE', self.achievements),
                             ('highscores.HIGHSCORES_FILE', self.scores)]:
            p = patch(target, path)
            p.start()
            self.addCleanup(p.stop)
        self.game = Game(42)

    def test_hero_persistence_and_invalid_value(self):
        g = self.game
        g.update_menu([key(pygame.K_RIGHT), key(pygame.K_RIGHT)])
        self.assertEqual(Game(42).selected_hero_index, 2)
        g.hero_cursor = 3
        g.update_hero_select([key(pygame.K_RETURN)])
        self.assertEqual(Game(42).selected_hero_index, 3)
        g.hero_cursor = 1
        g.update_hero_select([key(pygame.K_ESCAPE)])
        self.assertEqual(Game(42).selected_hero_index, 3)
        self.settings.write_text(json.dumps({'selected_hero': 'invalid'}))
        self.assertEqual(Game(42).selected_hero_index, 0)

    def test_reset_confirmation_cancel_delete_and_error(self):
        g = self.game
        for path in (self.settings, self.achievements, self.scores):
            path.write_text('{}')
        other = self.settings.parent / 'unrelated.txt'
        other.write_text('keep')
        g.update_settings([click(reset_button_rect()), click(reset_cancel_rect())])
        self.assertTrue(all(p.exists() for p in (self.settings, self.achievements, self.scores)))
        g.update_settings([click(reset_button_rect())])
        g.draw_settings()
        g.update_settings([click(reset_confirm_rect())])
        self.assertFalse(g.running)
        self.assertFalse(any(p.exists() for p in (self.settings, self.achievements, self.scores)))
        self.assertTrue(other.exists())
        g.running = True
        with patch('main.os.remove', side_effect=PermissionError('denied')):
            g.update_settings([click(reset_button_rect()), click(reset_confirm_rect())])
        self.assertTrue(g.running)
        self.assertTrue(g.reset_error)

    def test_all_guide_filters_have_entries_and_render(self):
        b = Bestiary()
        for tab, name in enumerate(TABS):
            b.tab = tab
            for index in range(len(TAB_FILTERS[name])):
                b.filter, b.cursor = index, 0
                self.assertTrue(b.entries, (name, index))
                b.draw(self.game.screen, self.game.ui)
            b.handle([key(pygame.K_TAB)])
            self.assertEqual((b.filter, b.cursor), (0, 0))

    def test_fonts_and_decorations(self):
        self.assertTrue(all((ROOT / path).is_file() for path in FACES.values()))
        world = World(42)
        decorations = world.get_decorations_for_chunk(0, 0)
        self.assertGreaterEqual(len(decorations), 28)
        self.assertTrue(any(d.sprite and d.sprite.get_width() >= 24 for d in decorations))

    def test_fixed_window_and_settings_resolution(self):
        g = self.game
        self.assertFalse(g.display.window.get_flags() & pygame.RESIZABLE)
        g.prepare_events([pygame.event.Event(pygame.VIDEORESIZE, w=1000, h=800)])
        self.assertEqual(g.settings_manager.get('resolution'), (1280, 720))
        g.settings_manager.set('resolution', (1000, 800))
        g.display.apply()
        self.assertEqual(g.display.window.get_size(), (1000, 800))
        self.assertFalse(g.display.window.get_flags() & pygame.RESIZABLE)
