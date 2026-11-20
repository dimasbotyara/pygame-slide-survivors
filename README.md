![Slide Survivors — Slide. Strike. Survive.](assets/banners/slide-survivors-en.svg)

**English** · [Русский](README.ru.md)

# Slide Survivors

A top-down arena roguelike built with Pygame. Your hero punches automatically; you aim the fists and steer the slide. Slip past a crab just before its attack lands, turn back with a charged cleave, and collect the XP before the next wave reaches you.

## Start a run

From the project directory, with Python 3 and pip installed:

```bash
python -m pip install -r requirements.txt
python main.py
```

Choose English or Russian on first launch. Equip **Slider**, **Brawler**, **Spark**, or **Shadow** in **Heroes**, or cycle through them using the arrows on the lobby card. Choosing a hero doesn't start the clock: press **1 — Play** when you're ready. Fonts for both languages, symbols, and monochrome emoji ship with the game; no system font setup is needed.

## Controls

| Action | Input |
| --- | --- |
| Move and aim | WASD or arrow keys to move; mouse to aim |
| Slide | Hold Space or Shift; release to stop |
| Dash attack | Left-click just after a slide |
| Ultimate | Q or right-click when charged |
| Choose an upgrade | 1–3, click a card, or use Left/Right and Enter |
| Pause | Esc or P |

In numbered menus, the matching digit works like a click (top row or keypad). In Settings it changes the value on that row. **Pause → Surrender** ends the run and submits the result to the same local leaderboard as a defeat.

## Read the arena

- **Watch the warning, not just the enemy.** Step out of a melee ring before it fills. For a perfect dodge, *slide* across its edge when it flashes white in the final 0.16 seconds. Your fists glow: the next swing sweeps all around you. Shooters show their aim line before firing; step sideways rather than backing straight away.
- **Punch combos and kill streaks are different.** A punch advances the fist series only on contact, once even if it hits a crowd. The Cleave upgrade makes every fourth landed punch a sweep. A kill streak gives bonus XP; picking up a bomb adds **5 seconds** to the time remaining on an active streak, even when the screen is empty.
- **Build around how you move.** XP orbs earn levels and upgrade cards. Ice Trail makes pursuers keep their heading on slippery ground: turn back once they're on it. Repulsion pushes crowds away, Siphon drains the closest foe, and Stasis slows incoming shots. Bosses bring their own arena walls.
- **Pickups aren't permanent upgrades.** Alongside heals, magnets, bombs and speed boosts, enemies can drop **12 timed pickups**. Ember Pepper boosts punches, Ruby Fang lets hits heal you, and Comet Wax speeds up slides. These twelve effects last **8–12 seconds** of play. Different bonuses coexist; another copy refreshes its timer instead of doubling its strength. Watch the icons above the XP bar.

## Field guide

Ten biomes share one map. Each has its own ground palette, two signature floor decorations, and one native species. The order changes between runs, but the scenery stays put when you revisit a region. A shell on the beach is scenery, not loot.

| Biome | Resident | Biome | Resident |
| --- | --- | --- | --- |
| Wildflower Meadow | Clover Moth | Basalt Wastes | Cinder Slug |
| Amber Dunes | Sand Scorpion | Crystal Caverns | Echo Bat |
| Glacial Shelf | Rime Lynx | Tide Coast | Tide Crab |
| Reed Marsh | Reed Toad | Old Foundry | Gear Mite |
| Crimson Grove | Thorn Stag | Forgotten Ruins | Rune Wisp |

A resident dies if it crosses its biome boundary, even if you pushed it. That escape buys you breathing room, but **no kill credit, XP, combo, corpse, or item**. Ordinary enemies and bosses can follow you across the border.

## Development

- Run the tests: `python -m unittest discover -s tests`.
- For the optional trainer, run `python cheat_launcher.py` **instead of** `main.py`, then press F1 to open its overlay.
- The game code is [MIT-licensed](LICENSE). The [bundled fonts](assets/fonts/README.md) have their own licenses.
