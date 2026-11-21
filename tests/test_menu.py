"""Menu navigation, layout and offline glyph regressions, without a display."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from highscores import load_highscores
from achievements import ACHIEVEMENTS_LIST
from main import Game
from translations import set_language, t
from typography import face
from ui import hero_arrow_rect, hero_rect, menu_rect, pause_rect, upgrade_rect, word_lines


def press(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def click(rect):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)


class MenuTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        patcher = patch('settings_manager.SETTINGS_FILE', Path(folder.name) / 'settings.json')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.game = Game()
        self.game.state = 'menu'

    def test_equip_is_not_start_and_escape_keeps_hero(self):
        g = self.game
        g.update_menu([click(menu_rect(1))])
        g.update_hero_select([click(hero_rect(2))])
        self.assertEqual((g.state, g.selected_hero_index, g.menu_selection), ('menu', 2, 0))
        self.assertIsNone(g.player)
        g.update_menu([click(menu_rect(1))])
        g.update_hero_select([press(pygame.K_LEFT), press(pygame.K_ESCAPE)])
        self.assertEqual(g.selected_hero_index, 2)
        g.update_menu([press(pygame.K_UP), press(pygame.K_RETURN)])
        self.assertEqual((g.state, g.player.hero_id), ('playing', 'spark'))

    def test_digits_activate_menus_but_select_tabs_in_settings(self):
        g = self.game
        g.update_menu([press(pygame.K_4)])
        self.assertEqual(g.state, 'settings')
        with patch.object(g.settings_manager, 'save'):
            before = g.settings_manager.get('screen_shake')
            g.update_settings([press(pygame.K_KP2)])
            self.assertEqual(g.settings_tab, 1)
            self.assertEqual(g.settings_manager.get('screen_shake'), before)
            g.settings_selection = 2
            g.update_settings([press(pygame.K_RETURN)])
            self.assertEqual(g.settings_manager.get('screen_shake'), not before)
            g.update_settings([press(pygame.K_ESCAPE)])
        self.assertEqual(g.state, 'menu')
        for digit, state in [(2, 'hero_select'), (3, 'achievements'), (5, 'controls'), (6, 'highscores')]:
            g.state = 'menu'
            g.update_menu([press(getattr(pygame, f'K_{digit}'))])
            self.assertEqual(g.state, state)
        g.state = 'game_over'
        g.update_game_over([press(pygame.K_2)])
        self.assertEqual(g.state, 'menu')
        g.update_menu([press(pygame.K_7)])
        self.assertFalse(g.running)

    def test_lobby_arrows_equip_without_starting(self):
        g = self.game
        g.update_menu([click(hero_arrow_rect(-1))])
        self.assertEqual(g.selected_hero_index, 3)
        g.update_menu([click(hero_arrow_rect(1)), press(pygame.K_RIGHT)])
        self.assertEqual((g.selected_hero_index, g.state), (1, 'menu'))
        self.assertIsNone(g.player)
        g.update_menu([press(pygame.K_KP1)])
        self.assertEqual(g.player.hero_id, 'brawler')

    def test_surrender_submits_run_once(self):
        g = self.game
        g.start_new_game()
        g.state, g.game_time, g.player.enemies_killed = 'paused', 52, 8
        with TemporaryDirectory() as folder, patch('highscores.SAVE_DIR', folder), \
                patch('highscores.HIGHSCORES_FILE', Path(folder)/'scores.json'):
            g.update_paused([click(pause_rect(2)), press(pygame.K_RETURN)])
            self.assertEqual((g.state, g.surrendered, g.new_record_pos), ('game_over', True, 0))
            g.draw_game_over()
            g.finish_run()  # repeated input cannot insert a duplicate
            scores = load_highscores()
            self.assertEqual(len(scores), 1)
            self.assertEqual((scores[0]['time'], scores[0]['level'], scores[0]['kills']), (52, 1, 8))
        g.start_new_game()
        self.assertFalse(g.surrendered)

    def test_achievement_list_mouse_wheel_and_draggable_scrollbar(self):
        g = self.game
        g.state = 'achievements'
        g.draw_achievements()
        self.assertGreaterEqual(len(ACHIEVEMENTS_LIST), 25)
        for lang in ('ru', 'en'):
            set_language(lang)
            for ach_id in ACHIEVEMENTS_LIST:
                self.assertNotEqual(t(f'ach_{ach_id}_title'), f'ach_{ach_id}_title')
                self.assertNotEqual(t(f'ach_{ach_id}_desc'), f'ach_{ach_id}_desc')
        set_language('ru')
        self.assertEqual(g.ui.achievement_scroll, 0)
        g.update_achievements([pygame.event.Event(pygame.MOUSEWHEEL, y=-3)])
        self.assertGreater(g.ui.achievement_scroll, 0)
        maximum, thumb = g.ui.achievement_scroll_metrics()
        self.assertGreater(maximum, 0)
        g.update_achievements([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                  pos=thumb.center)])
        g.update_achievements([pygame.event.Event(pygame.MOUSEMOTION,
                                                  pos=(thumb.centerx, g.ui.ACH_TRACK_RECT.bottom),
                                                  rel=(0, 100), buttons=(1, 0, 0))])
        g.update_achievements([pygame.event.Event(pygame.MOUSEBUTTONUP, button=1,
                                                  pos=(thumb.centerx, g.ui.ACH_TRACK_RECT.bottom))])
        self.assertEqual(g.ui.achievement_scroll, maximum)
        g.draw_achievements()

    def test_offline_fallback_and_language_flags(self):
        font = self.game.ui.font
        for text, role in [('🏆', 'emoji'), ('🔒', 'emoji'), ('🇷🇺', 'emoji'), ('🇬🇧', 'emoji'),
                           ('↑↓', 'mono'), ('✦', 'symbol')]:
            self.assertEqual(list(font.runs(text)), [(face(role, font.px), text)])
            surf = font.render(text, True, 'white')
            self.assertNotEqual(surf.get_bounding_rect().size, (0, 0))
            self.assertEqual(surf.get_width(), font.size(text)[0])
        self.game.draw_language_select()
        self.game.draw_achievements()

    def test_upgrade_labels_fit_in_both_languages(self):
        g = self.game
        g.start_new_game()
        card = upgrade_rect(0, 3)
        self.addCleanup(set_language, 'ru')
        for lang in ('ru', 'en'):
            set_language(lang)
            for u in g.upgrade_manager.all_upgrades:
                names = list(word_lines(g.ui.font_medium, u.name, card.w-48))
                desc = list(word_lines(g.ui.body, u.description, card.w-48))
                self.assertLessEqual(88 + 36*len(names) + 25*len(desc), card.h-75, u.name)
                self.assertNotIn('UPGRADE_', t('UPGRADE_LVL', '0 → 1 / 3'))
            g.ui.draw_upgrade_screen(g.screen, g.upgrade_manager.all_upgrades[:3], 2, g.player)
            g.draw_menu()
