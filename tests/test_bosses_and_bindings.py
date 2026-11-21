import os
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from enemies import Boss, Enemy, EnemySpawner, BOSS_KEYS
from main import Game
from preferences import TABS, BINDINGS
from settings_manager import SettingsManager
from wildlife import RESIDENTS
from bestiary import Bestiary


def press(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


class BossesBindingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'settings.json'
        p = patch('settings_manager.SETTINGS_FILE', self.path)
        p.start()
        self.addCleanup(p.stop)
        self.game = Game(42)

    def test_boss_rotation_attack_phase_and_render(self):
        g = self.game
        g.start_new_game()
        spawner = EnemySpawner()
        bosses = [spawner.spawn_boss(0, 0) for _ in BOSS_KEYS]
        self.assertEqual([b.variant for b in bosses], list(BOSS_KEYS))
        self.assertEqual(spawner.spawn_boss(0, 0).variant, BOSS_KEYS[0])
        for boss in bosses:
            with self.subTest(variant=boss.variant):
                boss.x, boss.y = 80, 0
                boss.advance_attack(.01, g.player)
                self.assertGreater(boss.windup_left, 0)
                result = boss.advance_attack(boss.windup_duration + .01, g.player)
                self.assertEqual(result, 'shot' if boss.shoot_range else 'hit')
                boss.hp = boss.max_hp * .4
                boss.update(.01, g.player.x, g.player.y, [])
                self.assertTrue(boss.is_enraged)
                if boss.variant == 'boss':
                    self.assertEqual(len(boss.shot_offsets), 3)
                    self.assertGreater(boss.shoot_range, 0)
                boss.draw(g.screen, g.camera)
                boss.draw_windup(g.screen, g.camera)
                guide = Bestiary()
                guide.image(boss.variant, 1, True)
        spawner.boss_timer = 300
        active = [bosses[0]]
        spawner.update(.01, 0, 0, active, [])
        self.assertEqual(sum(e.is_boss for e in active), 1)
        active[0].alive = False
        spawner.update(.01, 0, 0, active, [])
        self.assertEqual(sum(e.is_boss and e.alive for e in active), 1)

    def test_rebinding_persists_swaps_and_controls_player(self):
        g = self.game
        g.settings_tab = next(i for i, tab in enumerate(TABS) if tab[0] == 'CONTROLS')
        g.settings_selection = 0
        g.update_settings([press(pygame.K_RETURN), press(pygame.K_s)])
        self.assertEqual(g.settings_manager.get('bind_up'), pygame.K_s)
        self.assertEqual(g.settings_manager.get('bind_down'), pygame.K_w)
        self.assertEqual(SettingsManager().get('bind_up'), pygame.K_s)
        g.start_new_game()
        g.player.update_movement(.1, defaultdict(bool, {pygame.K_s: True}))
        self.assertLess(g.player.velocity_y, 0)
        g.update_settings([press(pygame.K_RETURN), press(pygame.K_ESCAPE)])
        self.assertEqual(g.settings_manager.get('bind_up'), pygame.K_s)
        self.assertIsNone(g.binding_capture)
        # A rebound arrow must not also activate another action's default shortcut.
        g.player.bindings['bind_down'] = pygame.K_UP
        g.player.bindings['bind_up'] = pygame.K_w
        g.player.update_movement(.1, defaultdict(bool, {pygame.K_UP: True}))
        self.assertGreater(g.player.velocity_y, 0)
        g.draw_settings()

    def test_resident_behaviors_remain_moving_and_bounded(self):
        for kind in RESIDENTS:
            with self.subTest(kind=kind):
                e = Enemy(0, 0, kind)
                e.update(.1, 500, 0, [e])
                self.assertNotEqual((e.velocity_x, e.velocity_y), (0, 0))
                self.assertLess(abs(e.velocity_x) + abs(e.velocity_y), 600)
                e.windup_left = 1
                e.update(.1, 500, 0, [e])
                self.assertEqual((e.velocity_x, e.velocity_y), (0, 0))
