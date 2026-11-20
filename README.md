# 🧟 pygame-slide-survivors

Survivors-style arena roguelike on Pygame. Pick a hero, survive the hordes, level up, repeat.

## Features

- **Heroes** — pick your fighter from the `HEROES` registry
- **Enemy waves** with bosses, projectiles and spawners
- **Upgrades** between waves, XP orbs and dropped items
- Particles, camera system, world & UI
- Local **highscores**
- EN/RU localization

## Combat tips

- Leave the warning circle before the inner ring fills. Against a shooter, sidestep the aim line: it won’t track you during the wind-up. Exploders also leave a short fuse on death.
- **Perfect dodge** (all heroes): slide fully out of a melee ring when it flashes white in the last 0.16 seconds. Your glowing fists signal one charged cleave on the next swing, even without the Cleave upgrade. Charges do not stack.
- **Ice Trail** lays slippery ground only while sliding. Enemies keep their incoming heading there, so double back after they step onto it. Ice lasts 2/3/4 seconds at levels 1/2/3.
- Three aura cards offer different ways to deal with a crowd: **Repulsion** pushes nearby enemies every 2.5 seconds, **Siphon** drains the closest foe every 2 seconds and heals for a quarter of the HP taken, and **Stasis Field** slows nearby enemy shots by 20% per level.
- Watch for **Skirmishers** weaving in after 0:20, **Crushers** winding up wide slams after 1:15, and **Prisms** firing three-way volleys after 2:15.
- **Cleave** turns every fourth punch into a longer circular sweep with no target cap. **Second Wind** heals on the first hit of each dash attack.
- A bomb adds **5 seconds** to the time left on an active kill streak, even on an empty screen. A later kill won’t shorten that extra time.

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

The [bundled fonts and their licenses](assets/fonts/README.md) ship with the game, including Cyrillic, symbols, and monochrome Noto Emoji. No font downloads or system font configuration are needed at runtime.

Choose a fighter in **Heroes**, then start the run with **Play**. Use the arrow keys and Enter or click a menu button. **Pause → Surrender** finishes the run and submits its score to the same local leaderboard as a defeat.
