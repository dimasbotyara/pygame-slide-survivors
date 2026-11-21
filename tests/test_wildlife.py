import os
import unittest
import random
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from biomes import BIOMES
from consumables import TONICS
from enemies import Boss, Enemy
from items import DroppedItem, roll_drop
from main import Game
from translations import TRANSLATIONS
from world import World
from wildlife import RESIDENTS, RESIDENT_BY_BIOME, resident_sprite, HabitatFade
import pygame


class WildlifeTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        patcher = patch('settings_manager.SETTINGS_FILE', Path(folder.name) / 'settings.json')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.g = Game()
        self.g.start_new_game()
        self.g.world = World(3)
        self.g.spawner.world = self.g.world

    def test_residents_selected_at_spawn_point_not_player(self):
        g = self.g
        self.assertEqual(set(RESIDENT_BY_BIOME), {b.key for b in BIOMES})
        seen = set()
        with patch('enemies.random.random', return_value=0), patch('enemies.random.uniform', return_value=500):
            for i in range(150):
                x = i * 1536 + 1000
                resident = g.spawner.spawn_enemy(x, 0)
                self.assertEqual(resident.home_biome, g.world.biome_at(resident.x, resident.y).key)
                seen.add(resident.enemy_type)
                g.camera.offset_x = resident.x - 100
                resident.draw(g.screen, g.camera)
        self.assertEqual(seen, set(RESIDENTS))

    def test_crossing_boundary_is_never_a_player_kill(self):
        g = self.g
        # Locate an actual generated border, not a former fixed grid boundary.
        border = next(x for x in range(1, 20000) if g.world.biome_at(x-1, 0) != g.world.biome_at(x, 0))
        home = g.world.biome_at(border-1, 0).key
        resident = Enemy(border-1, 0, RESIDENT_BY_BIOME[home])
        resident.knockback_vx = 1000
        wanderer, boss = Enemy(1026, 50, 'zombie'), Boss(1030, 100)
        g.enemies = [resident, wanderer, boss]
        with patch('main.roll_drop') as roll:
            g.update_enemies(0.02)
            roll.assert_not_called()
        self.assertFalse(resident.alive)
        self.assertEqual(g.enemies, [wanderer, boss])
        self.assertEqual((g.player.enemies_killed, g.player.combo_count, g.player.ult_charge), (0, 0, 0))
        self.assertFalse(g.xp_orbs or g.dropped_items or g.corpse_positions or g.pending_explosions)

    def test_stunned_resident_outside_removed_but_local_kill_drops_loot(self):
        g = self.g
        kind = RESIDENT_BY_BIOME[g.world.biome_at(0, 0).key]
        x = next(x for x in range(100, 20000, 100) if g.world.biome_at(x, 0).key != g.world.biome_at(0, 0).key)
        local, outside = Enemy(0, 0, kind), Enemy(x, 0, kind)
        outside.stun_timer = 1
        g.enemies = [outside, local]
        g.update_enemies(0.01)
        self.assertEqual(g.enemies, [local])
        with patch('main.roll_drop', return_value='iron_acorn'):
            g.deal_damage_to_enemy(local, 10000)
        self.assertEqual((len(g.xp_orbs), g.player.enemies_killed), (1, 1))
        self.assertEqual([d.item_type for d in g.dropped_items], ['iron_acorn'])

    def test_all_residents_have_distinct_cached_gait_frames(self):
        for kind in RESIDENTS:
            with self.subTest(kind=kind):
                frames = [resident_sprite(kind, 15, False, frame) for frame in range(4)]
                self.assertNotEqual(pygame.image.tobytes(frames[1], 'RGBA'),
                                    pygame.image.tobytes(frames[3], 'RGBA'))
                self.assertIs(frames[1], resident_sprite(kind, 15, False, 1))
                resident = Enemy(0, 0, kind)
                resident.update(.2, 500, 0, [resident])
                self.assertNotEqual(resident.walk_frame, 0)
                # Attack wind-up stops gait without disabling the existing bob.
                resident.windup_left = .1
                resident.update(.1, 500, 0, [resident])
                self.assertEqual(resident.walk_frame, 0)

    def test_environment_fade_is_visual_only_and_expires(self):
        g = self.g
        home = g.world.biome_at(0, 0).key
        x = next(x for x in range(100, 20000, 100) if g.world.biome_at(x, 0).key != home)
        resident = Enemy(x, 0, RESIDENT_BY_BIOME[home])
        g.enemies = [resident]
        state = random.getstate()
        with patch.object(g.particle_manager, 'spawn_death_particles') as particles, patch('main.roll_drop') as drop:
            g.update_enemies(.01)
            particles.assert_not_called()
            drop.assert_not_called()
        self.assertEqual(random.getstate(), state)
        self.assertEqual(g.enemies, [])
        self.assertEqual(len(g.habitat_fades), 1)
        self.assertFalse(resident.alive)
        self.assertFalse(g.xp_orbs or g.dropped_items or g.corpse_positions or g.pending_explosions)
        self.assertEqual((g.player.enemies_killed, g.player.combo_count, g.player.ult_charge), (0, 0, 0))
        effect = g.habitat_fades[0]
        # Drawing and pausing do not advance the effect.
        effect.draw(g.screen, g.camera)
        g.state = 'paused'
        g.draw_paused()
        self.assertEqual(effect.elapsed, 0)
        g.update_enemies(HabitatFade.duration / 2)
        self.assertEqual(len(g.habitat_fades), 1)
        effect.draw(g.screen, g.camera)
        g.update_enemies(HabitatFade.duration / 2)
        self.assertFalse(g.habitat_fades)
        g.start_new_game()
        self.assertFalse(g.habitat_fades)

    def test_combat_death_keeps_existing_particles_without_habitat_fade(self):
        g = self.g
        kind = RESIDENT_BY_BIOME[g.world.biome_at(0, 0).key]
        resident = Enemy(0, 0, kind)
        g.enemies = [resident]
        with patch.object(g.particle_manager, 'spawn_death_particles') as particles:
            g.deal_damage_to_enemy(resident, 10000)
            particles.assert_called_once()
        g.update_enemies(.01)
        self.assertFalse(g.habitat_fades)
        self.assertEqual(g.player.enemies_killed, 1)
        self.assertEqual(len(g.xp_orbs), 1)

    def test_tonics_draw_collect_apply_and_expire(self):
        g, p = self.g, self.g.player
        getters = [p.get_armor, p.get_fist_damage, p.get_fist_attack_speed, p.get_crit_chance,
                   p.get_fist_range, p.get_fist_lifesteal, p.get_xp_multiplier, p.get_xp_radius,
                   p.get_slide_turn_speed, p.get_slide_initial_speed, p.get_fist_stun_chance,
                   p.get_slide_knockback_damage]
        baseline = [getter() for getter in getters]
        for key in TONICS:
            for lang in TRANSLATIONS.values():
                self.assertIn('TONIC_' + key, lang)
            g.dropped_items.append(DroppedItem(0, 0, key))
            g.dropped_items[-1].draw(g.screen, g.camera)
        permanent = dict(p.stats)
        g.update_items(0.01)
        self.assertFalse(g.dropped_items)
        self.assertEqual(set(p.tonic_timers), set(TONICS))
        self.assertTrue(all(getter() > old for getter, old in zip(getters, baseline)))
        g.draw_playing()
        p.update_tonics(3)
        g.apply_item_effect('iron_acorn')
        self.assertEqual(p.get_armor(), baseline[0] + 6)
        p.update_tonics(9)
        self.assertEqual(p.tonic_timers, {'iron_acorn': 1})
        p.stats['armor'] += 2  # real upgrades during a buff must survive expiration
        p.update_tonics(1)
        permanent['armor'] += 2
        self.assertEqual(p.stats, permanent)
        self.assertEqual([getter() for getter in getters], [baseline[0]+2] + baseline[1:])
        g.apply_item_effect('ruby_fang')
        g.start_new_game()
        self.assertFalse(g.player.tonic_timers)

    def test_normal_and_high_luck_drop_pools_include_tonics(self):
        for roll, luck in [(0.12, 0), (0.99, 10000)]:
            with patch('items.random.random', return_value=roll):
                self.assertIn(roll_drop(luck), TONICS)
        with patch('items.random.random', return_value=0.9):
            self.assertIsNone(roll_drop())
