# achievements.py — persistent achievement catalogue and unlock storage

import json
import os
from translations import t

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ACHIEVEMENTS_FILE = os.path.join(SCRIPT_DIR, "achievements.json")

# IDs are intentionally stable: saved unlocks survive catalogue additions.
ACHIEVEMENTS_LIST = [
    "first_kill", "kills_10", "kills_50", "kills_100", "kills_500", "kills_1000",
    "slide_10", "slide_master", "slide_250", "slide_1000",
    "combo_25", "combo_50", "combo_100",
    "level_5", "level_10", "level_20",
    "survive_1min", "survive_5min", "survive_10min",
    "ult_used", "ult_10", "ult_25",
    "boss_slayer", "boss_5", "boss_10",
    "slider_path", "brawler_path", "spark_path", "shadow_path",
]


class AchievementManager:
    def __init__(self):
        self.unlocked = {}
        self.load()

    def load(self):
        if os.path.exists(ACHIEVEMENTS_FILE):
            try:
                with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.unlocked = data if isinstance(data, dict) else {}
            except Exception as e:
                print(f"Error loading achievements: {e}")
                self.unlocked = {}
        else:
            self.unlocked = {}

    def save(self):
        try:
            with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.unlocked, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving achievements: {e}")

    def is_unlocked(self, ach_id):
        return self.unlocked.get(ach_id, False)

    def unlock(self, ach_id, particle_manager=None):
        if ach_id not in ACHIEVEMENTS_LIST or self.is_unlocked(ach_id):
            return False
        self.unlocked[ach_id] = True
        self.save()
        title = t(f"ach_{ach_id}_title")
        if particle_manager:
            particle_manager.add_message(f"🏆 {t('ACH_UNLOCKED')}: {title}", (255, 215, 0))
        return True
