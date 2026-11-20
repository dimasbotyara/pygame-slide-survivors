# ui.py — User Interface with localization, hero selection, boss bar & achievements

import pygame
import math
from settings import *
from highscores import load_highscores, format_time, calculate_score
from translations import t
from heroes import HEROES, HERO_KEYS
from achievements import ACHIEVEMENTS_LIST
from typography import TextFont

INK = (12, 18, 29)
PANEL = (23, 34, 50)
EDGE = (54, 73, 91)
MUTED = (159, 180, 194)
MINT = (109, 249, 197)
PAPER = (233, 242, 246)


def menu_rect(i):
    return pygame.Rect(70, 222 + i * 56, 540, 48)


def pause_rect(i):
    return pygame.Rect(SCREEN_WIDTH // 2 - 250, 273 + i * 64, 500, 54)


def hero_rect(i):
    return pygame.Rect((SCREEN_WIDTH - (len(HERO_KEYS)*285 - 25))//2 + i*285, 190, 260, 360)


def upgrade_rect(i, count):
    width = min(UI_UPGRADE_BOX_WIDTH, (SCREEN_WIDTH - 80 - (count-1)*20)//count)
    x = (SCREEN_WIDTH - count*width - (count-1)*20)//2
    return pygame.Rect(x + i*(width+20), 192, width, UI_UPGRADE_BOX_HEIGHT)


def language_rect(i):
    return pygame.Rect(420, 290 + 74*i, 440, 60)


def settings_rect(i):
    return pygame.Rect(320, 185 + 65*i, 640, 54)


def result_rect(i):
    return pygame.Rect(410, 440 + i*65, 460, 54)


def menu_inputs(events, rects):
    """Yield (focused index, key); a left click activates just like Enter."""
    for event in events:
        if event.type == pygame.KEYDOWN:
            yield None, event.key
        elif event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            for i, rect in enumerate(rects):
                if rect.collidepoint(event.pos):
                    yield i, pygame.K_RETURN if event.type == pygame.MOUSEBUTTONDOWN else None
                    break


def word_lines(font, text, width):
    line = ''
    for word in text.split():
        joined = f'{line} {word}' if line else word
        if line and font.size(joined)[0] > width:
            yield line
            line = word
        else:
            line = joined
    if line:
        yield line


class UI:
    def __init__(self):
        pygame.font.init()
        self.font = TextFont('body', UI_FONT_SIZE)
        self.font_large = TextFont('display', 42)
        self.font_small = TextFont('label', UI_FONT_SIZE_SMALL)
        self.font_title = TextFont('poster', 54)
        self.font_medium = TextFont('display', 29)
        self.font_combo = TextFont('display', 36)
        self.mono = TextFont('mono', 16)
        self.body = TextFont('body', 19)

    def button(self, screen, rect, label, index, selected):
        fg = INK if selected else PAPER
        pygame.draw.rect(screen, MINT if selected else PANEL, rect, border_radius=6)
        if not selected:
            pygame.draw.rect(screen, EDGE, rect, 1, border_radius=6)
        number = self.mono.render(f'{index+1:02}', True, fg if selected else MUTED)
        screen.blit(number, number.get_rect(midleft=(rect.left+18, rect.centery)))
        text = self.font.render(label, True, fg)
        screen.blit(text, text.get_rect(midleft=(rect.left+62, rect.centery)))
        if selected:
            x, y = rect.right-25, rect.centery
            pygame.draw.lines(screen, INK, False, [(x-5,y-6),(x+1,y),(x-5,y+6)], 3)

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

        remaining = self.mono.render(t('UPGRADE_REMAINING', player.pending_levels + 1), True, PAPER)
        screen.blit(remaining, remaining.get_rect(center=(SCREEN_WIDTH // 2, 149)))

        for i, upgrade in enumerate(choices):
            r = upgrade_rect(i, len(choices))
            active = i == selected_index
            pygame.draw.rect(screen, PANEL, r, border_radius=10)
            pygame.draw.rect(screen, MINT if active else EDGE, r, 3 if active else 1, border_radius=10)
            x, y = r.x + 24, r.y + 22
            category = {'fist': 'CAT_COMBAT', 'hero': 'CAT_HERO', 'slide': 'CAT_SLIDE',
                        'utility': 'CAT_SPECIAL', 'basic': 'CAT_BASIC'}[upgrade.category]
            pygame.draw.circle(screen, upgrade.icon_color, (x+7, y+13), 7)
            screen.blit(self.body.render(t(category), True, PAPER), (x+23, y))
            badge = self.mono.render(f'0{i+1}', True, MUTED)
            screen.blit(badge, badge.get_rect(topright=(r.right-24, y)))
            y += 52
            for line in word_lines(self.font_medium, upgrade.name, r.w-48):
                screen.blit(self.font_medium.render(line, True, PAPER), (x, y))
                y += 36
            y += 14
            for line in word_lines(self.body, upgrade.description, r.w-48):
                screen.blit(self.body.render(line, True, MUTED), (x, y))
                y += 25
            pygame.draw.line(screen, EDGE, (x, r.bottom-75), (r.right-24, r.bottom-75))
            current, cap = upgrade.current_level, upgrade.max_level
            progress = f'{current} → {current + 1}' + (f' / {cap}' if cap else '')
            level = self.body.render(t('UPGRADE_LVL', progress), True, MINT if active else PAPER)
            screen.blit(level, (x, r.bottom-60))
            if cap:
                pygame.draw.rect(screen, EDGE, (x, r.bottom-24, r.w-48, 4))
                pygame.draw.rect(screen, upgrade.icon_color, (x, r.bottom-24, int((r.w-48)*(current+1)/cap), 4))

        hint = self.body.render(t('UPGRADE_HINT'), True, PAPER)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-90)))

    # ================================================================
    # ВЫБОР ПЕРСОНАЖА
    # ================================================================
    def draw_hero_select_screen(self, screen, selected_index):
        screen.fill((15, 15, 30))

        title = self.font_large.render(t("HERO_SELECT_TITLE"), True, CYAN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title, title_rect)

        for i, key in enumerate(HERO_KEYS):
            h_data = HEROES[key]
            rect = hero_rect(i)
            bx, by, box_w = rect.x, rect.y, rect.w
            pygame.draw.rect(screen, PANEL, rect, border_radius=10)
            pygame.draw.rect(screen, MINT if i == selected_index else EDGE, rect,
                             3 if i == selected_index else 1, border_radius=10)

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
                for line in word_lines(self.font_small, part, box_w - 28):
                    p_s = self.font_small.render(line, True, LIGHT_GRAY)
                    screen.blit(p_s, p_s.get_rect(center=(cx, y_offset)))
                    y_offset += 23

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
            self.button(screen, language_rect(i), opt, i, i == selected_option)

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
            self.button(screen, settings_rect(i), opt, i, i == selected_option)

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
        screen.fill(INK)
        key = HERO_KEYS[selected_hero_index]
        hero = HEROES[key]
        accent = hero['color']
        # Track markings behind the two panels.
        for x in range(-300, SCREEN_WIDTH, 68):
            pygame.draw.line(screen, (19, 29, 43), (x, SCREEN_HEIGHT), (x+350, 0), 1)
        screen.blit(self.mono.render('SS  /  ' + t('LOBBY'), True, MINT), (70, 40))
        pygame.draw.line(screen, EDGE, (70, 76), (1210, 76))
        screen.blit(self.font_title.render(t('TITLE'), True, PAPER), (66, 85))
        screen.blit(self.body.render(t('SUBTITLE'), True, MUTED), (72, 163))
        keys = ('MENU_PLAY', 'MENU_HEROES', 'MENU_ACHIEVEMENTS', 'MENU_SETTINGS',
                'MENU_CONTROLS', 'MENU_HIGHSCORES', 'MENU_EXIT')
        for i, label in enumerate(keys):
            self.button(screen, menu_rect(i), t(label), i, i == selected_option)

        card = pygame.Rect(661, 202, 549, 405)
        pygame.draw.rect(screen, PANEL, card, border_radius=12)
        pygame.draw.rect(screen, EDGE, card, 1, border_radius=12)
        x = card.x + 28
        screen.blit(self.mono.render(t('ACTIVE_FIGHTER'), True, MUTED), (x, 225))
        serial = self.mono.render(f'{selected_hero_index+1:02} / {len(HERO_KEYS):02}', True, accent)
        screen.blit(serial, serial.get_rect(topright=(card.right-28, 225)))
        # Hero emblem with a contrail, orbit ticks and the fighter's own colours.
        cx, cy = card.centerx, 329
        for j in range(3):
            pygame.draw.line(screen, EDGE, (cx-115+j*12, cy+29-j*14), (cx-18, cy+10-j*14), 3)
        pygame.draw.circle(screen, EDGE, (cx,cy), 60, 1)
        for j in range(4):
            ang = pygame.time.get_ticks()*0.0006 + j*math.pi/2
            pygame.draw.arc(screen, accent, (cx-61,cy-61,122,122), ang, ang+0.38, 3)
        pygame.draw.circle(screen, hero['outline_color'], (cx,cy), 36)
        pygame.draw.circle(screen, accent, (cx,cy), 32)
        pygame.draw.line(screen, INK, (cx+3,cy-9), (cx+24,cy-12), 5)
        pygame.draw.circle(screen, accent, (cx+29,cy+22), 10)
        pygame.draw.circle(screen, INK, (cx+29,cy+22), 10, 2)
        for font, field, y, color in [(self.font_medium, 'name', 417, PAPER),
                                      (self.body, 'sub', 450, MUTED)]:
            label = font.render(t(f'hero_{key}_{field}'), True, color)
            screen.blit(label, label.get_rect(center=(cx, y)))
        pygame.draw.line(screen, EDGE, (x, 484), (card.right-28, 484))
        screen.blit(self.mono.render(t('ULT_LABEL'), True, MUTED), (x, 509))
        screen.blit(self.font.render('⚡ ' + t(hero['ult_id']+'_name'), True, accent), (x, 538))
        pygame.draw.line(screen, EDGE, (70, 646), (1210, 646))
        screen.blit(self.body.render(t('MENU_HINT'), True, MUTED), (70, 661))

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

        pause_items = ('PAUSE_RESUME', 'PAUSE_SETTINGS', 'PAUSE_SURRENDER', 'PAUSE_MAIN_MENU')
        for i, label in enumerate(pause_items):
            self.button(screen, pause_rect(i), t(label), i, i == selected_option)

    # ================================================================
    # GAME OVER
    # ================================================================
    def draw_game_over(self, screen, player, game_time, selected_option, new_record_pos=-1, surrendered=False):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(180)
        screen.blit(overlay, (0, 0))

        title = self.font_title.render(t("RUN_COMPLETE" if surrendered else "GAME_OVER_TITLE"), True, MINT if surrendered else RED)
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
            self.button(screen, result_rect(i), item, i, i == selected_option)
