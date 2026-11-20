import unittest

from biomes import BIOMES, prop_sprite
from world import World


class WorldTests(unittest.TestCase):
    def test_all_ten_regions_and_twenty_distinct_props_are_reachable(self):
        world = World(seed=3)
        regions = {world.biome_at(i * 3 * world.chunk_size, -0.5) for i in range(-100, 101)}
        self.assertEqual(regions, set(BIOMES))
        self.assertEqual(len({region.ground for region in regions}), 10)
        self.assertEqual(len({kind for region in regions for kind in region.props}), 20)
        for region in regions:
            for kind in region.props:
                self.assertGreater(prop_sprite(kind, region.ink, 2, False).get_bounding_rect().width, 0)

    def test_revisiting_evicted_chunk_restores_its_scenery(self):
        world = World(seed=13)
        def contents():
            return [(d.x, d.y, d.deco_type, d.size, d.anim_offset) for d in world.get_decorations_for_chunk(-3, 1)]
        first = contents()
        for i in range(70):
            world.get_decorations_for_chunk(i, 0)
        self.assertNotIn((-3, 1), world.decoration_cache)
        self.assertEqual(first, contents())
        for x, y, kind, _, _ in first:
            region = world.biome_at(x, y)
            self.assertIn(kind, region.props + region.scatter)

    def test_seed_reproducibility_and_smooth_ground(self):
        a, b, c = World(42), World(42), World(43)
        points = [(x*117, x*-83) for x in range(-40, 40)]
        self.assertEqual([a.biome_at(*p) for p in points], [b.biome_at(*p) for p in points])
        self.assertNotEqual([a.biome_at(*p) for p in points], [c.biome_at(*p) for p in points])
        for x, y in points:
            self.assertEqual(a.ground_color_at(x, y), b.ground_color_at(x, y))
            self.assertLessEqual(max(abs(i-j) for i, j in zip(a.ground_color_at(x, y), a.ground_color_at(x+1, y))), 2)

    def test_regions_are_not_a_repeating_ten_chunk_sequence(self):
        world = World(7)
        row = [world.biome_at(x*100, 0).key for x in range(200)]
        lengths = []
        start = 0
        for i in range(1, len(row)):
            if row[i] != row[i-1]:
                lengths.append(i-start)
                start = i
        self.assertGreater(len(set(lengths)), 3)
        self.assertNotEqual(row[:100], row[100:])
