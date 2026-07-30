# achievements.py — Achievements system saving to script directory

import json
import os
from translations import t

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ACHIEVEMENTS_FILE = os.path.join(SCRIPT_DIR, "achievements.json")

ACHIEVEMENTS_LIST = [
    "first_kill",
    "slide_master",
    "combo_50",
    "boss_slayer",
    "level_20",
    "ult_used",
    "kills_500",
    "survive_5min",
]


class AchievementManager:
    def __init__(self):
        self.unlocked = {}
        self.load()

    def load(self):
        if os.path.exists(ACHIEVEMENTS_FILE):
            try:
                with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                    self.unlocked = json.load(f)
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
        if not self.is_unlocked(ach_id):
            self.unlocked[ach_id] = True
            self.save()
            title = t(f"ach_{ach_id}_title")
            if particle_manager:
                particle_manager.add_message(f"🏆 {t('ACH_UNLOCKED')}: {title}", (255, 215, 0))
            return True
        return False
