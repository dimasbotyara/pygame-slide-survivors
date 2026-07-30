# upgrades.py — Upgrades system with translation support

import random
from settings import *
from translations import t


class Upgrade:
    def __init__(self, upgrade_id, icon_color, stat_key, value,
                 max_level=None, category="basic"):
        self.upgrade_id = upgrade_id
        self.icon_color = icon_color
        self.stat_key = stat_key
        self.value = value
        self.max_level = max_level
        self.current_level = 0
        self.category = category

    @property
    def name(self):
        return t(f"upgrade_{self.upgrade_id}_name")

    @property
    def description(self):
        return t(f"upgrade_{self.upgrade_id}_desc")

    def can_upgrade(self):
        if self.max_level is None:
            return True
        return self.current_level < self.max_level

    def apply(self, player):
        self.current_level += 1
        player.stats[self.stat_key] += self.value


def create_all_upgrades():
    upgrades = []

    # ──── БАЗОВЫЕ ────
    upgrades.append(Upgrade("max_hp", RED, "max_hp", 20, category="basic"))
    upgrades.append(Upgrade("hp_regen", PINK, "hp_regen", 0.5, category="basic"))
    upgrades.append(Upgrade("move_speed", CYAN, "move_speed", 8, category="basic"))
    upgrades.append(Upgrade("armor", GRAY, "armor", 2, category="basic"))
    upgrades.append(Upgrade("xp_radius", YELLOW, "xp_radius", 15, category="basic"))
    upgrades.append(Upgrade("luck", GREEN, "luck", 5, category="basic"))
    upgrades.append(Upgrade("damage", ORANGE, "damage", 12, category="basic"))
    upgrades.append(Upgrade("attack_speed", YELLOW, "attack_speed", 15, category="basic"))
    upgrades.append(Upgrade("attack_range", WHITE, "attack_range", 12, category="basic"))
    upgrades.append(Upgrade("crit_chance", RED, "crit_chance", 5, max_level=20, category="basic"))
    upgrades.append(Upgrade("crit_multiplier", DARK_RED, "crit_multiplier", 25, category="basic"))
    upgrades.append(Upgrade("target_count", PURPLE, "target_count", 1, max_level=5, category="basic"))

    # ──── 🥊 КУЛАКИ ────
    upgrades.append(Upgrade("fist_combo_hits", ORANGE, "fist_combo_hits", 1, max_level=3, category="fist"))
    upgrades.append(Upgrade("fist_lifesteal", CRIMSON, "fist_lifesteal", 5, max_level=10, category="fist"))
    upgrades.append(Upgrade("fist_stun", YELLOW, "fist_stun_chance", 10, max_level=8, category="fist"))
    upgrades.append(Upgrade("fist_rage", RED, "fist_rage", 20, max_level=5, category="fist"))
    upgrades.append(Upgrade("fist_ground_slam", BROWN, "fist_ground_slam", 1, max_level=5, category="fist"))
    upgrades.append(Upgrade("fist_counter", SILVER, "fist_counter_attack", 25, max_level=4, category="fist"))
    upgrades.append(Upgrade("fist_arc", ORANGE, "fist_arc_bonus", 20, category="fist"))
    upgrades.append(Upgrade("fist_wave", YELLOW, "fist_wave", 1, max_level=5, category="fist"))
    upgrades.append(Upgrade("fist_xp_pull", GOLD, "fist_xp_pull", 1, max_level=3, category="fist"))

    # ──── 🏂 СКОЛЬЖЕНИЕ ────
    upgrades.append(Upgrade("slide_speed", CYAN, "slide_speed", 15, category="slide"))
    upgrades.append(Upgrade("slide_duration", BLUE, "slide_duration", 10, category="slide"))
    upgrades.append(Upgrade("slide_cooldown", DARK_BLUE, "slide_cooldown", 8, max_level=10, category="slide"))
    upgrades.append(Upgrade("slide_damage", ORANGE, "slide_damage", 15, category="slide"))
    upgrades.append(Upgrade("slide_knockback_radius", WHITE, "slide_knockback_radius", 5, category="slide"))
    upgrades.append(Upgrade("slide_charges", PURPLE, "slide_charges", 1, max_level=4, category="slide"))
    upgrades.append(Upgrade("slide_kill_reset", GREEN, "slide_kill_reset_chance", 5, max_level=10, category="slide"))
    upgrades.append(Upgrade("slide_turn_speed", CYAN, "slide_turn_speed", 20, category="slide"))
    upgrades.append(Upgrade("slide_invincibility", BLUE, "slide_invincibility_after", 0.3, max_level=5, category="slide"))
    upgrades.append(Upgrade("slide_electric", CYAN, "slide_electric_trail", 1, max_level=5, category="slide"))
    upgrades.append(Upgrade("slide_shockwave", PURPLE, "slide_shockwave", 1, max_level=3, category="slide"))

    # ──── 🌟 УТИЛИТИ ────
    upgrades.append(Upgrade("xp_multiplier", YELLOW, "xp_multiplier", 10, category="utility"))
    upgrades.append(Upgrade("drop_chance", GREEN, "drop_chance", 10, category="utility"))
    upgrades.append(Upgrade("heal_effectiveness", PINK, "heal_effectiveness", 15, category="utility"))
    upgrades.append(Upgrade("aura_damage", RED, "aura_damage", 3.0, category="utility"))
    upgrades.append(Upgrade("aura_slow", BLUE, "aura_slow", 5, max_level=10, category="utility"))
    upgrades.append(Upgrade("block_chance", GRAY, "block_chance", 3, max_level=15, category="utility"))
    upgrades.append(Upgrade("thorns", BROWN, "thorns", 5, category="utility"))

    return upgrades


class UpgradeManager:
    def __init__(self):
        self.all_upgrades = create_all_upgrades()
        self.upgrade_map = {u.upgrade_id: u for u in self.all_upgrades}
        self.choices = []
        self.choosing = False
        self.selected_index = 0

    def generate_choices(self, num_choices=CHOICES_PER_LEVEL, luck_bonus=0):
        available = [u for u in self.all_upgrades if u.can_upgrade()]
        if not available:
            available = [u for u in self.all_upgrades if u.max_level is None]

        weights = [self._get_weight(u, luck_bonus) for u in available]
        num = min(num_choices, len(available))
        self.choices = []
        total_weight = sum(weights)
        pool = list(zip(available, weights))

        for _ in range(num):
            if not pool:
                break
            roll = random.random() * total_weight
            cumulative = 0
            idx = 0
            for i, (u, w) in enumerate(pool):
                cumulative += w
                if roll <= cumulative:
                    idx = i
                    break
            chosen, cw = pool.pop(idx)
            total_weight -= cw
            self.choices.append(chosen)

        self.choosing = True
        self.selected_index = 0

    def _get_weight(self, upgrade, luck_bonus):
        weights = {"basic": 100, "fist": 65 + luck_bonus, "slide": 65 + luck_bonus, "utility": 55 + luck_bonus}
        w = weights.get(upgrade.category, 70)
        rare = ["fist_combo_hits", "fist_ground_slam", "fist_counter", "fist_wave", "fist_xp_pull",
                "slide_charges", "slide_electric", "slide_shockwave", "slide_kill_reset"]
        if upgrade.upgrade_id in rare:
            w = 40 + luck_bonus * 2
        return max(1, w)

    def select_upgrade(self, index, player):
        if 0 <= index < len(self.choices):
            upgrade = self.choices[index]
            upgrade.apply(player)
            self.choosing = False
            self.choices = []
            return upgrade
        return None