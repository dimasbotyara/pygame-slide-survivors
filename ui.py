# ui.py — User Interface with localization, hero selection, boss bar & achievements

import pygame
import math
from settings import *
from highscores import load_highscores, format_time, calculate_score
from translations import t
from heroes import HEROES, HERO_KEYS
from achievements import ACHIEVEMENTS_LIST


class UI:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", UI_FONT_SIZE)
        self.font_large = pygame.font.SysFont("Arial", UI_FONT_SIZE_LARGE, bold=True)
        self.font_small = pygame.font.SysFont("Arial", UI_FONT_SIZE_SMALL)
        self.font_title = pygame.font.SysFont("Arial", 72, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 32)
        self.font_combo = pygame.font.SysFont("Arial", 36, bold=True)

    # ================================================================
    # HUD
    # ================================================================
    def draw_hud(self, screen, player, game_time, enemy_count, active_boss=None):
        self.draw_hp_bar(screen, player)
        self.draw_xp_bar(screen, player)
        self.draw_level(screen, player)
        self.draw_timer(screen, game_time)
        self.draw_slide_indicator(screen, player)
        self.draw_ult_bar(screen, player)
        self.draw_stats_mini(screen, player, enemy_count)
        self.draw_combo(screen, player)
        self.draw_dash_hint(screen, player)
        if active_boss:
            self.draw_boss_bar(screen, active_boss)

    def draw_hp_bar(self, screen, player):
        x = UI_MARGIN
        y = UI_MARGIN

        bg_rect = pygame.Rect(x, y, UI_HP_BAR_WIDTH, UI_HP_BAR_HEIGHT)
        pygame.draw.rect(screen, DARK_RED, bg_rect)

        hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0
        fill_width = int(UI_HP_BAR_WIDTH * max(0.0, min(1.0, hp_ratio)))
        fill_rect = pygame.Rect(x, y, fill_width, UI_HP_BAR_HEIGHT)

        if hp_ratio > 0.6:
            fill_color = GREEN
        elif hp_ratio > 0.3:
            fill_color = YELLOW
        else:
            fill_color = RED

        pygame.draw.rect(screen, fill_color, fill_rect)

        highlight = pygame.Surface((fill_width, UI_HP_BAR_HEIGHT // 2), pygame.SRCALPHA)
        highlight.fill((255, 255, 255, 30))
        screen.blit(highlight, (x, y))

        pygame.draw.rect(screen, WHITE, bg_rect, 2)

        hp_text = f"{int(player.hp)}/{int(player.max_hp)}"
        text_surface = self.font_small.render(hp_text, True, WHITE)
        text_rect = text_surface.get_rect(center=bg_rect.center)
        screen.blit(text_surface, text_rect)

    def draw_xp_bar(self, screen, player):
        y = SCREEN_HEIGHT - UI_XP_BAR_HEIGHT
        xp_ratio = player.xp / player.xp_to_next if player.xp_to_next > 0 else 0

        bg_rect = pygame.Rect(0, y, SCREEN_WIDTH, UI_XP_BAR_HEIGHT)
        pygame.draw.rect(screen, DARK_BLUE, bg_rect)

        fill_width = int(SCREEN_WIDTH * max(0.0, min(1.0, xp_ratio)))
        fill_rect = pygame.Rect(0, y, fill_width, UI_XP_BAR_HEIGHT)
        pygame.draw.rect(screen, CYAN, fill_rect)

    def draw_level(self, screen, player):
        x = UI_MARGIN
        y = UI_MARGIN + UI_HP_BAR_HEIGHT + 5
        level_text = t("LEVEL_PREFIX", player.level)
        text_surface = self.font.render(level_text, True, YELLOW)
        screen.blit(text_surface, (x, y))

    def draw_timer(self, screen, game_time):
        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"
        text_surface = self.font_large.render(timer_text, True, WHITE)
        text_rect = text_surface.get_rect(midtop=(SCREEN_WIDTH // 2, UI_MARGIN))
        screen.blit(text_surface, text_rect)

    def draw_slide_indicator(self, screen, player):
        x = UI_MARGIN
        y = UI_MARGIN + UI_HP_BAR_HEIGHT + 35

        max_charges = player.slide_max_charges
        for i in range(max_charges):
            charge_x = x + i * 25
            charge_rect = pygame.Rect(charge_x, y, 20, 20)

            if i < player.slide_charges:
                pygame.draw.rect(screen, CYAN, charge_rect)
                pygame.draw.rect(screen, WHITE, charge_rect, 2)
                pts = [(charge_x + 7, y + 2), (charge_x + 10, y + 9),
                       (charge_x + 8, y + 9), (charge_x + 13, y + 18),
                       (charge_x + 10, y + 11), (charge_x + 12, y + 11)]
                pygame.draw.polygon(screen, WHITE, pts)
            else:
                pygame.draw.rect(screen, DARK_GRAY, charge_rect)
                if i == player.slide_charges:
                    cooldown_total = player.get_slide_cooldown()
                    if cooldown_total > 0:
                        progress = 1.0 - (player.slide_cooldown_timer / cooldown_total)
                        fill_h = int(20 * max(0.0, min(1.0, progress)))
                        fill_rect = pygame.Rect(charge_x, y + 20 - fill_h, 20, fill_h)
                        pygame.draw.rect(screen, DARK_BLUE, fill_rect)
                pygame.draw.rect(screen, GRAY, charge_rect, 2)

        if player.is_sliding:
            slide_text = t("SLIDING")
            text_surface = self.font_small.render(slide_text, True, CYAN)
            screen.blit(text_surface, (x, y + 25))

    def draw_ult_bar(self, screen, player):
        bar_w = 160
        bar_h = 16
        bar_x = UI_MARGIN
        bar_y = UI_MARGIN + UI_HP_BAR_HEIGHT + 65

        ratio = player.ult_charge / 100.0
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(screen, DARK_GRAY, bg_rect)

        fill_w = int(bar_w * ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        fill_color = GOLD if player.can_use_ult() else YELLOW
        pygame.draw.rect(screen, fill_color, fill_rect)
        pygame.draw.rect(screen, WHITE if player.can_use_ult() else GRAY, bg_rect, 2)

        from heroes import HEROES
        hero_id = getattr(player, 'hero_id', 'slider')
        hero_info = HEROES.get(hero_id, HEROES["slider"])
        ult_id = hero_info["ult_id"]
        ult_name = t(f"{ult_id}_name")

        if player.can_use_ult():
            t_str = t("ULT_READY", ult_name)
            text_s = self.font_small.render(t_str, True, GOLD)
            screen.blit(text_s, (bar_x, bar_y + 20))
        else:
            pct_str = f"{ult_name}: {int(player.ult_charge)}%"
            text_s = self.font_small.render(pct_str, True, LIGHT_GRAY)
            text_r = text_s.get_rect(center=bg_rect.center)
            screen.blit(text_s, text_r)

    def draw_boss_bar(self, screen, boss):
        if not boss or not boss.alive:
            return

        bar_w = 500
        bar_h = 22
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 35

        is_enraged = getattr(boss, 'is_enraged', False)
        title_text = t("BOSS_HP_TITLE")
        title_s = self.font.render(title_text, True, RED if is_enraged else GOLD)
        title_r = title_s.get_rect(center=(SCREEN_WIDTH // 2, 18))
        screen.blit(title_s, title_r)

        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(screen, (30, 0, 0), bg_rect)

        hp_ratio = max(0.0, min(1.0, boss.hp / boss.max_hp))
        fill_w = int(bar_w * hp_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        fill_color = CRIMSON if is_enraged else PURPLE
        pygame.draw.rect(screen, fill_color, fill_rect)
        pygame.draw.rect(screen, RED if is_enraged else GOLD, bg_rect, 2)

        hp_text = f"{int(boss.hp)} / {int(boss.max_hp)}"
        hp_s = self.font_small.render(hp_text, True, WHITE)
        hp_r = hp_s.get_rect(center=bg_rect.center)
        screen.blit(hp_s, hp_r)

    def draw_combo(self, screen, player):
        if player.combo_count <= 0:
            return

        combo_x = SCREEN_WIDTH // 2
        combo_y = 80

        scale = min(2.0, 1.0 + player.combo_count * 0.02)

        combo_text = t("COMBO", player.combo_count)
        text_surface = self.font_combo.render(combo_text, True, ORANGE)

        w = int(text_surface.get_width() * scale)
        h = int(text_surface.get_height() * scale)
        text_surface = pygame.transform.scale(text_surface, (w, h))

        text_rect = text_surface.get_rect(center=(combo_x, combo_y))

        shadow = self.font_combo.render(combo_text, True, BLACK)
        shadow = pygame.transform.scale(shadow, (w, h))
        screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        screen.blit(text_surface, text_rect)

        bonus = player.get_combo_xp_bonus()
        if bonus > 0:
            bonus_text = t("COMBO_XP_BONUS", bonus)
            bonus_surface = self.font_small.render(bonus_text, True, YELLOW)
            bonus_rect = bonus_surface.get_rect(center=(combo_x, combo_y + h // 2 + 12))
            screen.blit(bonus_surface, bonus_rect)

        bar_w = 100
        bar_h = 4
        bar_x = combo_x - bar_w // 2
        bar_y = combo_y + h // 2 + 25
        ratio = max(0.0, min(1.0, player.combo_timer / player.combo_window))
        pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, ORANGE, (bar_x, bar_y, int(bar_w * ratio), bar_h))

    def draw_dash_hint(self, screen, player):
        if player.dash_attack_window_timer > 0 and not player.dash_attack_triggered:
            text = t("DASH_HINT")
            pulse = abs(math.sin(player.body_anim_timer * 10))
            color = (
                int(255 * pulse + 200 * (1 - pulse)),
                int(150 * pulse + 100 * (1 - pulse)),
                0
            )
            surface = self.font.render(text, True, color)
            rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            screen.blit(surface, rect)

    def draw_stats_mini(self, screen, player, enemy_count):
        x = SCREEN_WIDTH - 160
        y = UI_MARGIN

        lines = [
            t("STAT_KILLS", player.enemies_killed),
            t("STAT_ENEMIES", enemy_count),
            t("STAT_SPEED", int(player.current_speed)),
            t("STAT_MAX_COMBO", player.combo_max_reached),
        ]

        for i, line in enumerate(lines):
            text_surface = self.font_small.render(line, True, LIGHT_GRAY)
            screen.blit(text_surface, (x, y + i * 20))

    # ================================================================
    # МИНИ-КАРТА
    # ================================================================
    def draw_minimap(self, screen, player, enemies, xp_orbs, dropped_items, bosses_alive):
        mm_size = MINIMAP_SIZE
        mm_x = SCREEN_WIDTH - mm_size - MINIMAP_MARGIN
        mm_y = SCREEN_HEIGHT - mm_size - MINIMAP_MARGIN - UI_XP_BAR_HEIGHT - 5
        center = mm_size // 2
        radius = center - 3

        mm_surface = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)

        # Тёмный прозрачный круговой фон
        pygame.draw.circle(mm_surface, (12, 16, 32, 210), (center, center), radius)

        # Радарная сетка (концентрические круги)
        pygame.draw.circle(mm_surface, (0, 220, 255, 45), (center, center), int(radius * 0.66), 1)
        pygame.draw.circle(mm_surface, (0, 220, 255, 25), (center, center), int(radius * 0.33), 1)

        # Перекрестие (север-юг-запад-восток)
        pygame.draw.line(mm_surface, (0, 220, 255, 40), (center, 6), (center, mm_size - 6), 1)
        pygame.draw.line(mm_surface, (0, 220, 255, 40), (6, center), (mm_size - 6, center), 1)

        # Вращающийся луч радара
        t_time = pygame.time.get_ticks() / 1000.0
        sweep_angle = (t_time * 2.2) % (math.pi * 2)
        end_x = center + int(math.cos(sweep_angle) * radius)
        end_y = center + int(math.sin(sweep_angle) * radius)
        pygame.draw.line(mm_surface, (0, 255, 220, 70), (center, center), (end_x, end_y), 2)

        # Опыт (XP gems)
        for orb in xp_orbs:
            dx = (orb.x - player.x) * MINIMAP_SCALE
            dy = (orb.y - player.y) * MINIMAP_SCALE
            if dx * dx + dy * dy <= radius * radius:
                mx = int(center + dx)
                my = int(center + dy)
                pygame.draw.circle(mm_surface, (255, 240, 80, 220), (mx, my), 1)

        # Выпавшие предметы (Health, Bomb, Magnet...)
        for item in dropped_items:
            dx = (item.x - player.x) * MINIMAP_SCALE
            dy = (item.y - player.y) * MINIMAP_SCALE
            if dx * dx + dy * dy <= radius * radius:
                mx = int(center + dx)
                my = int(center + dy)
                pygame.draw.circle(mm_surface, GREEN, (mx, my), 2)

        # Враги и Боссы + Указатель на Закадрового Босса
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = (enemy.x - player.x) * MINIMAP_SCALE
            dy = (enemy.y - player.y) * MINIMAP_SCALE
            dist_sq = dx * dx + dy * dy

            if dist_sq <= radius * radius:
                mx = int(center + dx)
                my = int(center + dy)
                if enemy.is_boss:
                    boss_pulse = 4 + int(abs(math.sin(t_time * 6)) * 3)
                    pygame.draw.circle(mm_surface, (255, 40, 80), (mx, my), boss_pulse)
                    pygame.draw.circle(mm_surface, GOLD, (mx, my), boss_pulse, 1)
                else:
                    pygame.draw.rect(mm_surface, RED, (mx - 1, my - 1, 2, 2))
            elif enemy.is_boss:
                # Стрелка-указатель на босса на краю радара
                angle = math.atan2(dy, dx)
                edge_x = center + int(math.cos(angle) * (radius - 8))
                edge_y = center + int(math.sin(angle) * (radius - 8))
                pulse_color = (255, 0, 100) if (int(t_time * 8) % 2 == 0) else GOLD
                pygame.draw.circle(mm_surface, pulse_color, (edge_x, edge_y), 5)
                pygame.draw.circle(mm_surface, WHITE, (edge_x, edge_y), 5, 1)

        # Игрок (Стрелка направления движения)
        vx, vy = getattr(player, 'vx', 0), getattr(player, 'vy', 0)
        p_angle = math.atan2(vy, vx) if (vx != 0 or vy != 0) else -math.pi / 2
        p_front_x = center + int(math.cos(p_angle) * 7)
        p_front_y = center + int(math.sin(p_angle) * 7)
        p_left_x = center + int(math.cos(p_angle + 2.4) * 5)
        p_left_y = center + int(math.sin(p_angle + 2.4) * 5)
        p_right_x = center + int(math.cos(p_angle - 2.4) * 5)
        p_right_y = center + int(math.sin(p_angle - 2.4) * 5)
        pygame.draw.polygon(mm_surface, CYAN, [(p_front_x, p_front_y), (p_left_x, p_left_y), (p_right_x, p_right_y)])
        pygame.draw.polygon(mm_surface, WHITE, [(p_front_x, p_front_y), (p_left_x, p_left_y), (p_right_x, p_right_y)], 1)

        # Внешнее неоновое кольцо радара
        pygame.draw.circle(mm_surface, (0, 220, 255), (center, center), radius, 2)

        screen.blit(mm_surface, (mm_x, mm_y))

    # ================================================================
    # ВЫБОР УЛУЧШЕНИЙ
    # ================================================================
    def draw_upgrade_screen(self, screen, choices, selected_index, player):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))

        title_text = t("UPGRADE_TITLE", player.level)
        title_surface = self.font_large.render(title_text, True, YELLOW)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)

        num_choices = len(choices)
        total_width = num_choices * UI_UPGRADE_BOX_WIDTH + (num_choices - 1) * 20
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, upgrade in enumerate(choices):
            box_x = start_x + i * (UI_UPGRADE_BOX_WIDTH + 20)
            box_y = 200
            rect = pygame.Rect(box_x, box_y, UI_UPGRADE_BOX_WIDTH, UI_UPGRADE_BOX_HEIGHT)

            is_selected = (i == selected_index)

            bg_color = (40, 40, 60) if is_selected else (25, 25, 40)
            pygame.draw.rect(screen, bg_color, rect)

            border_color = YELLOW if is_selected else GRAY
            border_w = 4 if is_selected else 2
            pygame.draw.rect(screen, border_color, rect, border_w)

            # Категория / Значок
            icon_box = pygame.Rect(box_x + 15, box_y + 15, 40, 40)
            pygame.draw.rect(screen, upgrade.icon_color, icon_box)
            pygame.draw.rect(screen, WHITE, icon_box, 2)

            cat_str = f"[{upgrade.category.upper()}]"
            cat_s = self.font_small.render(cat_str, True, GOLD if upgrade.category == "hero" else LIGHT_GRAY)
            screen.blit(cat_s, (box_x + 65, box_y + 18))

            name_surface = self.font.render(upgrade.name, True, WHITE)
            screen.blit(name_surface, (box_x + 65, box_y + 35))

            desc_surface = self.font_small.render(upgrade.description, True, LIGHT_GRAY)
            screen.blit(desc_surface, (box_x + 15, box_y + 70))

            level_str = t("UPGRADE_MAX") if upgrade.max_level and upgrade.current_level >= upgrade.max_level else t("UPGRADE_LEVEL", upgrade.current_level + 1)
            level_surface = self.font_small.render(level_str, True, GOLD if is_selected else GRAY)
            screen.blit(level_surface, (box_x + 15, box_y + 110))

        hint_text = t("UPGRADE_HINT")
        hint_surface = self.font_small.render(hint_text, True, GRAY)
        hint_rect = hint_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(hint_surface, hint_rect)

    def _draw_upgrade_box(self, screen, upgrade, x, y, selected, number):
        rect = pygame.Rect(x, y, UI_UPGRADE_BOX_WIDTH, UI_UPGRADE_BOX_HEIGHT)

        bg_color = (40, 40, 60) if not selected else (60, 60, 90)
        pygame.draw.rect(screen, bg_color, rect)

        if selected:
            glow_rect = rect.inflate(6, 6)
            pygame.draw.rect(screen, YELLOW, glow_rect, 2)

        border_color = YELLOW if selected else GRAY
        border_width = 3 if selected else 1
        pygame.draw.rect(screen, border_color, rect, border_width)

        num_text = self.font_small.render(f"[{number}]", True, LIGHT_GRAY)
        screen.blit(num_text, (x + 5, y + 5))

        icon_rect = pygame.Rect(x + 15, y + 25, 30, 30)
        pygame.draw.rect(screen, upgrade.icon_color, icon_rect)
        pygame.draw.rect(screen, WHITE, icon_rect, 1)

        name_surface = self.font.render(upgrade.name, True, WHITE)
        screen.blit(name_surface, (x + 55, y + 20))

        if upgrade.current_level > 0:
            level_str = t("UPGRADE_LVL", upgrade.current_level)
            if upgrade.max_level:
                level_str += f"/{upgrade.max_level}"
            level_surface = self.font_small.render(level_str, True, YELLOW)
            screen.blit(level_surface, (x + 55, y + 45))

        desc_surface = self.font_small.render(upgrade.description, True, LIGHT_GRAY)
        screen.blit(desc_surface, (x + 15, y + 75))

        if upgrade.category == "hero":
            cat_text = t("CAT_HERO")
            cat_color = GOLD
        elif "slide" in upgrade.upgrade_id:
            cat_text = t("CAT_SLIDE")
            cat_color = CYAN
        elif upgrade.category == "fist" or upgrade.upgrade_id in ["damage", "attack_speed", "attack_range", "crit_chance", "crit_multiplier", "target_count"]:
            cat_text = t("CAT_COMBAT")
            cat_color = RED
        elif upgrade.upgrade_id in ["aura_damage", "aura_slow", "thorns", "block_chance", "shield_wall", "orbital_blade"]:
            cat_text = t("CAT_SPECIAL")
            cat_color = PURPLE
        else:
            cat_text = t("CAT_BASIC")
            cat_color = GREEN

        cat_surface = self.font_small.render(cat_text, True, cat_color)
        screen.blit(cat_surface, (x + 15, y + 95))

    # ================================================================
    # ВЫБОР ПЕРСОНАЖА
    # ================================================================
    def draw_hero_select_screen(self, screen, selected_index):
        screen.fill((15, 15, 30))

        title = self.font_large.render(t("HERO_SELECT_TITLE"), True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title, title_rect)

        box_w = 260
        box_h = 360
        total_w = len(HERO_KEYS) * box_w + (len(HERO_KEYS) - 1) * 25
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, key in enumerate(HERO_KEYS):
            h_data = HEROES[key]
            is_selected = (i == selected_index)

            bx = start_x + i * (box_w + 25)
            by = SCREEN_HEIGHT // 2 - box_h // 2 + 10
            rect = pygame.Rect(bx, by, box_w, box_h)

            bg_c = (50, 50, 80) if is_selected else (30, 30, 50)
            pygame.draw.rect(screen, bg_c, rect)

            if is_selected:
                glow = rect.inflate(8, 8)
                pygame.draw.rect(screen, YELLOW, glow, 3)

            border_c = YELLOW if is_selected else GRAY
            pygame.draw.rect(screen, border_c, rect, 2)

            # Круг персонажа
            cx = bx + box_w // 2
            cy = by + 60
            pygame.draw.circle(screen, h_data["color"], (cx, cy), 35)
            pygame.draw.circle(screen, h_data["outline_color"], (cx, cy), 35, 3)

            # Название и подзаголовок
            name_s = self.font.render(t(f"hero_{key}_name"), True, WHITE)
            name_r = name_s.get_rect(center=(cx, by + 120))
            screen.blit(name_s, name_r)

            sub_s = self.font_small.render(t(f"hero_{key}_sub"), True, GOLD)
            sub_r = sub_s.get_rect(center=(cx, by + 145))
            screen.blit(sub_s, sub_r)

            # Описание и характеристики
            desc_text = t(f"hero_{key}_desc")
            parts = desc_text.split(" | ")
            y_offset = by + 180
            for part in parts:
                p_s = self.font_small.render(part, True, LIGHT_GRAY)
                p_r = p_s.get_rect(center=(cx, y_offset))
                screen.blit(p_s, p_r)
                y_offset += 25

        hint = self.font_small.render(t("HERO_SELECT_HINT"), True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(hint, hint_rect)

    # ================================================================
    # ВЫБОР ЯЗЫКА (ПЕРВЫЙ ЗАПУСК)
    # ================================================================
    def draw_language_select_screen(self, screen, selected_option):
        screen.fill((15, 15, 30))

        title = self.font_large.render(t("SELECT_LANG_TITLE"), True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        screen.blit(title, title_rect)

        options = [t("LANG_RU"), t("LANG_EN")]

        for i, opt in enumerate(options):
            y = 320 + i * 80
            is_selected = (i == selected_option)
            color = YELLOW if is_selected else WHITE
            font = self.font_large if is_selected else self.font_medium

            text = font.render(opt, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))

            if is_selected:
                highlight = pygame.Rect(text_rect.x - 30, text_rect.y - 8,
                                       text_rect.width + 60, text_rect.height + 16)
                pygame.draw.rect(screen, (30, 30, 60), highlight)
                pygame.draw.rect(screen, YELLOW, highlight, 2)

                arrow = self.font_large.render("►", True, YELLOW)
                screen.blit(arrow, (highlight.x - 35, text_rect.y))

            screen.blit(text, text_rect)

        hint = self.font_small.render(t("SELECT_LANG_HINT"), True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        screen.blit(hint, hint_rect)

    # ================================================================
    # НАСТРОЙКИ
    # ================================================================
    def draw_settings_screen(self, screen, selected_option, settings_manager):
        screen.fill((15, 15, 30))

        title = self.font_large.render(t("SETTINGS_TITLE"), True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title, title_rect)

        lang_val = t("LANG_RU") if settings_manager.get("language") == "ru" else t("LANG_EN")
        shake_val = t("SETTING_ON") if settings_manager.get("screen_shake", True) else t("SETTING_OFF")
        dmg_val = t("SETTING_ON") if settings_manager.get("damage_numbers", True) else t("SETTING_OFF")
        mm_val = t("SETTING_ON") if settings_manager.get("minimap", True) else t("SETTING_OFF")

        options = [
            f"{t('SETTING_LANG')}: < {lang_val} >",
            f"{t('SETTING_SHAKE')}: < {shake_val} >",
            f"{t('SETTING_DAMAGE_NUMS')}: < {dmg_val} >",
            f"{t('SETTING_MINIMAP')}: < {mm_val} >",
            t("SETTING_BACK"),
        ]

        for i, opt in enumerate(options):
            y = 200 + i * 65
            is_selected = (i == selected_option)
            color = YELLOW if is_selected else WHITE
            font = self.font_large if is_selected else self.font_medium

            text = font.render(opt, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))

            if is_selected:
                highlight = pygame.Rect(text_rect.x - 20, text_rect.y - 5,
                                       text_rect.width + 40, text_rect.height + 10)
                pygame.draw.rect(screen, (30, 30, 50), highlight)
                pygame.draw.rect(screen, YELLOW, highlight, 2)

            screen.blit(text, text_rect)

        hint = self.font_small.render(t("SETTINGS_HINT"), True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        screen.blit(hint, hint_rect)

    # ================================================================
    # ДОСТИЖЕНИЯ
    # ================================================================
    def draw_achievements_screen(self, screen, achievement_manager):
        screen.fill((15, 15, 30))

        title = self.font_large.render(t("ACH_TITLE"), True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title, title_rect)

        start_y = 110
        for i, ach_id in enumerate(ACHIEVEMENTS_LIST):
            y = start_y + i * 65
            unlocked = achievement_manager.is_unlocked(ach_id)

            rect = pygame.Rect(180, y, SCREEN_WIDTH - 360, 55)
            bg_c = (40, 50, 40) if unlocked else (30, 30, 40)
            pygame.draw.rect(screen, bg_c, rect)
            pygame.draw.rect(screen, GOLD if unlocked else GRAY, rect, 1)

            icon_str = "🏆" if unlocked else "🔒"
            icon_s = self.font.render(icon_str, True, GOLD if unlocked else GRAY)
            screen.blit(icon_s, (rect.x + 15, rect.y + 12))

            title_str = t(f"ach_{ach_id}_title")
            t_s = self.font.render(title_str, True, GOLD if unlocked else WHITE)
            screen.blit(t_s, (rect.x + 55, rect.y + 8))

            desc_str = t(f"ach_{ach_id}_desc")
            d_s = self.font_small.render(desc_str, True, LIGHT_GRAY if unlocked else GRAY)
            screen.blit(d_s, (rect.x + 55, rect.y + 32))

        back = self.font.render(t("ESC_RETURN_HINT"), True, GRAY)
        back_rect = back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(back, back_rect)

    # ================================================================
    # ГЛАВНОЕ МЕНЮ
    # ================================================================
    def draw_main_menu(self, screen, selected_option, selected_hero_index=0):
        screen.fill((12, 14, 28))

        t_time = pygame.time.get_ticks() / 1000.0

        # Анимированный динамический фон (дрейфующие неоновые частицы)
        for i in range(35):
            px = int((math.sin(t_time * 0.4 + i * 0.7) * 0.5 + 0.5) * SCREEN_WIDTH)
            py = int((math.cos(t_time * 0.25 + i * 1.1) * 0.5 + 0.5) * SCREEN_HEIGHT)
            alpha = int(abs(math.sin(t_time * 1.5 + i)) * 110)
            size = 3 if i % 2 == 0 else 5
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            color = (0, 220, 255, alpha) if i % 3 == 0 else (255, 200, 50, alpha)
            s.fill(color)
            screen.blit(s, (px, py))

        # Заголовок игры с неоновой тенью
        title = self.font_title.render(t("TITLE"), True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2 - 120, 100))

        shadow = self.font_title.render(t("TITLE"), True, DARK_BLUE)
        screen.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
        screen.blit(title, title_rect)

        subtitle = self.font.render(t("SUBTITLE"), True, GOLD)
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2 - 120, 160))
        screen.blit(subtitle, sub_rect)

        # Меню слева
        menu_items = [
            t("MENU_PLAY"),
            t("MENU_HEROES"),
            t("MENU_ACHIEVEMENTS"),
            t("MENU_SETTINGS"),
            t("MENU_CONTROLS"),
            t("MENU_HIGHSCORES"),
            t("MENU_EXIT"),
        ]

        menu_x = SCREEN_WIDTH // 2 - 120

        for i, item in enumerate(menu_items):
            y = 230 + i * 48
            is_selected = (i == selected_option)

            color = YELLOW if is_selected else WHITE
            font = self.font_large if is_selected else self.font_medium

            text = font.render(item, True, color)
            text_rect = text.get_rect(center=(menu_x, y))

            if is_selected:
                highlight = pygame.Rect(
                    text_rect.x - 25, text_rect.y - 6,
                    text_rect.width + 50, text_rect.height + 12
                )
                pygame.draw.rect(screen, (35, 45, 75), highlight, border_radius=6)
                pygame.draw.rect(screen, YELLOW, highlight, 2, border_radius=6)

                arrow_l = self.font_large.render("►", True, YELLOW)
                screen.blit(arrow_l, (highlight.x - 32, text_rect.y))

            screen.blit(text, text_rect)

        # Карточка выбранного героя (справа от меню)
        hero_key = HERO_KEYS[selected_hero_index] if 0 <= selected_hero_index < len(HERO_KEYS) else HERO_KEYS[0]
        h_data = HEROES.get(hero_key, HEROES["slider"])

        card_w, card_h = 240, 310
        card_x = SCREEN_WIDTH - card_w - 60
        card_y = 180
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        pygame.draw.rect(screen, (22, 28, 48), card_rect, border_radius=12)
        pygame.draw.rect(screen, CYAN, card_rect, 2, border_radius=12)

        # Аватар героя
        cx = card_x + card_w // 2
        cy = card_y + 55
        pygame.draw.circle(screen, h_data["color"], (cx, cy), 35)
        pygame.draw.circle(screen, h_data["outline_color"], (cx, cy), 35, 3)

        # Данные героя
        h_name = self.font.render(t(f"hero_{hero_key}_name"), True, WHITE)
        screen.blit(h_name, h_name.get_rect(center=(cx, card_y + 110)))

        h_sub = self.font_small.render(t(f"hero_{hero_key}_sub"), True, GOLD)
        screen.blit(h_sub, h_sub.get_rect(center=(cx, card_y + 135)))

        ult_name = t(f"{h_data['ult_id']}_name")
        ult_lbl = self.font_small.render(f"⚡ {ult_name}", True, CYAN)
        screen.blit(ult_lbl, ult_lbl.get_rect(center=(cx, card_y + 175)))

        change_hint = self.font_small.render(t("MENU_HEROES"), True, GRAY)
        screen.blit(change_hint, change_hint.get_rect(center=(cx, card_y + 270)))

        # Подсказка снизу
        hint = self.font_small.render(f"{t('MENU_HINT')}  |  [F1] Trainer", True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25))
        screen.blit(hint, hint_rect)

    # ================================================================
    # РЕКОРДЫ
    # ================================================================
    def draw_highscores_screen(self, screen):
        screen.fill((15, 15, 30))

        title = self.font_large.render(t("HIGHSCORES_TITLE"), True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title, title_rect)

        scores = load_highscores()

        headers = [t("HS_RANK"), t("HS_SCORE"), t("HS_TIME"), t("HS_LEVEL"), t("HS_KILLS")]
        hx = [200, 350, 500, 650, 800]

        for i, h in enumerate(headers):
            hs = self.font.render(h, True, YELLOW)
            hr = hs.get_rect(center=(hx[i], 110))
            screen.blit(hs, hr)

        pygame.draw.line(screen, GRAY, (150, 130), (SCREEN_WIDTH - 150, 130), 1)

        if not scores:
            no_scores = self.font.render(t("HS_NO_SCORES"), True, LIGHT_GRAY)
            nr = no_scores.get_rect(center=(SCREEN_WIDTH // 2, 250))
            screen.blit(no_scores, nr)
        else:
            for i, score in enumerate(scores):
                y = 155 + i * 40

                if i == 0:
                    c = GOLD
                elif i == 1:
                    c = SILVER
                elif i == 2:
                    c = BROWN
                else:
                    c = WHITE

                values = [
                    f"{i + 1}.",
                    str(score.get("score", 0)),
                    format_time(score.get("time", 0)),
                    str(score.get("level", 0)),
                    str(score.get("kills", 0)),
                ]

                for j, val in enumerate(values):
                    vs = self.font.render(val, True, c)
                    vr = vs.get_rect(center=(hx[j], y))
                    screen.blit(vs, vr)

        back = self.font.render(t("ESC_RETURN_HINT"), True, GRAY)
        back_rect = back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(back, back_rect)

    # ================================================================
    # УПРАВЛЕНИЕ
    # ================================================================
    def draw_controls_screen(self, screen):
        screen.fill((15, 15, 30))

        title = self.font_large.render(t("CONTROLS_TITLE"), True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title, title_rect)

        controls = [
            (t("CTRL_MOVE_KEY"), t("CTRL_MOVE_DESC")),
            (t("CTRL_SLIDE_KEY"), t("CTRL_SLIDE_DESC")),
            (t("CTRL_DASH_KEY"), t("CTRL_DASH_DESC")),
            (t("CTRL_ULT_KEY"), t("CTRL_ULT_DESC")),
            (t("CTRL_LOOK_KEY"), t("CTRL_LOOK_DESC")),
            (t("CTRL_SELECT_KEY"), t("CTRL_SELECT_DESC")),
            (t("CTRL_PAUSE_KEY"), t("CTRL_PAUSE_DESC")),
            ("", ""),
            (t("CTRL_HEADER_SLIDE"), ""),
            ("", t("CTRL_SLIDE_INFO_1")),
            ("", t("CTRL_SLIDE_INFO_2")),
            ("", t("CTRL_SLIDE_INFO_3")),
            ("", t("CTRL_SLIDE_INFO_4")),
            ("", t("CTRL_PERFECT_DODGE")),
            ("", ""),
            (t("CTRL_HEADER_DASH"), ""),
            ("", t("CTRL_DASH_INFO_1")),
            ("", t("CTRL_DASH_INFO_2")),
            ("", ""),
            (t("CTRL_HEADER_COMBO"), ""),
            ("", t("CTRL_COMBO_INFO_1")),
        ]

        y = 85
        for key, desc in controls:
            if key:
                key_s = self.font.render(key, True, YELLOW)
                screen.blit(key_s, (80, y))
            if desc:
                desc_s = self.font.render(desc, True, WHITE)
                x_pos = 420 if key else 80
                screen.blit(desc_s, (x_pos, y))
            y += 26

        back = self.font.render(t("ESC_RETURN_HINT"), True, GRAY)
        back_rect = back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(back, back_rect)

    # ================================================================
    # ПАУЗА
    # ================================================================
    def draw_pause(self, screen, selected_option):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))

        title = self.font_title.render(t("PAUSE_TITLE"), True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(title, title_rect)

        pause_items = [t("PAUSE_RESUME"), t("PAUSE_SETTINGS"), t("PAUSE_MAIN_MENU")]

        for i, item in enumerate(pause_items):
            y = 330 + i * 65
            is_selected = (i == selected_option)
            color = YELLOW if is_selected else WHITE
            font = self.font_large if is_selected else self.font_medium

            text = font.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))

            if is_selected:
                highlight = pygame.Rect(text_rect.x - 20, text_rect.y - 5,
                                       text_rect.width + 40, text_rect.height + 10)
                pygame.draw.rect(screen, (40, 40, 60), highlight)
                pygame.draw.rect(screen, YELLOW, highlight, 2)

            screen.blit(text, text_rect)

    # ================================================================
    # GAME OVER
    # ================================================================
    def draw_game_over(self, screen, player, game_time, selected_option, new_record_pos=-1):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        screen.blit(overlay, (0, 0))

        title = self.font_title.render(t("GAME_OVER_TITLE"), True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(title, title_rect)

        if new_record_pos >= 0:
            record_text = t("NEW_RECORD_MSG", new_record_pos + 1)
            record_s = self.font_large.render(record_text, True, GOLD)
            record_r = record_s.get_rect(center=(SCREEN_WIDTH // 2, 180))
            screen.blit(record_s, record_r)

        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        score = calculate_score(game_time, player.level, player.enemies_killed)

        stats = [
            t("GO_TIME", f"{minutes:02d}:{seconds:02d}"),
            t("GO_LEVEL", player.level),
            t("GO_KILLS", player.enemies_killed),
            t("GO_MAX_COMBO", player.combo_max_reached),
            t("GO_SCORE", score),
        ]

        y = 230
        for stat in stats:
            text = self.font.render(stat, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            screen.blit(text, text_rect)
            y += 35

        options = [t("GO_RETRY"), t("GO_MENU")]

        for i, item in enumerate(options):
            oy = 460 + i * 60
            is_selected = (i == selected_option)
            color = YELLOW if is_selected else WHITE
            font = self.font_large if is_selected else self.font_medium

            text = font.render(item, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, oy))

            if is_selected:
                highlight = pygame.Rect(text_rect.x - 20, text_rect.y - 5,
                                       text_rect.width + 40, text_rect.height + 10)
                pygame.draw.rect(screen, (40, 40, 60), highlight)
                pygame.draw.rect(screen, YELLOW, highlight, 2)

            screen.blit(text, text_rect)