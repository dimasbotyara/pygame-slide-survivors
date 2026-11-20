"""Algorithmic regressions: no timing thresholds or hardware assumptions."""
import copy
import math
import os
import random
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from camera import Camera
from enemies import Enemy, Boss
from main import Game
from preferences import DEFAULTS, TABS, valid_value
from spatial import EnemyGrid
from translations import set_language, t
from world import World


class PerformanceTests(unittest.TestCase):
    def test_spatial_separation_matches_sequential_brute_force(self):
        rng = random.Random(42)
        brute = [Enemy(rng.uniform(-300, 300), rng.uniform(-300, 300), 'zombie') for _ in range(100)]
        brute.extend([Enemy(-128, -128, 'ghost'), Boss(120, 120)])
        brute[0].alive = False
        brute[1].knockback_vx = 50000  # Cross several cells in a single update.
        indexed = copy.deepcopy(brute)
        for _ in range(10):
            grid = EnemyGrid(indexed)
            for a, b in zip(brute, indexed):
                if a.alive:
                    a.update(.016, 0, 0, brute)
                    b.update(.016, 0, 0, grid)
                    grid.update(b)
                self.assertAlmostEqual(a.x, b.x, places=10)
                self.assertAlmostEqual(a.y, b.y, places=10)

    def test_sparse_neighbors_do_not_scan_the_entire_crowd(self):
        enemies = [Enemy(x*150, y*150, 'zombie') for x in range(20) for y in range(20)]
        grid = EnemyGrid(enemies)
        checks = sum(len(grid.nearby(e)) for e in enemies)
        self.assertLess(checks, len(enemies)*10)
        self.assertLess(checks, len(enemies)**2/20)

    def test_fast_habitat_query_matches_region_reference(self):
        world = World(42)
        rng = random.Random(7)
        for _ in range(300):
            x, y = rng.uniform(-20000, 20000), rng.uniform(-20000, 20000)
            self.assertEqual(world.biome_at(x, y), world._regions(x, y)[0][0])

    def test_visual_settings_do_not_change_habitats(self):
        world = World(3)
        points = [(x*129, -x*37) for x in range(-20, 20)]
        habitats = [world.biome_at(x, y) for x, y in points]
        for quality in ('low', 'medium', 'high'):
            for blend in (120, 220, 340):
                for shading in (False, True):
                    world.terrain_tile(1, -3, quality, blend, shading)
        self.assertEqual(habitats, [world.biome_at(x, y) for x, y in points])
        self.assertLessEqual(world.terrain_tile.cache_info().currsize, 768)

    def test_narrower_blend_keeps_gradients_and_seeded_geography(self):
        world = World(42)
        found = False
        for x in range(-3000, 3000, 20):
            regions = world._regions(x, 0)
            gap = regions[1][1]-regions[0][1]
            if 220 < gap < 340:
                narrow = world.ground_color_at(x, 0, 220, False)
                wide = world.ground_color_at(x, 0, 340, False)
                self.assertEqual(narrow, regions[0][0].ground)
                found |= wide != narrow
        self.assertTrue(found)

    def test_removed_settings_cannot_be_loaded(self):
        for name in ('biome_notifications', 'minimap_biomes'):
            self.assertNotIn(name, DEFAULTS)
            self.assertFalse(valid_value(name, True))
            self.assertFalse(any(name == key for _, rows in TABS for key, _ in rows))

    def test_aspect_ratios_desktop_resolution_and_scaled_buffer_reuse(self):
        with patch('settings_manager.SettingsManager.save'):
            game = Game(42)
            for size in ((1440, 900), (1024, 768), (1280, 800), (1920, 1080), (2560, 1080)):
                game.settings_manager.settings['resolution'] = size
                game.display.apply()
                viewport = game.display.viewport
                self.assertLessEqual(viewport.right, size[0])
                self.assertLessEqual(viewport.bottom, size[1])
                self.assertAlmostEqual(viewport.w/viewport.h, 16/9, delta=.003)
                self.assertEqual(game.display.logical_pos(viewport.center), (640, 360))
                game.present()
                buffer = game.display.scaled_frame
                game.present()
                self.assertIs(game.display.scaled_frame, buffer)
            game.settings_manager.settings['resolution'] = (0, 0)
            with patch('pygame.display.get_desktop_sizes', return_value=[(1440, 900)]):
                game.display.apply()
            self.assertEqual(game.display.window.get_size(), (1440, 900))

    def test_radar_never_samples_terrain_even_with_legacy_setting(self):
        game = Game(42)
        game.start_new_game()
        game.settings_manager.settings['minimap_biomes'] = True
        with patch.object(game.world, 'ground_color_at', side_effect=AssertionError('radar sampled terrain')):
            game.ui.draw_minimap(game.screen, game.player, [], [], [], False, game.world, 3)
        self.assertEqual(game.ui._biome_label_key, t('BIOME_'+game.world.biome_at(0, 0).key))

    def test_gameplay_does_not_copy_the_canvas_for_menu_transitions(self):
        game = Game(42)
        game.state = 'playing'
        self.assertIsNone(game.transition_snapshot())
        game.state = 'menu'
        self.assertIsNotNone(game.transition_snapshot())
        game.settings_manager.settings['menu_animations'] = False
        self.assertIsNone(game.transition_snapshot())
