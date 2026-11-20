import os
import unittest
from collections import defaultdict
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from enemies import Enemy, EnemyProjectile
from main import Game
from settings import DRAIN_PERIOD, ICE_DURATION, PERFECT_DODGE_WINDOW, STASIS_RADIUS
from translations import TRANSLATIONS


class AbilityTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.start_new_game()
        self.player = self.game.player

    def equip(self, key):
        self.game.upgrade_manager.upgrade_map[key].apply(self.player)

    def test_slide_exit_charges_exactly_one_following_swing(self):
        enemy = Enemy(0, 0, 'crusher')
        self.game.enemies.append(enemy)
        self.player.x = enemy.strike_radius + self.player.size - 1
        enemy.windup_left = PERFECT_DODGE_WINDOW
        keys = defaultdict(bool, {pygame.K_SPACE: True})
        with patch('pygame.key.get_pressed', return_value=keys), patch('pygame.mouse.get_pos', return_value=(400, 0)):
            self.game.update_playing(0.016, [])
        self.assertTrue(self.player.dodge_charge)
        self.assertFalse(self.player.get_fist_attack_area()['cleave'])  # current swing is unchanged
        self.player.update_fist_attack(1)
        self.assertTrue(self.player.get_fist_attack_area()['cleave'])
        self.assertFalse(self.player.dodge_charge)
        self.player.update_fist_attack(1)
        self.assertFalse(self.player.get_fist_attack_area()['cleave'])

    def test_no_reward_for_walking_early_exit_or_remaining_outside(self):
        enemy = Enemy(0, 0, 'crusher')
        self.player.x = 120
        enemy.windup_left = PERFECT_DODGE_WINDOW
        self.assertFalse(enemy.check_slide_escape(self.player, (0, 0)))
        self.player.is_sliding = True
        enemy.windup_left += 0.01
        self.assertFalse(enemy.check_slide_escape(self.player, (0, 0)))
        enemy.windup_left /= 2
        self.assertFalse(enemy.check_slide_escape(self.player, (110, 0)))
        self.assertTrue(enemy.check_slide_escape(self.player, (0, 0)))
        self.assertFalse(enemy.check_slide_escape(self.player, (0, 0)))

    def test_ice_preserves_heading_only_on_live_patches(self):
        trail = self.game.ice_trail
        self.player.x = 80
        trail.update(0.02, self.player, (0, 0))
        self.assertFalse(trail.patches)
        self.equip('ice_trail')
        self.player.is_sliding = True
        trail.update(0.02, self.player, (0, 0))
        enemy = Enemy(24, 0, 'zombie')
        enemy.velocity_y = enemy.base_speed  # initially moving across path
        self.game.enemies.append(enemy)
        self.game.update_enemies(0.02)
        self.assertEqual(enemy.x, 24)
        self.assertGreater(enemy.y, 0)
        self.player.is_sliding = False
        trail.update(ICE_DURATION, self.player, (80, 0))
        self.assertFalse(trail.patches)
        self.game.update_enemies(0.02)
        self.assertGreater(enemy.x, 24)  # can now turn to chase

    def test_pulses_respect_range_cooldown_and_kill_rewards(self):
        self.equip('drain_aura')
        self.equip('repulse_aura')
        self.player.hp = 50
        near, other, far = [Enemy(x, 0, 'zombie') for x in (30, -40, 500)]
        near.hp = 4
        self.game.enemies = [far, other, near]
        def tick(dt):
            self.game.pulse_auras.update(dt, self.player, self.game.enemies, self.game.deal_damage_to_enemy)
        tick(0.016)
        self.assertFalse(near.alive)
        self.assertEqual(self.player.enemies_killed, 1)
        self.assertEqual(self.player.hp, 51)  # overkill cannot heal
        self.assertLess(other.knockback_vx, 0)
        self.assertEqual(far.knockback_vx, 0)
        tick(0.016)
        self.assertEqual(other.hp, other.max_hp)
        tick(DRAIN_PERIOD)
        self.assertEqual(other.hp, other.max_hp-8)
        self.assertEqual(self.player.hp, 53)
        self.assertEqual(far.hp, far.max_hp)

    def test_stasis_slows_only_inside_without_extending_lifetime(self):
        self.equip('stasis_aura')
        self.equip('stasis_aura')
        p = EnemyProjectile(STASIS_RADIUS-1, 0, 1, 0, 100, 1)
        self.game.enemy_projectiles = [p]
        x, ttl = p.x, p.lifetime
        self.game.update_enemy_projectiles(0.1)
        self.assertAlmostEqual(p.x-x, 6)
        self.assertAlmostEqual(ttl-p.lifetime, 0.1)
        x = p.x
        self.game.update_enemy_projectiles(0.1)
        self.assertAlmostEqual(p.x-x, 10)

    def test_new_upgrades_render_translate_and_reset(self):
        for key in ('ice_trail', 'drain_aura', 'repulse_aura', 'stasis_aura'):
            self.equip(key)
            for strings in TRANSLATIONS.values():
                for suffix in ('name', 'desc'):
                    self.assertIn(f'upgrade_{key}_{suffix}', strings)
        self.player.is_sliding = self.player.dodge_charge = True
        self.game.ice_trail.update(0.016, self.player, (0, 0))
        self.game.draw_playing()
        self.game.start_new_game()
        self.assertFalse(self.game.ice_trail.patches)
        self.assertFalse(self.game.player.dodge_charge)
        self.assertEqual(self.game.player.stats['stasis_aura'], 0)
