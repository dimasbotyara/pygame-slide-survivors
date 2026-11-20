# settings_manager.py — Save/load settings in script directory

import json
import os
from translations import set_language

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

from preferences import DEFAULTS, valid_value

DEFAULT_SETTINGS = DEFAULTS


class SettingsManager:
    def __init__(self):
        self.settings = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.settings.update({k: tuple(v) if k == "resolution" else v
                                              for k, v in data.items() if valid_value(k, v)})
            except Exception as e:
                print(f"Error loading settings: {e}")
        else:
            self.settings["first_launch"] = True

        set_language(self.settings.get("language", "ru"))

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        if key == "language":
            set_language(value)
        self.save()
