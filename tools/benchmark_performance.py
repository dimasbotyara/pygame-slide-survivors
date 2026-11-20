"""Reproducible CPU/headless microbenchmarks; not a hardware FPS guarantee.

Run from the repository root: python tools/benchmark_performance.py
"""
import argparse
import os
from pathlib import Path
import random
import statistics
import sys
import time

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from camera import Camera
from enemies import Enemy
from spatial import EnemyGrid
from world import World


def crowd(count):
    rng = random.Random(42)
    return [Enemy(rng.uniform(-1500, 1500), rng.uniform(-1000, 1000), 'zombie') for _ in range(count)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=100)
    parser.add_argument('--enemies', type=int, default=400)
    args = parser.parse_args()
    if args.frames < 1 or args.enemies < 1:
        parser.error('frames and enemies must be positive')
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    for quality in ('low', 'medium', 'high'):
        world, camera = World(42), Camera(1280, 720)
        config = {'terrain_quality': quality, 'biome_blend': 220, 'terrain_shading': True,
                  'slide_trails': True, 'decorations': True,
                  'decoration_density': 1, 'animated_decorations': True}
        frames = []
        for i in range(args.frames):
            camera.offset_x, camera.offset_y = i*24, i*3
            started = time.perf_counter()
            world.draw(screen, camera, i/60, config)
            frames.append((time.perf_counter()-started)*1000)
        p95 = sorted(frames)[min(len(frames)-1, int(.95*len(frames)))]
        print(f'Terrain {quality:6}: total={sum(frames):.1f}ms mean={statistics.mean(frames):.2f}ms '
              f'p95={p95:.2f}ms cold={frames[0]:.2f}ms')
    for indexed in (False, True):
        enemies = crowd(args.enemies)
        started = time.perf_counter()
        for _ in range(20):
            neighbors = EnemyGrid(enemies) if indexed else enemies
            for enemy in enemies:
                enemy.update(.016, 0, 0, neighbors)
                if indexed:
                    neighbors.update(enemy)
        print(f'Separation {"grid" if indexed else "list":4} ({args.enemies} enemies, 20 ticks): '
              f'{(time.perf_counter()-started)*1000:.1f}ms')
    pygame.quit()


if __name__ == '__main__':
    main()
