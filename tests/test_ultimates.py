"""Ultimate charge gates, cinematic casts, and Echo Slam body impacts."""
import os
import math
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from enemies import Enemy
from main import Game
from heroes import HEROES
from settings import DROP_CHANCE_TONIC


class UltimateTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        settings = patch('settings_manager.SETTINGS_FILE', Path(self.temp.name)/'settings.json')
        achievements = patch('achievements.ACHIEVEMENTS_FILE', Path(self.temp.name)/'achievements.json')
        settings.start(); achievements.start()
        self.addCleanup(settings.stop); self.addCleanup(achievements.stop)
        self.game = Game(world_seed=17)
        self.game.start_new_game()

    def test_charge_is_half_rate_and_cannot_gain_during_cast_or_cooldown(self):
        p = self.game.player
        p.gain_ult_charge(40)
        self.assertEqual(p.ult_charge, 20)
        p.ult_cooldown_timer = 3
        p.gain_ult_charge(40)
        self.assertEqual(p.ult_charge, 20)
        p.ult_cooldown_timer = 0
        p.ult_cast_timer = .6
        p.gain_ult_charge(40)
        self.assertEqual(p.ult_charge, 20)
        self.assertFalse(p.can_use_ult())

    def test_cast_uses_hero_duration_roots_player_and_starts_ten_second_cooldown(self):
        for index, hero_id in enumerate(('slider', 'brawler', 'spark', 'shadow')):
            g = self.game
            g.selected_hero_index = index
            g.start_new_game()
            p = g.player
            p.ult_charge = 100
            p.x, p.y = 25, 40
            start = (p.x, p.y)
            self.assertTrue(g.trigger_hero_ult())
            duration = HEROES[hero_id]['ult_cast_time']
            self.assertGreaterEqual(duration, .6)
            self.assertLessEqual(duration, 1.5)
            self.assertAlmostEqual(p.ult_cast_timer, duration)
            self.assertEqual(p.ult_charge, 0)
            hp_before = p.hp
            self.assertEqual(p.take_damage(60), 0)
            self.assertEqual(p.hp, hp_before)
            keys = defaultdict(bool, {pygame.K_d: True, pygame.K_SPACE: True})
            steps = int(duration / .05) + 1
            for _ in range(steps):
                p.update(.05, keys, (640, 360), g.camera)
                g._update_ultimate_cast(.05)
                if not g.ultimate_cast_pending:
                    break
            self.assertEqual((p.x, p.y), start)
            self.assertFalse(g.ultimate_cast_pending)
            self.assertEqual(p.ult_cooldown_timer, 10.0)
            self.assertEqual(g.ult_uses_run, 1)

    def test_earthquake_cracks_ground_and_launched_body_damages_another_enemy(self):
        g = self.game
        g.selected_hero_index = 1
        g.start_new_game()
        source = Enemy(420, 0, 'ghoul')
        target = Enemy(600, 0, 'ghoul')
        g.enemies = [source, target]
        hp_before = target.hp
        g._resolve_hero_ult('brawler')
        self.assertFalse(source.alive)
        self.assertTrue(target.alive)
        self.assertGreater(len(g.earthquake_cracks), 20)
        self.assertEqual(g.earthquake_crack_timer, 15.0)
        farthest = max(math.dist(point, (g.player.x, g.player.y))
                       for segment in g.earthquake_cracks for point in segment)
        self.assertGreater(farthest, 455 * 1.2)
        self.assertTrue(g.ultimate_bodies)
        body = g.ultimate_bodies[0]
        body.x = target.x - body.radius - 1
        body.y = target.y
        body.vx, body.vy = 100, 0
        g._update_ultimate_effects(.02)
        self.assertLess(target.hp, hp_before)
        self.assertIn(id(target), body.hit_targets)

    def test_slider_auto_ricochet_returns_to_origin_and_starts_slide_cooldown(self):
        g = self.game
        g.enemies = [Enemy(160, 0, 'ghoul')]
        target = g.enemies[0]
        target.max_hp = target.hp = 5000
        origin = (g.player.x, g.player.y)
        g._resolve_hero_ult('slider')
        self.assertTrue(g.player.ultimate_action_lock)
        for _ in range(100):
            g._update_slider_ultimate(.05)
            if g.slider_ultimate is None:
                break
        self.assertIsNone(g.slider_ultimate)
        self.assertFalse(g.player.ultimate_action_lock)
        self.assertEqual((g.player.x, g.player.y), origin)
        self.assertLess(target.hp, 5000)
        self.assertEqual(g.player.slide_charges, 0)
        self.assertGreater(g.player.slide_cooldown_timer, 0)
        self.assertEqual(g.player.speed_boost_timer, 5.0)

    def test_slider_empty_cast_refunds_half_meter_but_keeps_cooldown(self):
        g = self.game
        g.player.ult_charge = 0
        g.player.ult_cooldown_timer = 10.0
        g._resolve_hero_ult('slider')
        g._update_slider_ultimate(.01)
        self.assertEqual(g.player.ult_charge, 50.0)
        self.assertEqual(g.player.ult_cooldown_timer, 10.0)
        self.assertIsNone(g.slider_ultimate)
        self.assertEqual(g.player.speed_boost_timer, 5.0)
        self.assertEqual(g.player.slide_charges, 0)

    def test_spark_storm_weather_and_shadow_blade_turns(self):
        g = self.game
        g._resolve_hero_ult('spark')
        self.assertEqual(g.spark_storm_timer, 10.0)
        self.assertEqual(len(g.rain_drops), 150)
        g._update_spark_storm(.5)
        self.assertLess(g.spark_storm_timer, 10.0)
        g.rain_drops = [[100, 100, 500, 20]]
        with patch('pygame.draw.line') as draw_rain:
            g._draw_spark_storm_weather()
        rain_start, rain_end = draw_rain.call_args.args[2:4]
        self.assertGreater(rain_end[1]-rain_start[1],
                           abs(rain_end[0]-rain_start[0]))
        lightning_target = Enemy(120, 0, 'ghoul')
        lightning_target.max_hp = lightning_target.hp = 5000
        g.enemies = [lightning_target]
        hp_before_storm = lightning_target.hp
        g._update_spark_storm(.01)
        self.assertLess(lightning_target.hp, hp_before_storm)

        g.selected_hero_index = 3
        g.start_new_game()
        g.player.hp = 50
        shadow_target = Enemy(130, 20, 'ghoul')
        shadow_target.max_hp = shadow_target.hp = 5000
        g.enemies = [shadow_target]
        hp_before_shadow = shadow_target.hp
        g._resolve_hero_ult('shadow')
        first, second = g.shadow_ult_blades
        self.assertEqual(first['direction'], 1)
        self.assertEqual(second['direction'], -1)
        self.assertEqual(second['delay'], .2)
        hp_before_blades = g.player.hp
        g._update_shadow_ult_blades(.01)
        self.assertGreater(first['turns'], 0)
        self.assertAlmostEqual(second['delay'], .19)
        self.assertLess(shadow_target.hp, hp_before_shadow)
        self.assertGreater(g.player.hp, hp_before_blades)
        g._update_shadow_ult_blades(.09)
        self.assertAlmostEqual(second['delay'], .1)
        g._update_shadow_ult_blades(1.7)
        self.assertFalse(g.shadow_ult_blades)

    def test_selected_hero_cast_times_are_in_the_requested_range(self):
        self.assertEqual([HEROES[h]['ult_cast_time'] for h in ('slider', 'brawler', 'spark', 'shadow')],
                         [.6, 1.5, .9, 1.2])

    def test_temporary_tonic_drop_rate_is_approximately_one_third(self):
        self.assertAlmostEqual(DROP_CHANCE_TONIC, .13/3, places=3)
