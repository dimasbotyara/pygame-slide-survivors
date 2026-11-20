import unittest

from biomes import BIOMES, prop_sprite
from world import World


class WorldTests(unittest.TestCase):
    def test_all_ten_regions_and_twenty_distinct_props_are_reachable(self):
        world = World(seed=3)
        regions = {world.biome_at(i * 3 * world.chunk_size, -0.5) for i in range(-5, 5)}
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
        region = world.biome_for_chunk(-3, 1)
        for x, y, kind, _, _ in first:
            self.assertEqual(world.biome_at(x, y), region)
            self.assertIn(kind, region.props + region.scatter)
