# cheat_launcher.py — v2 — Ultimate Trainer for Slide Survivors
# Run this instead of main.py. Does NOT modify any source files.
#
#   python cheat_launcher.py
#
# Controls:
#   F1          Toggle trainer overlay (mouse-clickable)
#   F2-F11      Quick-toggle hotkeys (work with menu closed)
#   ~  (tilde)  Toggle dev console
#
# Inside overlay:
#   Mouse click on any item to toggle / cycle / execute
#   Arrow keys + Enter also work
#   Tab / Q/E   Switch tabs
#   Scroll      Navigate items

import math
import sys
import random
import pygame

# ── import game modules (untouched) ──────────────────────────────
import main as _game_main
import player as _player_mod
import enemies as _enemies_mod
import upgrades as _upgrades_mod
import items as _items_mod
from settings import *

# ═════════════════════════════════════════════════════════════════
#  GLOBALS
# ═════════════════════════════════════════════════════════════════
_TRAINER = None      # singleton, set once in patched run()
_ORIG    = {}        # original unpatched methods
_PATCHED = False


# ═════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════
def _fmt(v):
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(v))
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _safe_ratio(a, b):
    return 0.0 if b == 0 else a / b


def _rect_contains(rect, pos):
    return rect[0] <= pos[0] < rect[0] + rect[2] and rect[1] <= pos[1] < rect[1] + rect[3]


# ═════════════════════════════════════════════════════════════════
#  DEV CONSOLE
# ═════════════════════════════════════════════════════════════════
class DevConsole:
    MAX_LINES = 18

    def __init__(self):
        self.visible = False
        self.input_text = ""
        self.history = []          # list of (text, color)
        self.cmd_history = []
        self.cmd_index = -1
        self.font = pygame.font.SysFont("consolas", 18)

    def toggle(self):
        self.visible = not self.visible

    def log(self, text, color=WHITE):
        self.history.append((str(text), color))
        if len(self.history) > 200:
            self.history = self.history[-200:]

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type != pygame.KEYDOWN:
            return True            # eat all key events when open

        if event.key == pygame.K_ESCAPE:
            self.visible = False
            return True
        if event.key == pygame.K_RETURN:
            cmd = self.input_text.strip()
            if cmd:
                self.cmd_history.append(cmd)
                self.cmd_index = -1
                self.log("> " + cmd, CYAN)
                self._exec(cmd)
            self.input_text = ""
            return True
        if event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return True
        if event.key == pygame.K_UP:
            if self.cmd_history:
                if self.cmd_index == -1:
                    self.cmd_index = len(self.cmd_history) - 1
                else:
                    self.cmd_index = max(0, self.cmd_index - 1)
                self.input_text = self.cmd_history[self.cmd_index]
            return True
        if event.key == pygame.K_DOWN:
            if self.cmd_index >= 0:
                self.cmd_index += 1
                if self.cmd_index >= len(self.cmd_history):
                    self.cmd_index = -1
                    self.input_text = ""
                else:
                    self.input_text = self.cmd_history[self.cmd_index]
            return True

        if event.unicode and event.unicode.isprintable():
            self.input_text += event.unicode
        return True

    # ── command execution ──
    def _exec(self, cmd):
        t = _TRAINER
        if t is None:
            self.log("Trainer not ready", RED)
            return
        g = t.game
        p = getattr(g, "player", None)

        parts = cmd.split()
        c = parts[0].lower()

        try:
            if c == "help":
                for h in [
                    "help             show commands",
                    "god              toggle god mode",
                    "ohk              toggle one-hit-kill",
                    "heal [n]         heal player (default full)",
                    "hp <n>           set current hp",
                    "maxhp <n>        set max hp",
                    "level [n]        add n levels (default 1)",
                    "xp <n>           add xp",
                    "kill             kill all enemies",
                    "killnorm         kill non-boss enemies",
                    "spawn <type> [n] spawn enemy (zombie,ghoul,...,boss)",
                    "stat <k> <v>     set player.stats[k] = v",
                    "stats            show all player stats",
                    "speed <n>        set move speed mult",
                    "dmg <n>          set damage mult",
                    "time <n>         set time scale",
                    "tp <x> <y>       teleport to world coords",
                    "tpm              teleport to mouse",
                    "item <type>      use item (heal/magnet/bomb/speed_boost)",
                    "upgrade <id>     force apply upgrade by id",
                    "upgrades         list all upgrade ids",
                    "freeze           toggle freeze enemies",
                    "nospawn          toggle no enemy spawn",
                    "pos              print player position",
                    "clear            clear console",
                ]:
                    self.log(h, LIGHT_GRAY)

            elif c == "clear":
                self.history.clear()

            elif c == "god":
                t.god_mode = not t.god_mode
                self.log(f"God mode: {'ON' if t.god_mode else 'OFF'}", GREEN)

            elif c == "ohk":
                t.one_hit_kill = not t.one_hit_kill
                self.log(f"One-hit-kill: {'ON' if t.one_hit_kill else 'OFF'}", GREEN)

            elif c == "freeze":
                t.freeze_enemies = not t.freeze_enemies
                self.log(f"Freeze: {'ON' if t.freeze_enemies else 'OFF'}", GREEN)

            elif c == "nospawn":
                t.no_enemy_spawn = not t.no_enemy_spawn
                self.log(f"No spawn: {'ON' if t.no_enemy_spawn else 'OFF'}", GREEN)

            elif c == "heal":
                if not p: raise Exception("no player")
                amt = float(parts[1]) if len(parts) > 1 else p.get_max_hp()
                p.heal(amt)
                self.log(f"Healed {_fmt(amt)}", GREEN)

            elif c == "hp":
                if not p: raise Exception("no player")
                p.hp = float(parts[1])
                self.log(f"HP = {_fmt(p.hp)}", GREEN)

            elif c == "maxhp":
                if not p: raise Exception("no player")
                p.stats["max_hp"] = float(parts[1])
                p.max_hp = p.get_max_hp()
                p.hp = min(p.hp, p.max_hp)
                self.log(f"Max HP = {_fmt(p.max_hp)}", GREEN)

            elif c == "level":
                if not p: raise Exception("no player")
                n = int(parts[1]) if len(parts) > 1 else 1
                for _ in range(n):
                    p.gain_xp(p.xp_to_next + 1)
                self.log(f"+{n} levels -> now {p.level}", YELLOW)

            elif c == "xp":
                if not p: raise Exception("no player")
                n = int(parts[1])
                p.gain_xp(n)
                self.log(f"+{n} XP", YELLOW)

            elif c == "kill":
                t._kill_enemies(True)
                self.log("Killed all", ORANGE)

            elif c == "killnorm":
                t._kill_enemies(False)
                self.log("Killed normals", ORANGE)

            elif c == "spawn":
                etype = parts[1].lower()
                n = int(parts[2]) if len(parts) > 2 else 1
                t.action_spawn_enemies(etype, n)
                self.log(f"Spawned {n}x {etype}", CYAN)

            elif c == "stat":
                if not p: raise Exception("no player")
                k = parts[1]
                v = float(parts[2])
                if k in p.stats:
                    p.stats[k] = v
                    self.log(f"stats[{k}] = {_fmt(v)}", GREEN)
                else:
                    self.log(f"Unknown stat: {k}", RED)

            elif c == "stats":
                if not p: raise Exception("no player")
                for k, v in sorted(p.stats.items()):
                    self.log(f"  {k}: {_fmt(v)}", LIGHT_GRAY)

            elif c == "speed":
                t.move_speed_multiplier = float(parts[1])
                self.log(f"Move speed x{_fmt(t.move_speed_multiplier)}", CYAN)

            elif c == "dmg":
                t.damage_multiplier = float(parts[1])
                self.log(f"Damage x{_fmt(t.damage_multiplier)}", CYAN)

            elif c == "time":
                t.time_scale = float(parts[1])
                self.log(f"Time scale x{_fmt(t.time_scale)}", CYAN)

            elif c == "tp":
                if not p: raise Exception("no player")
                p.x = float(parts[1])
                p.y = float(parts[2])
                self.log(f"TP -> ({_fmt(p.x)}, {_fmt(p.y)})", CYAN)

            elif c == "tpm":
                t.action_teleport_to_mouse()
                self.log("Teleported to mouse", CYAN)

            elif c == "item":
                t.action_use_item(parts[1])
                self.log(f"Used item: {parts[1]}", PURPLE)

            elif c == "upgrade":
                uid = parts[1]
                t.action_force_upgrade(uid)

            elif c == "upgrades":
                um = _upgrades_mod.create_all_upgrades()
                for u in um:
                    lvl = ""
                    if u.max_level:
                        lvl = f" (max {u.max_level})"
                    self.log(f"  {u.upgrade_id}: {u.name}{lvl}", LIGHT_GRAY)

            elif c == "pos":
                if not p: raise Exception("no player")
                self.log(f"({_fmt(p.x)}, {_fmt(p.y)})", CYAN)

            elif c == "ult":
                t.act_fill_ult()
                self.log("⚡ Ultimate charged to 100%", GOLD)

            elif c == "hero":
                if len(parts) > 1:
                    t.act_switch_hero(parts[1].lower())
                else:
                    self.log("Usage: hero <slider|brawler|spark|shadow>", RED)

            elif c == "ach":
                sub = parts[1].lower() if len(parts) > 1 else ""
                if sub in ["unlockall", "all"]:
                    t.act_unlock_all_achievements()
                elif sub in ["clear", "reset"]:
                    t.act_reset_achievements()
                else:
                    self.log("Usage: ach <unlockall|clear>", RED)

            else:
                self.log(f"Unknown command: {c}. Type 'help'.", RED)

        except Exception as e:
            self.log(f"Error: {e}", RED)

    # ── draw ──
    def draw(self, screen):
        if not self.visible:
            return

        h = 420
        w = SCREEN_WIDTH - 40
        x, y = 20, SCREEN_HEIGHT - h - 20

        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((8, 8, 14, 230))
        pygame.draw.rect(panel, (100, 140, 200), (0, 0, w, h), 1)

        # title
        title = self.font.render("DEV CONSOLE  (~  to close,  'help' for commands)", True, GRAY)
        panel.blit(title, (10, 6))

        # history
        vis = self.history[-(self.MAX_LINES):]
        ly = 30
        for text, color in vis:
            ts = self.font.render(text, True, color)
            panel.blit(ts, (10, ly))
            ly += 20

        # input
        iy = h - 28
        pygame.draw.rect(panel, (20, 22, 30), (8, iy, w - 16, 22))
        prompt = self.font.render("> " + self.input_text + "_", True, WHITE)
        panel.blit(prompt, (12, iy + 2))

        screen.blit(panel, (x, y))


