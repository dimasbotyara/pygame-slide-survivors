"""Run with python -m unittest discover -s tests (no window required)."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from enemies import Boss, Enemy
from main import Game
from settings import COMBO_TIMEOUT, EXPLOSION_FUSE, SPEED_BOOST_DURATION
from translations import TRANSLATIONS


class CombatTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.start_new_game()
        self.player = self.game.player

    def equip(self, key):
        self.game.upgrade_manager.upgrade_map[key].apply(self.player)

    def test_bomb_extends_remaining_streak_once_per_pickup(self):
        self.player.add_combo()
        self.player.combo_timer = 1.25
        self.game.enemies = [Enemy(0, 0, 'ghoul') for _ in range(4)]
        self.game.apply_item_effect('bomb')
        self.assertEqual(self.player.enemies_killed, 4)
        self.assertEqual(self.player.combo_timer, 6.25)
        self.player.add_combo()
        self.assertEqual(self.player.combo_timer, 6.25)
        self.game.apply_item_effect('bomb')  # empty arena
        self.assertEqual(self.player.combo_timer, 11.25)
        self.assertEqual(self.player.combo_count, 2)

    def test_bomb_with_no_streak_does_not_bank_time(self):
        self.game.apply_item_effect('bomb')
        self.assertEqual(self.player.combo_count, 0)
        self.player.add_combo()
        self.assertEqual(self.player.combo_timer, COMBO_TIMEOUT)

    def test_melee_warns_then_hits_or_misses_once(self):
        for dodge in (False, True):
            enemy = Enemy(0, 0, 'crusher')
            self.player.x = 10
            self.assertIsNone(enemy.advance_attack(0.01, self.player))
            self.assertIsNone(enemy.advance_attack(0.3, self.player))
            self.player.x = 200 if dodge else 10
            enemy.update(0.1, self.player.x, 0, [enemy])
            self.assertEqual(enemy.x, 0)
            self.assertEqual(enemy.advance_attack(0.6, self.player), None if dodge else 'hit')
            self.assertGreater(enemy.hit_cooldown, 0)
            self.assertIsNone(enemy.advance_attack(0.2, self.player))

    def test_stun_interrupts_and_prism_locks_aim(self):
        enemy = Enemy(-100, 0, 'prism')
        self.game.enemies = [enemy]
        self.game.check_enemy_attacks(0.1)
        enemy.stun_timer = 1
        self.game.check_enemy_attacks(1)
        self.assertFalse(self.game.enemy_projectiles)
        enemy.stun_timer = 0
        self.game.check_enemy_attacks(0.1)
        self.player.y = 200
        self.game.check_enemy_attacks(enemy.windup_duration)
        shots = self.game.enemy_projectiles
        self.assertEqual(len(shots), 3)
        self.assertAlmostEqual(shots[1].dir_y, 0)
        self.assertLess(shots[0].dir_y, 0)
        self.assertGreater(shots[2].dir_y, 0)

    def test_exploder_gives_time_to_escape(self):
        enemy = Enemy(0, 0, 'exploder')
        enemy.take_damage(1000)
        self.game.on_enemy_killed(enemy)
        self.game.update_explosion_fuses(EXPLOSION_FUSE / 2)
        self.assertEqual(self.player.hp, self.player.max_hp)
        self.player.x = 200
        self.game.update_explosion_fuses(EXPLOSION_FUSE / 2)
        self.assertEqual(self.player.hp, self.player.max_hp)
        self.assertFalse(self.game.pending_explosions)

    def test_cleave_strikes_front_and_back_once(self):
        self.equip('cleave')
        self.game.enemies = [Enemy(x, 0, 'tank') for x in (40, 41, -63, -64, 350)]
        self.player.update_fist_attack(0.016)
        self.game.check_fist_attacks()
        self.game.check_fist_attacks()
        self.assertEqual(len(self.player.fist_hit_enemies), 1)
        self.assertEqual(self.player.fist_total_hits, 1)
        self.player.fist_total_hits = 3  # three landed swings; the next is a cleave
        self.player.update_fist_attack(1)
        self.game.check_fist_attacks()
        self.assertEqual(self.player.fist_hit_enemies, self.game.enemies[:4])
        self.assertEqual(self.player.fist_total_hits, 4)
        damage = self.player.damage_dealt
        self.game.check_fist_attacks()
        self.assertEqual(self.player.damage_dealt, damage)

    def test_empty_swings_do_not_build_or_refresh_the_fist_series(self):
        p = self.player
        for _ in range(8):
            p.update_fist_attack(0.7)
            self.game.check_fist_attacks()
            self.assertFalse(p.fist_is_mega)
        self.assertEqual((p.fist_total_hits, p.fist_combo_index, p.fist_combo_timer), (0, 0, 0))
        self.game.enemies = [Enemy(30, 0, 'tank')]
        self.game.check_fist_attacks()
        self.assertEqual((p.fist_total_hits, p.fist_combo_index), (1, 1))
        self.game.enemies.clear()
        for _ in range(2):
            p.update_fist_attack(0.7)
            self.game.check_fist_attacks()
        self.assertEqual((p.fist_total_hits, p.fist_combo_index), (1, 0))

    def test_utility_upgrades_and_translations(self):
        for key in ('combo_grace', 'ult_per_kill', 'hit_grace', 'boost_duration', 'dash_heal', 'cleave'):
            self.equip(key)
            for strings in TRANSLATIONS.values():
                for suffix in ('name', 'desc'):
                    self.assertIn(f'upgrade_{key}_{suffix}', strings)
        self.game.on_enemy_killed(Enemy(0, 0, 'ghoul'))
        self.assertEqual(self.player.combo_timer, COMBO_TIMEOUT + 0.75)
        self.assertEqual(self.player.ult_charge, 4)
        self.game.apply_item_effect('speed_boost')
        self.assertEqual(self.player.speed_boost_timer, SPEED_BOOST_DURATION + 2)
        self.player.take_damage(20)
        self.assertAlmostEqual(self.player.invincible_timer, 0.65)
        hp = self.player.hp
        self.game.enemies = [Enemy(30, 0, 'tank'), Enemy(35, 0, 'tank')]
        self.player.dash_attack_active = True
        self.game.check_dash_attack()
        self.assertEqual(self.player.hp, hp + 3)

    def test_boss_and_new_enemies_update_and_draw(self):
        self.game.enemies = [Boss(50, 0)] + [Enemy(45, 0, kind) for kind in ('prism', 'crusher', 'skirmisher')]
        with patch.object(self.game.achievement_manager, 'save'):
            for _ in range(4):
                self.game.update_playing(0.016, [])
                self.game.draw_playing()
