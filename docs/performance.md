# CPU performance notes

These measurements were collected in the development sandbox with Python 3.11,
Pygame 2.6.1 and SDL's dummy video driver. They are **not measurements on the
HP Pavilion, Core 2 Duo, i7-7700 or either NVIDIA GPU**, and do not predict their
in-game FPS. Real display scaling, drivers, combat effects and other processes
add work that the benchmark does not model.

## What profiling found

A fixed-seed camera path (100 frames, +24/+3 world units per frame) originally
spent most of its world-render time sampling terrain. Under `cProfile`:

| Default world-render scenario | Before | After |
| --- | ---: | ---: |
| 100 moving frames, including cold generation | 2.352 s | 0.523 s |
| Function calls recorded | 4,063,952 | 517,554 |

This comparison includes **both** shared implementation optimizations and the
new default terrain quality (3×3 samples per tile instead of 5×5) and blend width
(220 instead of 340 world units). It must not be interpreted as a same-quality
rendering speedup. Select **High + Wide** to restore the previous sampling density
and blend width. Biome ownership, spawn habitats and seeded geography do not
change with graphics settings.

The previous enemy-separation routine visited every enemy for every enemy. The
new grid queries nearby cells, then applies the same overlap calculation in the
same order. The index is updated after each enemy moves, including knockback
across multiple cells. No enemy AI tick is skipped. Square roots are only taken
for overlapping pairs. Extremely dense crowds can still require many pair tests;
this is not a guarantee of linear performance in every arrangement.

## Reproduce current microbenchmarks

From the repository root, using the interpreter with the game's requirements:

```bash
python tools/benchmark_performance.py
python tools/benchmark_performance.py --frames 200 --enemies 600
```

The script uses seed 42, a 1280×720 logical canvas, a moving camera and a spread-out
uniform crowd. Terrain tests include decorations and shading. Timings are wall
clock, without profiling overhead. Example from this sandbox:

| Current renderer / separation | Time |
| --- | ---: |
| Low terrain, 100 frames | 178.6 ms total; 1.79 ms mean; 3.05 ms p95 |
| Medium terrain, 100 frames | 270.0 ms total; 2.70 ms mean; 5.47 ms p95 |
| High terrain, 100 frames | 545.1 ms total; 5.45 ms mean; 15.25 ms p95 |
| List separation, 400 enemies × 20 ticks | 629.6 ms |
| Grid separation, 400 enemies × 20 ticks | 34.3 ms |

The list comparison uses the **current** overlap routine, including its
square-root optimization. Both AI cases use identical initial positions and run
all movement ticks. These are isolated workloads, not full-game frame times.
Cold generation is included (24.73 / 55.01 / 142.93 ms for the first low / medium /
high terrain frame in this run). Timings vary between runs; tests deliberately
assert correctness and candidate counts rather than timing thresholds.

## Changes that do not reduce visual quality

- Cache deterministic noise lattice corners; bound noise, colour and tile caches.
- Avoid sorting regions, square roots and full Biome dataclass hashing for habitat
  queries. Colour blending still groups and mixes all relevant neighbouring biomes.
- Cache enemy/player shadow surfaces instead of allocating them each frame.
- Reuse scaled output surfaces and fitted HUD text; avoid a full canvas copy on
  every gameplay frame and use a smaller snapshot for the lobby hero animation.
- Use dynamic neighbour queries for separation without disabling distant AI.
- Remove all biome-entry notification work and the radar's terrain-colour sampler,
  as requested. The biome name remains above the monochrome minimap, even when
  legacy settings files contain the removed options.

## Tuning

For a Core 2 Duo-class laptop, try Low terrain, Narrow transitions, terrain shading
off, 25% or disabled decorations, animated decorations off, shadows off, fewer
particles, view culling on and radar pickups off. A 30 FPS cap is a useful target,
not a promise. Keep a comfortable display resolution; window resolution alone
does **not** reduce the fixed 1280×720 logical scene's simulation or rendering
work, although it affects presentation/scaling cost. Turn smooth scaling off if
that cost is significant. 1440×900 and Desktop resolution are available.

A stronger PC can use High terrain, Wide transitions, full animated decorations,
shading and shadows. Quality settings only change visuals, not enemy counts,
attack timing, spawn probabilities or rewards.

## Why not threads yet?

Pygame's window/event/render loop remains on the main thread. In conventional
CPython, Python-heavy AI threads contend on the GIL; merely moving AI to a thread
is not equivalent to parallel execution. Some native routines can release the
GIL, but that does not fix redundant Python-level pair checks or terrain queries.
Multiprocessing adds synchronization, data copying and lifecycle costs, especially
on a two-core machine. Profile again after the algorithmic fixes before choosing
a parallel architecture.

Automated checks cover seeded geography, equivalence to list-based separation,
negative coordinates, ghosts, bosses, large knockback, cached surfaces, removal
of legacy options, and input mapping for 4:3, 16:9, 16:10 and ultrawide windows.
Fullscreen behavior on real drivers and the target laptop still needs manual
validation.