# ═════════════════════════════════════════════════════════════════
#  TRAINER  (v2 — mouse-clickable, stat editor, spawner, upgrades)
# ═════════════════════════════════════════════════════════════════
class Trainer:
    def __init__(self, game):
        self.game = game
        self.console = DevConsole()

        # ── UI state ──
        self.visible = False
        self.tab_index = 0
        self.scroll_offset = 0
        self.message = ""
        self.message_timer = 0.0

        # ── cheat flags ──
        self.god_mode = False
        self.no_damage = False
        self.auto_heal = False
        self.one_hit_kill = False
        self.always_crit = False
        self.always_mega = False
        self.lock_combo = False
        self.infinite_slide = False
        self.no_slide_cooldown = False
        self.freeze_enemies = False
        self.no_enemy_spawn = False
        self.no_boss_arena = False
        self.auto_collect_xp = False

        # ── multipliers ──
        self.damage_multiplier = 1.0
        self.move_speed_multiplier = 1.0
        self.attack_speed_multiplier = 1.0
        self.xp_multiplier = 1.0
        self.time_scale = 1.0

        # ── visual flags ──
        self.show_compact_hud = True
        self.show_enemy_hp = False
        self.show_hitboxes = False
        self.show_pickup_radius = False
        self.show_aura_radius = False
        self.show_offscreen_arrows = False

        # ── fonts ──
        self.f_big   = pygame.font.SysFont("consolas", 26, bold=True)
        self.f_med   = pygame.font.SysFont("consolas", 20)
        self.f_sm    = pygame.font.SysFont("consolas", 16)
        self.f_xs    = pygame.font.SysFont("consolas", 13)

        # ── menu geometry ──
        self.panel_x = 16
        self.panel_y = 16
        self.panel_w = 580
        self.row_h   = 28
        self.header_h = 110

        # ── build tabs ──
        self.tabs = self._build_tabs()
        self.sel = [0] * len(self.tabs)

    # ─────────────────────────────────────────────────────────────
    #  TAB DEFINITIONS
    # ─────────────────────────────────────────────────────────────
    def _build_tabs(self):
        return [
            {"name": "PLAYER", "items": [
                self._toggle("God mode",            "god_mode"),
                self._toggle("No damage",           "no_damage"),
                self._toggle("Auto heal",           "auto_heal"),
                self._choice("Move speed x",        "move_speed_multiplier",
                             [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]),
                self._toggle("Infinite slide",      "infinite_slide"),
                self._toggle("No slide cooldown",   "no_slide_cooldown"),
                self._action("Heal full",           self.act_heal_full),
                self._action("Teleport to mouse",   self.action_teleport_to_mouse),
            ]},
            {"name": "COMBAT", "items": [
                self._toggle("One-hit kill",        "one_hit_kill"),
                self._choice("Damage x",            "damage_multiplier",
                             [1.0, 2.0, 5.0, 10.0, 50.0, 100.0]),
                self._choice("Attack speed x",      "attack_speed_multiplier",
                             [1.0, 1.5, 2.0, 3.0, 5.0, 10.0]),
                self._toggle("Always crit",         "always_crit"),
                self._toggle("Always mega",         "always_mega"),
                self._toggle("Lock combo (999)",    "lock_combo"),
                self._action("Kill normal enemies", lambda: self._kill_enemies(False)),
                self._action("Kill ALL enemies",    lambda: self._kill_enemies(True)),
                self._action("Clear projectiles",   self.act_clear_proj),
            ]},
            {"name": "WORLD", "items": [
                self._toggle("Freeze enemies",      "freeze_enemies"),
                self._toggle("No enemy spawn",      "no_enemy_spawn"),
                self._toggle("No boss arena",       "no_boss_arena"),
                self._choice("Time scale",          "time_scale",
                             [0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]),
                self._action("Spawn BOSS",          lambda: self.action_spawn_enemies("boss", 1)),
                self._action("Spawn 10 zombies",    lambda: self.action_spawn_enemies("zombie", 10)),
                self._action("Spawn 5 ghoul",       lambda: self.action_spawn_enemies("ghoul", 5)),
                self._action("Spawn 3 tank",        lambda: self.action_spawn_enemies("tank", 3)),
                self._action("Spawn 5 shooter",     lambda: self.action_spawn_enemies("shooter", 5)),
                self._action("Spawn 5 berserker",   lambda: self.action_spawn_enemies("berserker", 5)),
                self._action("Spawn 3 necromancer", lambda: self.action_spawn_enemies("necromancer", 3)),
                self._action("Spawn 5 sprinter",    lambda: self.action_spawn_enemies("sprinter", 5)),
                self._action("Spawn 5 exploder",    lambda: self.action_spawn_enemies("exploder", 5)),
                self._action("Spawn 3 shielder",    lambda: self.action_spawn_enemies("shielder", 3)),
                self._action("Spawn 3 ghost",       lambda: self.action_spawn_enemies("ghost", 3)),
                self._action("Spawn 3 fatty",       lambda: self.action_spawn_enemies("fatty", 3)),
                self._action("Use Magnet",          lambda: self.action_use_item("magnet")),
                self._action("Use Bomb",            lambda: self.action_use_item("bomb")),
                self._action("Use Heal",            lambda: self.action_use_item("heal")),
                self._action("Use Speed Boost",     lambda: self.action_use_item("speed_boost")),
            ]},
            {"name": "HEROES", "items": [
                self._action("Switch to SLIDER",     lambda: self.act_switch_hero("slider")),
                self._action("Switch to BRAWLER",    lambda: self.act_switch_hero("brawler")),
                self._action("Switch to SPARK",      lambda: self.act_switch_hero("spark")),
                self._action("Switch to SHADOW",     lambda: self.act_switch_hero("shadow")),
                self._action("⚡ Fill Ultimate (100%)", self.act_fill_ult),
            ]},
            {"name": "ACHIEVEMENTS", "items": [
                self._action("🏆 Unlock ALL achievements", self.act_unlock_all_achievements),
                self._action("🔒 Reset achievements",       self.act_reset_achievements),
            ]},
            {"name": "PROGRESS", "items": [
                self._choice("XP multiplier x",     "xp_multiplier",
                             [1.0, 2.0, 5.0, 10.0, 50.0]),
                self._toggle("Auto collect XP",     "auto_collect_xp"),
                self._action("+1 Level",            lambda: self.act_add_levels(1)),
                self._action("+5 Levels",           lambda: self.act_add_levels(5)),
                self._action("+10 Levels",          lambda: self.act_add_levels(10)),
                self._action("+1000 XP",            lambda: self.act_add_xp(1000)),
                self._action("+10000 XP",           lambda: self.act_add_xp(10000)),
                self._action("Max ALL stats",       self.act_max_stats),
            ]},
            {"name": "UPGRADES", "items":
                self._build_upgrade_items()
            },
            {"name": "STATS", "items":
                self._build_stat_items()
            },
            {"name": "VISUAL", "items": [
                self._toggle("Compact HUD",         "show_compact_hud"),
                self._toggle("Enemy HP bars",       "show_enemy_hp"),
                self._toggle("Hitboxes",            "show_hitboxes"),
                self._toggle("Pickup radius",       "show_pickup_radius"),
                self._toggle("Aura radius",         "show_aura_radius"),
                self._toggle("Off-screen arrows",   "show_offscreen_arrows"),
            ]},
        ]

    # ── item builders ──
    def _toggle(self, label, attr):
        return {"type": "toggle", "label": label, "attr": attr}

    def _choice(self, label, attr, values):
        return {"type": "choice", "label": label, "attr": attr, "values": values}

    def _action(self, label, fn):
        return {"type": "action", "label": label, "fn": fn}

    def _stat_item(self, key):
        return {"type": "stat", "label": key, "key": key}

    def _upgrade_item(self, uid, name):
        return {"type": "upgrade", "label": f"{name}", "uid": uid}

    def _build_stat_items(self):
        keys = [
            "max_hp","hp_regen","move_speed","armor","xp_radius","luck",
            "damage","attack_speed","attack_range","crit_chance","crit_multiplier","target_count",
            "fist_combo_hits","fist_lifesteal","fist_stun_chance","fist_rage",
            "fist_ground_slam","fist_counter_attack","fist_arc_bonus","fist_wave","fist_xp_pull",
            "slide_speed","slide_duration","slide_cooldown","slide_damage",
            "slide_knockback_radius","slide_charges","slide_kill_reset_chance",
            "slide_turn_speed","slide_invincibility_after","slide_electric_trail","slide_shockwave",
            "xp_multiplier","drop_chance","heal_effectiveness",
            "aura_damage","aura_slow","block_chance","thorns",
            "projectile_count","projectile_spread","effect_duration","pierce",
        ]
        return [self._stat_item(k) for k in keys]

    def _build_upgrade_items(self):
        all_ups = _upgrades_mod.create_all_upgrades()
        return [self._upgrade_item(u.upgrade_id, u.name) for u in all_ups]

    # ─────────────────────────────────────────────────────────────
    #  CUR ITEMS / SELECTION helpers
    # ─────────────────────────────────────────────────────────────
    def _items(self):
        return self.tabs[self.tab_index]["items"]

    def _sel(self):
        items = self._items()
        if not items:
            return 0
        return _clamp(self.sel[self.tab_index], 0, len(items) - 1)

    def _cur(self):
        items = self._items()
        if not items:
            return None
        return items[self._sel()]

    # ─────────────────────────────────────────────────────────────
    #  MESSAGES
    # ─────────────────────────────────────────────────────────────
    def _msg(self, text, color=CYAN):
        self.message = text
        self.message_timer = 2.5
        pm = getattr(self.game, "particle_manager", None)
        if pm:
            try:
                pm.add_message(text, color)
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────
    #  ACTIONS
    # ─────────────────────────────────────────────────────────────
    def _need_player(self):
        p = getattr(self.game, "player", None)
        if p is None:
            self._msg("Start a run first", RED)
        return p

    def act_heal_full(self):
        p = self._need_player()
        if p:
            p.hp = p.get_max_hp()
            self._msg("HP full", GREEN)

    def action_teleport_to_mouse(self):
        p = self._need_player()
        cam = getattr(self.game, "camera", None)
        if not p or cam is None:
            return
        mx, my = pygame.mouse.get_pos()
        wx, wy = cam.reverse(mx, my)
        p.x, p.y = float(wx), float(wy)
        self._msg("Teleported", CYAN)

    def act_add_xp(self, n):
        p = self._need_player()
        if p:
            p.gain_xp(n)
            self._msg(f"+{n} XP", YELLOW)

    def act_add_levels(self, n):
        p = self._need_player()
        if not p:
            return
        for _ in range(n):
            p.gain_xp(p.xp_to_next + 1)
        self._msg(f"+{n} level(s) -> {p.level}", YELLOW)

    def act_switch_hero(self, hero_id):
        p = self._need_player()
        if not p:
            return
        from heroes import HEROES
        if hero_id in HEROES:
            h = HEROES[hero_id]
            p.hero_id = hero_id
            p.color = h["color"]
            p.outline_color = h["outline_color"]
            self._msg(f"Switched hero to: {hero_id.upper()}", CYAN)

    def act_fill_ult(self):
        p = self._need_player()
        if p:
            p.ult_charge = 100.0
            self._msg("⚡ Ultimate 100% Ready!", GOLD)

    def act_unlock_all_achievements(self):
        g = self.game
        ach = getattr(g, "achievement_manager", None)
        if ach:
            from achievements import ACHIEVEMENTS_LIST
            for aid in ACHIEVEMENTS_LIST:
                ach.unlock(aid)
            self._msg("🏆 All Achievements Unlocked!", GOLD)

    def act_reset_achievements(self):
        g = self.game
        ach = getattr(g, "achievement_manager", None)
        if ach:
            ach.unlocked = set()
            ach.save()
            self._msg("🔒 Achievements Reset", LIGHT_GRAY)

    def act_clear_proj(self):
        projs = getattr(self.game, "enemy_projectiles", None)
        if projs is None:
            return
        c = len(projs)
        projs.clear()
        self._msg(f"Cleared {c} projectiles", CYAN)

    def _kill_enemies(self, include_bosses):
        g = self.game
        if getattr(g, "player", None) is None:
            self._msg("No active run", RED)
            return
        killed = 0
        for e in list(g.enemies):
            if not getattr(e, "alive", False):
                continue
            if not include_bosses and getattr(e, "is_boss", False):
                continue
            try:
                e.take_damage(10**9)
            except Exception:
                pass
            if getattr(e, "alive", True):
                e.alive = False
            try:
                g.on_enemy_killed(e)
            except Exception:
                pass
            killed += 1
        self._msg(f"Killed {killed}", ORANGE)

    def action_spawn_enemies(self, etype, count):
        g = self.game
        p = self._need_player()
        if not p:
            return
        spawner = getattr(g, "spawner", None)
        diff = getattr(spawner, "difficulty_multiplier", 1.0) if spawner else 1.0

        for _ in range(count):
            angle = random.random() * math.pi * 2
            dist = random.uniform(200, 500)
            sx = p.x + math.cos(angle) * dist
            sy = p.y + math.sin(angle) * dist

            if etype == "boss":
                e = _enemies_mod.Boss(sx, sy, diff)
                e.set_arena_center(p.x, p.y)
            else:
                if etype not in ENEMY_TYPES:
                    self._msg(f"Unknown type: {etype}", RED)
                    return
                e = _enemies_mod.Enemy(sx, sy, etype, diff)
            g.enemies.append(e)

        self._msg(f"Spawned {count}x {etype}", CYAN)

    def action_use_item(self, item_type):
        if getattr(self.game, "player", None) is None:
            self._msg("No active run", RED)
            return
        try:
            self.game.apply_item_effect(item_type)
            self._msg(f"Item: {item_type}", PURPLE)
        except Exception:
            self._msg(f"Failed: {item_type}", RED)

    def action_force_upgrade(self, uid):
        p = self._need_player()
        if not p:
            return
        um = getattr(self.game, "upgrade_manager", None)
        if um is None:
            self._msg("No upgrade manager", RED)
            return
        u = um.upgrade_map.get(uid)
        if u is None:
            self._msg(f"Unknown upgrade: {uid}", RED)
            return
        if not u.can_upgrade():
            u.current_level = 0
        u.apply(p)
        self._msg(f"Applied: {u.name} (lv {u.current_level})", GREEN)
        self.console.log(f"Upgrade {uid} -> lv {u.current_level}", GREEN)

    def act_max_stats(self):
        p = self._need_player()
        if not p:
            return
        boosts = {
            "max_hp": 5000, "hp_regen": 50.0, "move_speed": 400, "armor": 50,
            "xp_radius": 500, "luck": 100, "damage": 1500, "attack_speed": 600,
            "attack_range": 250, "crit_chance": 100, "crit_multiplier": 900,
            "target_count": 20, "fist_combo_hits": 4, "fist_lifesteal": 50,
            "fist_stun_chance": 100, "fist_rage": 100, "fist_ground_slam": 5,
            "fist_counter_attack": 100, "fist_arc_bonus": 180, "fist_wave": 5,
            "fist_xp_pull": 5, "slide_speed": 300, "slide_duration": 200,
            "slide_cooldown": 95, "slide_damage": 1000, "slide_knockback_radius": 200,
            "slide_charges": 20, "slide_kill_reset_chance": 100, "slide_turn_speed": 400,
            "slide_invincibility_after": 5.0, "slide_electric_trail": 5,
            "slide_shockwave": 5, "xp_multiplier": 500, "drop_chance": 100,
            "heal_effectiveness": 300, "aura_damage": 1000.0, "aura_slow": 90,
            "block_chance": 100, "thorns": 500, "projectile_count": 10,
            "projectile_spread": 100, "effect_duration": 300, "pierce": 10,
        }
        for k, v in boosts.items():
            if k in p.stats:
                p.stats[k] = max(p.stats[k], v)
        p.max_hp = p.get_max_hp()
        p.hp = p.max_hp
        p.slide_max_charges = p.get_slide_max_charges()
        p.slide_charges = p.slide_max_charges
        self._msg("All stats maxed!", GOLD)

    # ─────────────────────────────────────────────────────────────
    #  ITEM VALUE HELPERS
    # ─────────────────────────────────────────────────────────────
    def _item_value_text(self, item):
        t = item["type"]
        if t == "toggle":
            return "ON" if getattr(self, item["attr"]) else "OFF"
        if t == "choice":
            return _fmt(getattr(self, item["attr"]))
        if t == "action":
            return ">>>"
        if t == "stat":
            p = getattr(self.game, "player", None)
            if p:
                return _fmt(p.stats.get(item["key"], 0))
            return "---"
        if t == "upgrade":
            um = getattr(self.game, "upgrade_manager", None)
            if um:
                u = um.upgrade_map.get(item["uid"])
                if u:
                    ml = f"/{u.max_level}" if u.max_level else ""
                    return f"Lv {u.current_level}{ml}"
            return "---"
        return ""

    def _item_value_color(self, item):
        t = item["type"]
        if t == "toggle":
            return GREEN if getattr(self, item["attr"]) else (120, 120, 120)
        if t == "choice":
            v = getattr(self, item["attr"])
            return YELLOW if v != 1.0 else WHITE
        if t == "stat":
            return CYAN
        if t == "upgrade":
            return ORANGE
        return WHITE

    # ─────────────────────────────────────────────────────────────
    #  INTERACT (activate / cycle)
    # ─────────────────────────────────────────────────────────────
    def _activate(self, item, direction=1):
        t = item["type"]
        if t == "toggle":
            v = not getattr(self, item["attr"])
            setattr(self, item["attr"], v)
            self._msg(f"{item['label']}: {'ON' if v else 'OFF'}")
        elif t == "choice":
            vals = item["values"]
            cur = getattr(self, item["attr"])
            idx = min(range(len(vals)), key=lambda i: abs(vals[i] - cur))
            idx = (idx + direction) % len(vals)
            setattr(self, item["attr"], vals[idx])
            self._msg(f"{item['label']} = {_fmt(vals[idx])}")
        elif t == "action":
            item["fn"]()
        elif t == "stat":
            self._adjust_stat(item["key"], direction)
        elif t == "upgrade":
            self.action_force_upgrade(item["uid"])

    def _adjust_stat(self, key, direction):
        p = self._need_player()
        if not p:
            return
        cur = p.stats.get(key, 0)
        # determine step
        if isinstance(cur, float) and abs(cur) < 50:
            step = 1.0
        elif abs(cur) < 20:
            step = 1
        elif abs(cur) < 100:
            step = 5
        elif abs(cur) < 500:
            step = 25
        else:
            step = 100

        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT]:
            step *= 10

        new_val = cur + step * direction
        if isinstance(cur, int):
            new_val = int(new_val)
        p.stats[key] = new_val

        # refresh derived values
        p.max_hp = p.get_max_hp()
        p.hp = min(p.hp, p.max_hp)
        p.slide_max_charges = p.get_slide_max_charges()
        p.slide_charges = min(p.slide_charges, p.slide_max_charges)

        self._msg(f"{key} = {_fmt(new_val)}")

    # ─────────────────────────────────────────────────────────────
    #  EVENT HANDLING
    # ─────────────────────────────────────────────────────────────
    def handle_events(self, events):
        for event in events:
            # console gets first priority
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                self.console.toggle()
                continue
            if self.console.visible:
                self.console.handle_event(event)
                continue

            if event.type == pygame.KEYDOWN:
                self._on_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse(event)

    def _on_key(self, event):
        k = event.key

        if k == pygame.K_F1:
            self.visible = not self.visible
            self.scroll_offset = 0
            self._msg(f"Trainer: {'OPEN' if self.visible else 'CLOSED'}")
            return

        if self.visible:
            items = self._items()
            if k == pygame.K_ESCAPE:
                self.visible = False
            elif k in (pygame.K_TAB, pygame.K_e):
                self.tab_index = (self.tab_index + 1) % len(self.tabs)
                self.scroll_offset = 0
            elif k == pygame.K_q:
                self.tab_index = (self.tab_index - 1) % len(self.tabs)
                self.scroll_offset = 0
            elif k == pygame.K_UP:
                self.sel[self.tab_index] = (self._sel() - 1) % len(items) if items else 0
                self._ensure_visible()
            elif k == pygame.K_DOWN:
                self.sel[self.tab_index] = (self._sel() + 1) % len(items) if items else 0
                self._ensure_visible()
            elif k == pygame.K_LEFT:
                c = self._cur()
                if c:
                    self._activate(c, -1)
            elif k == pygame.K_RIGHT:
                c = self._cur()
                if c:
                    self._activate(c, 1)
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                c = self._cur()
                if c:
                    self._activate(c, 1)
            return

        # quick hotkeys (menu closed)
        hotkeys = {
            pygame.K_F2:  ("god_mode",        "God mode"),
            pygame.K_F3:  ("one_hit_kill",     "One-hit kill"),
            pygame.K_F4:  ("freeze_enemies",   "Freeze"),
            pygame.K_F5:  ("no_enemy_spawn",   "No spawn"),
            pygame.K_F6:  ("auto_collect_xp",  "Auto XP"),
        }
        if k in hotkeys:
            attr, label = hotkeys[k]
            v = not getattr(self, attr)
            setattr(self, attr, v)
            self._msg(f"{label}: {'ON' if v else 'OFF'}")
            return

        actions = {
            pygame.K_F7:  lambda: self._kill_enemies(False),
            pygame.K_F8:  lambda: self.act_add_levels(1),
            pygame.K_F9:  lambda: self.act_heal_full(),
            pygame.K_F10: lambda: self.act_max_stats(),
            pygame.K_F11: lambda: self.action_teleport_to_mouse(),
        }
        if k in actions:
            actions[k]()

    def _on_mouse(self, event):
        if not self.visible:
            return
        if event.button == 4:      # scroll up
            self.scroll_offset = max(0, self.scroll_offset - 1)
            return
        if event.button == 5:      # scroll down
            self.scroll_offset += 1
            return
        if event.button != 1:
            return

        mx, my = event.pos
        px, py = self.panel_x, self.panel_y

        # tab click
        tab_y = py + 72
        tx = px + 12
        for i, tab in enumerate(self.tabs):
            tw = max(70, len(tab["name"]) * 10 + 20)
            if _rect_contains((tx, tab_y, tw, 28), (mx, my)):
                self.tab_index = i
                self.scroll_offset = 0
                return
            tx += tw + 6

        # item click
        items = self._items()
        start_y = py + self.header_h
        max_vis = self._max_visible()
        for vi in range(max_vis):
            idx = vi + self.scroll_offset
            if idx >= len(items):
                break
            iy = start_y + vi * self.row_h
            row_rect = (px + 12, iy, self.panel_w - 24, self.row_h - 2)
            if _rect_contains(row_rect, (mx, my)):
                self.sel[self.tab_index] = idx
                # left half = activate, right half = maybe cycle backwards
                mid_x = px + self.panel_w // 2
                direction = 1 if mx >= mid_x else -1
                if items[idx]["type"] in ("toggle", "action", "upgrade"):
                    direction = 1
                self._activate(items[idx], direction)
                return

    def _max_visible(self):
        avail = SCREEN_HEIGHT - self.panel_y - self.header_h - 50
        return max(1, avail // self.row_h)

    def _ensure_visible(self):
        s = self._sel()
        mv = self._max_visible()
        if s < self.scroll_offset:
            self.scroll_offset = s
        elif s >= self.scroll_offset + mv:
            self.scroll_offset = s - mv + 1

    # ─────────────────────────────────────────────────────────────
    #  UPDATE (called every frame before game update)
    # ─────────────────────────────────────────────────────────────
    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt

        p = getattr(self.game, "player", None)
        if p is None:
            return

        if self.god_mode or self.no_damage:
            p.invincible_timer = max(p.invincible_timer, 0.25)
        if self.god_mode:
            p.hp = p.get_max_hp()
        if self.auto_heal:
            p.hp = min(p.hp + p.get_max_hp() * 2.0 * dt, p.get_max_hp())
        if self.infinite_slide:
            p.slide_max_charges = p.get_slide_max_charges()
            p.slide_charges = p.slide_max_charges
            p.slide_cooldown_timer = 0.0
        if self.no_slide_cooldown:
            p.slide_cooldown_timer = 0.0
        if self.lock_combo:
            p.combo_count = max(p.combo_count, 999)
            p.combo_timer = 999.0
        if self.auto_collect_xp:
            for orb in getattr(self.game, "xp_orbs", []):
                orb.being_collected = True
        if self.freeze_enemies:
            for proj in getattr(self.game, "enemy_projectiles", []):
                proj.alive = False

    def post_update(self, dt):
        p = getattr(self.game, "player", None)
        if p is None:
            return
        if self.god_mode:
            p.hp = p.get_max_hp()
        if self.infinite_slide:
            p.slide_charges = p.get_slide_max_charges()
            p.slide_cooldown_timer = 0.0

    # ─────────────────────────────────────────────────────────────
    #  ACTIVE CHEAT LABELS (for compact HUD)
    # ─────────────────────────────────────────────────────────────
    def _active_labels(self):
        out = []
        flags = [
            ("god_mode","God"),("no_damage","NoDmg"),("auto_heal","AutoHeal"),
            ("one_hit_kill","OHK"),("always_crit","Crit"),("always_mega","Mega"),
            ("lock_combo","Combo"),("infinite_slide","InfSlide"),
            ("no_slide_cooldown","SlideCD0"),("freeze_enemies","Freeze"),
            ("no_enemy_spawn","NoSpawn"),("no_boss_arena","NoArena"),
            ("auto_collect_xp","AutoXP"),
        ]
        for attr, label in flags:
            if getattr(self, attr):
                out.append(label)
        mults = [
            ("damage_multiplier","Dmg"),("move_speed_multiplier","Spd"),
            ("attack_speed_multiplier","AS"),("xp_multiplier","XP"),
            ("time_scale","Time"),
        ]
        for attr, label in mults:
            v = getattr(self, attr)
            if v != 1.0:
                out.append(f"{label}x{_fmt(v)}")
        return out

    # ─────────────────────────────────────────────────────────────
    #  DRAW  — OVERLAY
    # ─────────────────────────────────────────────────────────────
    def draw_overlay(self, screen):
        if self.visible:
            self._draw_menu(screen)
        elif self.show_compact_hud:
            self._draw_compact_hud(screen)

        # message bar
        if self.message_timer > 0 and self.message:
            w = min(600, SCREEN_WIDTH - 40)
            box = pygame.Surface((w, 34), pygame.SRCALPHA)
            box.fill((10, 10, 10, 200))
            txt = self.f_med.render(self.message, True, WHITE)
            box.blit(txt, (12, 7))
            screen.blit(box, ((SCREEN_WIDTH - w) // 2, SCREEN_HEIGHT - 55))

        self.console.draw(screen)

    # ── full menu ──
    def _draw_menu(self, screen):
        px, py = self.panel_x, self.panel_y
        pw = self.panel_w
        max_vis = self._max_visible()
        items = self._items()
        vis_count = min(max_vis, len(items) - self.scroll_offset) if items else 0
        ph = self.header_h + vis_count * self.row_h + 42

        # background
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((10, 12, 18, 235))
        pygame.draw.rect(panel, (70, 120, 200), (0, 0, pw, ph), 2)

        # title
        self._text(panel, self.f_big, "SLIDE SURVIVORS TRAINER v2", 14, 10, CYAN)
        self._text(panel, self.f_xs, "F1 close | Arrows/Mouse navigate | Left/Right adjust | ~/tilde console", 14, 40, GRAY)
        self._text(panel, self.f_xs, "Shift+Left/Right = x10 step for stat editor", 14, 54, GRAY)

        # tabs
        tab_y = 72
        tx = 12
        for i, tab in enumerate(self.tabs):
            tw = max(70, len(tab["name"]) * 10 + 20)
            bg = (35, 75, 140) if i == self.tab_index else (28, 30, 40)
            pygame.draw.rect(panel, bg, (tx, tab_y, tw, 26), border_radius=4)
            pygame.draw.rect(panel, (100, 140, 210), (tx, tab_y, tw, 26), 1, border_radius=4)
            self._text(panel, self.f_xs, tab["name"], tx + 8, tab_y + 6, WHITE)
            tx += tw + 6

        # items
        start_y = self.header_h
        for vi in range(vis_count):
            idx = vi + self.scroll_offset
            if idx >= len(items):
                break
            item = items[idx]
            iy = start_y + vi * self.row_h
            selected = idx == self._sel()

            bg = (40, 50, 70, 230) if selected else (20, 22, 30, 210)
            pygame.draw.rect(panel, bg, (12, iy, pw - 24, self.row_h - 2), border_radius=4)

            # label
            self._text(panel, self.f_med, item["label"], 22, iy + 4, WHITE)

            # value
            val = self._item_value_text(item)
            vc = self._item_value_color(item)
            self._text(panel, self.f_med, val, pw - 160, iy + 4, vc)

            # arrows for adjustable items
            if item["type"] in ("choice", "stat") and selected:
                self._text(panel, self.f_med, "<", pw - 180, iy + 4, YELLOW)
                self._text(panel, self.f_med, ">", pw - 30, iy + 4, YELLOW)

        # scroll indicator
        if items and len(items) > max_vis:
            total = len(items)
            bar_h = max(20, int(ph * max_vis / total))
            bar_y = int((ph - bar_h) * self.scroll_offset / max(1, total - max_vis))
            pygame.draw.rect(panel, (60, 80, 120), (pw - 10, bar_y, 6, bar_h), border_radius=3)

        # active cheats footer
        active = ", ".join(self._active_labels()) or "none"
        fy = ph - 24
        self._text(panel, self.f_xs, f"Active: {active}", 14, fy, ORANGE)

        screen.blit(panel, (px, py))

    # ── compact HUD ──
    def _draw_compact_hud(self, screen):
        active = self._active_labels()
        p = getattr(self.game, "player", None)

        lines = []
        if active:
            lines.append(("TRAINER [F1]", CYAN))
            for a in active:
                lines.append((a, ORANGE))

        if p:
            lines.append(("", WHITE))
            lines.append((f"HP {int(p.hp)}/{int(p.get_max_hp())}  LVL {p.level}", WHITE))
            lines.append((f"Kills {p.enemies_killed}  Combo {p.combo_count}", WHITE))
            lines.append((f"Enemies {len(self.game.enemies)}  {int(self.game.game_time)}s", WHITE))

        if not lines:
            return

        lh = 17
        w = 300
        h = 10 + len(lines) * lh + 6
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((8, 10, 14, 170))
        pygame.draw.rect(box, (80, 120, 180), (0, 0, w, h), 1)

        y = 6
        for text, color in lines:
            if text:
                self._text(box, self.f_sm, text, 8, y, color)
            y += lh

        screen.blit(box, (8, 8))

    # ─────────────────────────────────────────────────────────────
    #  DRAW  — WORLD VISUALS (hitboxes, HP bars, arrows, etc.)
    # ─────────────────────────────────────────────────────────────
    def draw_world(self, screen):
        g = self.game
        if g.state not in ("playing", "paused", "upgrading", "game_over"):
            return
        p = getattr(g, "player", None)
        cam = getattr(g, "camera", None)
        if not p or not cam:
            return

        psx, psy = cam.apply(p.x, p.y)
        psx, psy = int(psx), int(psy)

        if self.show_pickup_radius:
            r = int(p.get_xp_radius())
            pygame.draw.circle(screen, (60, 180, 230), (psx, psy), r, 1)

        if self.show_aura_radius:
            if p.stats["aura_damage"] > 0:
                pygame.draw.circle(screen, (255, 100, 0), (psx, psy), 80, 1)
            if p.stats["aura_slow"] > 0:
                pygame.draw.circle(screen, (50, 100, 255), (psx, psy), 100, 1)

        if self.show_hitboxes:
            pygame.draw.circle(screen, CYAN, (psx, psy), int(p.size), 1)
            atk = p.get_fist_attack_area()
            if atk:
                pygame.draw.circle(screen, YELLOW, (psx, psy), int(atk["range"]), 1)
            dash = p.get_dash_attack_area()
            if dash:
                pygame.draw.circle(screen, ORANGE, (psx, psy), int(dash["range"]), 1)
            for pr in g.enemy_projectiles:
                sx, sy = cam.apply(pr.x, pr.y)
                pygame.draw.circle(screen, ORANGE, (int(sx), int(sy)), int(pr.size), 1)

        for enemy in g.enemies:
            if not getattr(enemy, "alive", False):
                continue
            sx, sy = cam.apply(enemy.x, enemy.y)
            sx, sy = int(sx), int(sy)
            on_screen = -60 < sx < SCREEN_WIDTH + 60 and -60 < sy < SCREEN_HEIGHT + 60

            if on_screen:
                if self.show_hitboxes:
                    c = PURPLE if getattr(enemy, "is_boss", False) else RED
                    pygame.draw.circle(screen, c, (sx, sy), int(enemy.size), 1)

                if self.show_enemy_hp and hasattr(enemy, "hp") and hasattr(enemy, "max_hp"):
                    bw = max(28, int(enemy.size * 2.6))
                    bh = 5
                    bx = sx - bw // 2
                    by = sy - int(enemy.size) - 14
                    ratio = _clamp(_safe_ratio(enemy.hp, enemy.max_hp), 0, 1)
                    pygame.draw.rect(screen, (20, 20, 20), (bx, by, bw, bh))
                    pygame.draw.rect(screen, RED, (bx, by, bw, bh), 1)
                    fill = max(0, int((bw - 2) * ratio))
                    pygame.draw.rect(screen, GREEN, (bx + 1, by + 1, fill, bh - 2))
                    # hp text for bosses
                    if getattr(enemy, "is_boss", False):
                        hp_t = self.f_xs.render(f"{int(enemy.hp)}", True, WHITE)
                        screen.blit(hp_t, (bx, by - 14))
            else:
                # off-screen arrow
                if self.show_offscreen_arrows:
                    self._draw_arrow_to(screen, sx, sy, enemy)

    def _draw_arrow_to(self, screen, sx, sy, enemy):
        margin = 40
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        dx = sx - cx
        dy = sy - cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return
        nx, ny = dx / dist, dy / dist

        # find edge point
        ax = cx + nx * (SCREEN_WIDTH // 2 - margin)
        ay = cy + ny * (SCREEN_HEIGHT // 2 - margin)
        ax = _clamp(ax, margin, SCREEN_WIDTH - margin)
        ay = _clamp(ay, margin, SCREEN_HEIGHT - margin)

        color = PURPLE if getattr(enemy, "is_boss", False) else RED
        size = 10 if getattr(enemy, "is_boss", False) else 6

        # triangle
        angle = math.atan2(ny, nx)
        p1 = (int(ax + math.cos(angle) * size), int(ay + math.sin(angle) * size))
        p2 = (int(ax + math.cos(angle + 2.5) * size * 0.7), int(ay + math.sin(angle + 2.5) * size * 0.7))
        p3 = (int(ax + math.cos(angle - 2.5) * size * 0.7), int(ay + math.sin(angle - 2.5) * size * 0.7))
        pygame.draw.polygon(screen, color, [p1, p2, p3])

    # ── helper ──
    def _text(self, surface, font, text, x, y, color=WHITE):
        surface.blit(font.render(str(text), True, color), (x, y))


# ═════════════════════════════════════════════════════════════════
#  MONKEY PATCHES
# ═════════════════════════════════════════════════════════════════

def _p_take_damage(self, damage):
    t = _TRAINER
    if t and (t.god_mode or t.no_damage):
        self.invincible_timer = max(self.invincible_timer, 0.25)
        self.flash_timer = 0.0
        self.trigger_counter_attack()
        return self.stats.get("thorns", 0)
    return _ORIG["Player.take_damage"](self, damage)


def _p_get_move_speed(self):
    v = _ORIG["Player.get_move_speed"](self)
    t = _TRAINER
    if t:
        v *= t.move_speed_multiplier
    return v


def _p_get_fist_attack_speed(self):
    v = _ORIG["Player.get_fist_attack_speed"](self)
    t = _TRAINER
    if t:
        v *= t.attack_speed_multiplier
    return v


def _p_get_crit_chance(self):
    t = _TRAINER
    if t and t.always_crit:
        return 999999
    return _ORIG["Player.get_crit_chance"](self)


def _p_get_xp_multiplier(self):
    v = _ORIG["Player.get_xp_multiplier"](self)
    t = _TRAINER
    if t:
        v *= t.xp_multiplier
    return v


def _p_get_slide_cooldown(self):
    t = _TRAINER
    if t and t.no_slide_cooldown:
        return 0.01
    return _ORIG["Player.get_slide_cooldown"](self)


def _p_get_slide_max_charges(self):
    v = _ORIG["Player.get_slide_max_charges"](self)
    t = _TRAINER
    if t and t.infinite_slide:
        return max(v, 99)
    return v


def _p_update_fist_attack(self, dt):
    _ORIG["Player.update_fist_attack"](self, dt)
    t = _TRAINER
    if t and t.always_mega and self.fist_attack_active:
        self.fist_is_mega = True
        self.fist_which_hand = 2


def _g_deal_damage(self, enemy, base_damage, from_angle=None,
                   knockback_force=0, knockback_dir_x=0, knockback_dir_y=0,
                   can_crit=True, can_stun=True, can_lifesteal=True,
                   particle_color=None, particle_count=5, source="fist"):
    t = _TRAINER
    if t:
        base_damage *= t.damage_multiplier
        if t.one_hit_kill and getattr(enemy, "alive", True):
            base_damage = max(base_damage, getattr(enemy, "max_hp", 1) * 100 + 1)
    return _ORIG["Game.deal_damage_to_enemy"](
        self, enemy, base_damage, from_angle,
        knockback_force, knockback_dir_x, knockback_dir_y,
        can_crit, can_stun, can_lifesteal,
        particle_color, particle_count, source
    )


def _e_take_damage(self, damage, *a, **kw):
    t = _TRAINER
    if t and t.one_hit_kill and damage > 0 and getattr(self, "alive", True):
        damage = max(damage, getattr(self, "max_hp", 1) + 10**6)
    return _ORIG["Enemy.take_damage"](self, damage, *a, **kw)


def _b_take_damage(self, damage, *a, **kw):
    t = _TRAINER
    if t and t.one_hit_kill and damage > 0 and getattr(self, "alive", True):
        damage = max(damage, getattr(self, "max_hp", 1) + 10**6)
    return _ORIG["Boss.take_damage"](self, damage, *a, **kw)


def _s_update(self, dt, px, py, enemies, msgs):
    t = _TRAINER
    if t and t.no_enemy_spawn:
        return
    return _ORIG["EnemySpawner.update"](self, dt, px, py, enemies, msgs)


def _g_enforce_boss_arena(self):
    t = _TRAINER
    if t and t.no_boss_arena:
        return
    return _ORIG["Game.enforce_boss_arena"](self)


def _g_update_enemies(self, dt):
    t = _TRAINER
    if t and t.freeze_enemies:
        for e in self.enemies:
            if getattr(e, "alive", False):
                e.velocity_x = 0
                e.velocity_y = 0
        self.enemies = [e for e in self.enemies if getattr(e, "alive", False)]
        return
    return _ORIG["Game.update_enemies"](self, dt)


# ═════════════════════════════════════════════════════════════════
#  PATCHED GAME.RUN  —  main loop override
# ═════════════════════════════════════════════════════════════════
def _patched_run(self):
    global _TRAINER

    trainer = Trainer(self)
    self.trainer = trainer
    _TRAINER = trainer

    while self.running:
        dt = self.clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
                break
        if not self.running:
            break

        trainer.handle_events(events)
        trainer.update(dt)

        menu_open = trainer.visible or trainer.console.visible
        sdt = dt * trainer.time_scale

        if self.state == "menu":
            if not menu_open:
                self.update_menu(events)
            self.draw_menu()
        elif self.state == "controls":
            if not menu_open:
                self.update_controls(events)
            self.draw_controls()
        elif self.state == "highscores":
            if not menu_open:
                self.update_highscores(events)
            self.draw_highscores()
        elif self.state == "playing":
            trainer.update(sdt)
            if not menu_open:
                self.update_playing(sdt, events)
            self.draw_playing()
            trainer.draw_world(self.screen)
            trainer.post_update(sdt)
        elif self.state == "paused":
            if not menu_open:
                self.update_paused(events)
            self.draw_paused()
            trainer.draw_world(self.screen)
        elif self.state == "upgrading":
            if not menu_open:
                self.update_upgrading(events)
            self.draw_upgrading()
            trainer.draw_world(self.screen)
        elif self.state == "game_over":
            if not menu_open:
                self.update_game_over(events)
            self.draw_game_over()
            trainer.draw_world(self.screen)

        trainer.draw_overlay(self.screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


# ═════════════════════════════════════════════════════════════════
#  APPLY ALL PATCHES
# ═════════════════════════════════════════════════════════════════
def _patch():
    global _PATCHED
    if _PATCHED:
        return

    # save originals
    _ORIG["Game.run"]                     = _game_main.Game.run
    _ORIG["Game.deal_damage_to_enemy"]    = _game_main.Game.deal_damage_to_enemy
    _ORIG["Game.enforce_boss_arena"]      = _game_main.Game.enforce_boss_arena
    _ORIG["Game.update_enemies"]          = _game_main.Game.update_enemies
    _ORIG["Player.take_damage"]           = _player_mod.Player.take_damage
    _ORIG["Player.get_move_speed"]        = _player_mod.Player.get_move_speed
    _ORIG["Player.get_fist_attack_speed"] = _player_mod.Player.get_fist_attack_speed
    _ORIG["Player.get_crit_chance"]       = _player_mod.Player.get_crit_chance
    _ORIG["Player.get_xp_multiplier"]     = _player_mod.Player.get_xp_multiplier
    _ORIG["Player.get_slide_cooldown"]    = _player_mod.Player.get_slide_cooldown
    _ORIG["Player.get_slide_max_charges"] = _player_mod.Player.get_slide_max_charges
    _ORIG["Player.update_fist_attack"]    = _player_mod.Player.update_fist_attack
    _ORIG["EnemySpawner.update"]          = _enemies_mod.EnemySpawner.update
    _ORIG["Enemy.take_damage"]            = _enemies_mod.Enemy.take_damage
    _ORIG["Boss.take_damage"]             = _enemies_mod.Boss.take_damage

    # apply patches
    _game_main.Game.run                     = _patched_run
    _game_main.Game.deal_damage_to_enemy    = _g_deal_damage
    _game_main.Game.enforce_boss_arena      = _g_enforce_boss_arena
    _game_main.Game.update_enemies          = _g_update_enemies
    _player_mod.Player.take_damage          = _p_take_damage
    _player_mod.Player.get_move_speed       = _p_get_move_speed
    _player_mod.Player.get_fist_attack_speed = _p_get_fist_attack_speed
    _player_mod.Player.get_crit_chance      = _p_get_crit_chance
    _player_mod.Player.get_xp_multiplier    = _p_get_xp_multiplier
    _player_mod.Player.get_slide_cooldown   = _p_get_slide_cooldown
    _player_mod.Player.get_slide_max_charges = _p_get_slide_max_charges
    _player_mod.Player.update_fist_attack   = _p_update_fist_attack
    _enemies_mod.EnemySpawner.update        = _s_update
    _enemies_mod.Enemy.take_damage          = _e_take_damage
    _enemies_mod.Boss.take_damage           = _b_take_damage

    _PATCHED = True


# ═════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    _patch()
    game = _game_main.Game()
    game.run()
