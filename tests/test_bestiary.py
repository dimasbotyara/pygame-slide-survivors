"""Complete bilingual guide, real previews, navigation and live data regressions."""
import os
from pathlib import Path
import random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from bestiary import (Bestiary, ENTRY_KEYS, FILTERS, PAGE_SIZE, base_enemy, category,
                      facts, guide_rect, back_rect, filter_rect, row_rect, page_rect, name)
from enemies import Enemy, Boss
from main import Game
from settings import ENEMY_TYPES
from translations import TRANSLATIONS, set_language, t
from ui import word_lines
from wildlife import RESIDENTS


def press(key, **kwargs):
    return pygame.event.Event(pygame.KEYDOWN, key=key, **kwargs)


def click(rect):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)


class BestiaryTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        setting_file = patch('settings_manager.SETTINGS_FILE', Path(temp.name)/'settings.json')
        setting_file.start()
        self.addCleanup(setting_file.stop)
        self.addCleanup(set_language, 'ru')
        self.game = Game(42)
        self.game.state = 'menu'
        self.guide = Bestiary()

    def test_every_spawnable_type_is_covered_once_and_translated(self):
        self.assertEqual(set(ENTRY_KEYS), set(ENEMY_TYPES) | set(RESIDENTS) | {'boss'})
        self.assertEqual(len(ENTRY_KEYS), len(set(ENTRY_KEYS)))
        for lang in ('ru', 'en'):
            set_language(lang)
            for key in ENTRY_KEYS:
                e = self.guide.enemy(key)
                self.assertIn('MOB_'+key, TRANSLATIONS[lang])
                desc = 'GUIDE_BEHAVIOR_'+('boss' if key == 'boss' else e.archetype)
                self.assertIn(desc, TRANSLATIONS[lang])
                self.assertNotIn('GUIDE_', ' '.join(facts(key, e)))
                if e.home_biome:
                    self.assertIn(t('BIOME_'+e.home_biome), ' '.join(facts(key, e)))
                else:
                    self.assertIn(t('GUIDE_ANY_BIOME'), facts(key, e))

    def test_opening_and_browsing_does_not_start_run_or_change_rng(self):
        g = self.game
        self.assertIsNone(g.bestiary)
        state = random.getstate()
        g.update_menu([click(guide_rect())])
        self.assertEqual(g.state, 'bestiary')
        g.draw_bestiary()
        self.assertEqual(random.getstate(), state)
        self.assertIsNone(g.player)
        g.update_bestiary([press(pygame.K_ESCAPE)])
        self.assertEqual(g.state, 'menu')
        g.update_menu([press(pygame.K_b)])
        g.update_bestiary([click(back_rect())])
        g.update_menu([press(pygame.K_KP8)])
        self.assertEqual(g.state, 'bestiary')
        self.assertEqual(g.selected_hero_index, 0)
        self.assertEqual(g.game_time, 0)

    def test_filters_pages_mouse_wheel_and_boundary_navigation(self):
        b = self.guide
        b.handle([press(pygame.K_PAGEDOWN)])
        self.assertEqual(b.cursor, PAGE_SIZE)
        b.handle([click(row_rect(2))])
        self.assertEqual(b.cursor, PAGE_SIZE+2)
        b.handle([click(page_rect(1))])
        self.assertEqual(b.cursor, 2*PAGE_SIZE+2)
        b.handle([press(pygame.K_END), press(pygame.K_DOWN)])
        self.assertEqual(b.cursor, len(ENTRY_KEYS)-1)
        b.handle([pygame.event.Event(pygame.MOUSEWHEEL, y=1)])
        self.assertEqual(b.cursor, len(ENTRY_KEYS)-2)
        for i, group in enumerate(FILTERS):
            b.handle([click(filter_rect(i))])
            self.assertEqual(b.cursor, 0)
            self.assertTrue(all(group == 'all' or category(key) == group for key in b.entries))
        b.handle([press(pygame.K_TAB)])
        self.assertEqual(b.filter, 0)
        b.handle([press(pygame.K_TAB, mod=pygame.KMOD_SHIFT)])
        self.assertEqual(b.filter, 3)
        b.handle([press(pygame.K_3)])
        self.assertEqual(set(b.entries), set(RESIDENTS))
        b.handle([press(pygame.K_KP2)])
        self.assertEqual(set(b.entries), set(ENEMY_TYPES))

    def test_stats_follow_actual_game_objects_and_resident_overrides(self):
        for key in ENTRY_KEYS:
            e = self.guide.enemy(key)
            actual = base_enemy(key)
            for attr in ('max_hp', 'damage', 'base_speed', 'shoot_range', 'shot_offsets',
                         'explode_damage', 'explode_radius', 'windup_duration', 'attack_cooldown', 'home_biome'):
                self.assertEqual(getattr(e, attr), getattr(actual, attr), (key, attr))
        with patch.dict(ENEMY_TYPES['zombie'], hp=987, damage=321):
            e = base_enemy('zombie')
            self.assertIn('987', facts('zombie', e)[0])
            self.assertIn('321', facts('zombie', e)[1])
        crab = base_enemy('tide_crab')
        self.assertEqual(crab.damage, RESIDENTS['tide_crab'].traits['damage'])
        bat = base_enemy('echo_bat')
        self.assertEqual(len(bat.shot_offsets), 2)
        self.assertIn('2', ' '.join(facts('echo_bat', bat)))

    def test_every_image_and_detail_page_renders_and_fits_in_both_languages(self):
        ui = self.game.ui
        b = self.guide
        for lang in ('ru', 'en'):
            set_language(lang)
            for index, key in enumerate(ENTRY_KEYS):
                b.filter, b.cursor = 0, index
                b.draw(self.game.screen, ui)
                image = b.image(key)
                self.assertGreater(image.get_bounding_rect().w, 0)
                self.assertIs(b.icon(key), b.icon(key))
                self.assertLessEqual(b.icon(key).get_width(), 40)
                self.assertLess(ui.font_medium.size(name(key))[0], 746)
                e = b.enemy(key)
                desc = t('GUIDE_BEHAVIOR_'+('boss' if key == 'boss' else e.archetype))
                self.assertLessEqual(484+24*len(list(word_lines(ui.body, desc, 746))), 593)
                self.assertLessEqual(len(facts(key, e)), 8)
                self.assertLessEqual(593+21*len(list(word_lines(ui.font_small, t('GUIDE_NATIVE_RULE'), 746))), 646)
            self.assertLess(ui.mono.size(t('GUIDE_HINT'))[0], 1140)
            self.assertLess(ui.font_small.size(t('GUIDE_BASE_NOTE'))[0], 1140)

    def test_lobby_button_click_is_mapped_at_1440_by_900(self):
        g = self.game
        g.settings_manager.settings['resolution'] = (1440, 900)
        g.display.apply()
        rect = g.display.viewport
        x, y = guide_rect().center
        physical = rect.x+x*rect.w/1280, rect.y+y*rect.h/720
        events = g.prepare_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=physical)])
        g.update_menu(events)
        self.assertEqual(g.state, 'bestiary')
