# highscores.py — Кроссплатформенная система рекордов (Windows/Linux)

import json
import os
from settings import SAVE_DIR, HIGHSCORES_FILE, MAX_HIGHSCORES


def ensure_save_dir():
    """Создать директорию для сохранений если не существует"""
    if not os.path.exists(SAVE_DIR):
        try:
            os.makedirs(SAVE_DIR)
        except OSError as e:
            print(f"Не удалось создать директорию сохранений: {e}")


def load_highscores():
    """Загрузить рекорды из файла"""
    ensure_save_dir()

    if not os.path.exists(HIGHSCORES_FILE):
        return []

    try:
        with open(HIGHSCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data[:MAX_HIGHSCORES]
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Ошибка загрузки рекордов: {e}")

    return []


def save_highscores(scores):
    """Сохранить рекорды в файл"""
    ensure_save_dir()

    try:
        with open(HIGHSCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores[:MAX_HIGHSCORES], f, indent=2, ensure_ascii=False)
    except (IOError, OSError) as e:
        print(f"Ошибка сохранения рекордов: {e}")


def add_highscore(time_survived, level, enemies_killed):
    """Добавить новый рекорд и вернуть позицию (0-based) или -1"""
    scores = load_highscores()

    new_entry = {
        "time": time_survived,
        "level": level,
        "kills": enemies_killed,
        "score": calculate_score(time_survived, level, enemies_killed)
    }

    scores.append(new_entry)
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:MAX_HIGHSCORES]

    save_highscores(scores)

    # Найти позицию нового рекорда
    for i, s in enumerate(scores):
        if s is new_entry:
            return i

    return -1


def calculate_score(time_survived, level, enemies_killed):
    """Подсчитать очки"""
    time_score = int(time_survived) * 10
    level_score = level * 100
    kill_score = enemies_killed * 5
    return time_score + level_score + kill_score


def format_time(seconds):
    """Форматировать время"""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"