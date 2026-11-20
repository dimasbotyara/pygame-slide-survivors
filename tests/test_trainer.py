"""Trainer tools and menu rendering, without a real window or runtime patches."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from cheat_launcher import Trainer
from main import Game
from settings import RESIDENT_SPAWN_CHANCE
from translations import set_language
from wildlife import RESIDENT_BY_BIOME


class TrainerTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(world_seed=42)
        self.game.start_new_game()
        self.trainer = Trainer(self.game)

    def test_seed_and_run_scoped_bookmark(self):
        g, tr = self.game, self.trainer
        self.assertEqual(g.world.seed, 42)
        g.player.x, g.player.y = 123, -456
        tr.act_save_position()
        g.player.x = 999
        tr.act_return_position()
        self.assertEqual((g.player.x, g.player.y), (123, -456))
        g.start_new_game()
        tr.act_return_position()
        self.assertEqual((g.player.x, g.player.y), (0, 0))

    def test_native_spawn_and_reset_modifiers(self):
        g, tr = self.game, self.trainer
        tr.act_spawn_resident()
        enemy = g.enemies[-1]
        self.assertEqual(enemy.enemy_type, RESIDENT_BY_BIOME[g.world.biome_at(enemy.x, enemy.y).key])
        tr.infinite_ult = True
        tr.update(.01)
        self.assertEqual(g.player.ult_charge, 100)
        tr.god_mode, tr.damage_multiplier, tr.time_scale = True, 100, .1
        stats = dict(g.player.stats)
        tr.act_reset_modifiers()
        self.assertFalse(tr.god_mode or tr.infinite_ult)
        self.assertEqual((tr.damage_multiplier, tr.time_scale), (1, 1))
        self.assertEqual(g.player.stats, stats)

    def test_all_tabs_fit_and_are_clickable(self):
        tr = self.trainer
        tr.visible = True
        for i in range(len(tr.tabs)):
            rect = tr._tab_rect(i)
            self.assertLessEqual(rect.right, tr.panel_w)
            self.assertLessEqual(rect.bottom, tr.header_h)
            tr._on_mouse(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                           pos=rect.move(tr.panel_x, tr.panel_y).center))
            self.assertEqual(tr.tab_index, i)
            tr._draw_menu(self.game.screen)

    def test_menu_animation_finishes_and_both_languages_render(self):
        g = self.game
        self.addCleanup(set_language, 'ru')
        for lang in ('ru', 'en'):
            set_language(lang)
            g.draw_hero_select()
            with patch('pygame.time.get_ticks', return_value=1000):
                g.draw_menu()
                g.selected_hero_index = (g.selected_hero_index+1) % 4
                g.draw_menu()
                g.ui.begin_transition(g.screen.copy())
            with patch('pygame.time.get_ticks', return_value=1400):
                g.draw_menu()
                g.ui.draw_transition(g.screen)
                self.assertIsNone(g.ui.transition_frame)
            g.draw_playing()

    def test_resident_chance_is_three_times_lower(self):
        self.assertAlmostEqual(RESIDENT_SPAWN_CHANCE * 3, .25)
