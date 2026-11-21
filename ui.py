# ui.py — User Interface with localization, hero selection, boss bar & achievements

import pygame
import math
from functools import lru_cache
from settings import *
from highscores import load_highscores, format_time, calculate_score
from translations import t
from heroes import HEROES, HERO_KEYS
from achievements import ACHIEVEMENTS_LIST
from typography import TextFont
from consumables import tonic_icon
from preferences import TABS, DEFAULTS

INK = (12, 18, 29)
PANEL = (23, 34, 50)
EDGE = (54, 73, 91)
MUTED = (159, 180, 194)
MINT = (109, 249, 197)
PAPER = (233, 242, 246)
_BASE_PALETTE = {'INK': INK, 'PANEL': PANEL, 'EDGE': EDGE, 'MUTED': MUTED,
                 'MINT': MINT, 'PAPER': PAPER}
_THEME_COLORS = {
    'cyan': (63, 211, 229), 'red': (244, 89, 107), 'yellow': (247, 207, 78),
    'purple': (178, 113, 255), 'green': (91, 220, 158), 'orange': (255, 151, 75),
}
_HERO_PALETTES = {
    # Softer teal: less saturated blue than the original slider accent.
    'slider': {'INK': (15, 27, 34), 'PANEL': (23, 39, 47), 'EDGE': (57, 87, 92),
               'MUTED': (153, 184, 183), 'PAPER': (229, 239, 235), 'MINT': (90, 185, 181)},
    # Gruvbox Dark (hard-coded palette family).
    'spark': {'INK': (40, 40, 40), 'PANEL': (60, 56, 54), 'EDGE': (102, 92, 84),
              'MUTED': (189, 174, 147), 'PAPER': (235, 219, 178), 'MINT': (250, 189, 47)},
    # Catppuccin Mocha with a violet/lavender accent.
    'shadow': {'INK': (30, 30, 46), 'PANEL': (49, 50, 68), 'EDGE': (88, 91, 112),
               'MUTED': (166, 173, 200), 'PAPER': (205, 214, 244), 'MINT': (203, 166, 247)},
}


def _mix(a, b, amount):
    return tuple(round(x * (1 - amount) + y * amount) for x, y in zip(a, b))


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
    return pygame.Rect(70, 177 + 53*i, 1140, 47)


def settings_value_left_rect(i):
    row = settings_rect(i)
    return pygame.Rect(row.right-238, row.y+6, 34, row.h-12)


def settings_value_right_rect(i):
    row = settings_rect(i)
    return pygame.Rect(row.right-54, row.y+6, 34, row.h-12)


def settings_tab_rect(i):
    gap = 8
    width = (1140-gap*(len(TABS)-1))//len(TABS)
    return pygame.Rect(70+i*(width+gap), 102, width, 48)


def result_rect(i):
    return pygame.Rect(410, 440 + i*65, 460, 54)


def bestiary_rect():
    return pygame.Rect(982, 29, 228, 38)


def hero_arrow_rect(step):
    return pygame.Rect(703 if step < 0 else 1116, 303, 52, 52)


NUMBER_KEYS = {getattr(pygame, f'K_{prefix}{n}'): n - 1
               for prefix in ('', 'KP') for n in range(1, 10)}


def menu_inputs(events, rects, extra_buttons=()):
    """Yield (focused index, key); clicks and digits activate the same item as Enter."""
    for event in events:
        if event.type == pygame.KEYDOWN:
            index = NUMBER_KEYS.get(event.key)
            if index is None:
                yield None, event.key
            elif index < len(rects):
                yield index, pygame.K_RETURN
        elif event.type == pygame.MOUSEMOTION or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, key in extra_buttons:
                    if rect.collidepoint(event.pos):
                        yield None, key
                        break
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
        self.fitted_text = lru_cache(maxsize=128)(self.fitted_text)
        self.achievement_scroll = 0
        self.achievement_dragging = False
        self.apply_theme()

    def setting(self, key):
        settings = getattr(self, 'settings', None)
        return settings.get(key, DEFAULTS.get(key)) if settings else DEFAULTS.get(key)

    def apply_theme(self, selected_hero_index=0, theme='hero'):
        """Apply the chosen palette to menu screens, HUD, and shared UI effects."""
        global INK, PANEL, EDGE, MUTED, MINT, PAPER, CYAN, GOLD, YELLOW, ORANGE, PURPLE, TEAL
        global DARK_BLUE, DARK_GRAY, GRAY, LIGHT_GRAY
        hero_theme = theme == 'hero'
        if hero_theme:
            hero_id = HERO_KEYS[selected_hero_index % len(HERO_KEYS)]
            accent = HEROES[hero_id]['color']
            palette = _HERO_PALETTES.get(hero_id)
        else:
            hero_id = None
            accent = _THEME_COLORS.get(theme, _THEME_COLORS['cyan'])
            palette = None
        if palette:
            INK, PANEL, EDGE = palette['INK'], palette['PANEL'], palette['EDGE']
            MUTED, PAPER, MINT = palette['MUTED'], palette['PAPER'], palette['MINT']
            accent = MINT
        else:
            # Tinted dark surfaces retain readable contrast for custom themes
            # and the Brawler's original crimson palette.
            INK = _mix((12, 18, 29), accent, .12)
            PANEL = _mix((23, 34, 50), accent, .16)
            EDGE = _mix((54, 73, 91), accent, .48)
            MUTED = _mix((159, 180, 194), accent, .38)
            PAPER = _mix((233, 242, 246), accent, .12)
            MINT = accent
        CYAN = GOLD = YELLOW = ORANGE = PURPLE = TEAL = accent
        DARK_BLUE = _mix(INK, accent, .35)
        DARK_GRAY = _mix(PANEL, accent, .14)
        GRAY = EDGE
        LIGHT_GRAY = MUTED
        # Bestiary caches its imported palette, so refresh those bindings too.
        import sys
        guide = sys.modules.get('bestiary')
        if guide is not None:
            for name in ('INK', 'PANEL', 'EDGE', 'MUTED', 'MINT', 'PAPER'):
                setattr(guide, name, globals()[name])
        # Keep an instance copy as well as the module palette. Game-level
        # overlays (e.g. the FPS badge) consume these values through UI.
        self.INK, self.PANEL, self.EDGE = INK, PANEL, EDGE
        self.MUTED, self.MINT, self.PAPER = MUTED, MINT, PAPER
        self.theme_accent = accent
        self.theme_palette = {'accent': MINT, 'panel': PANEL, 'edge': EDGE, 'text': PAPER}
        game = getattr(self, 'game', None)
        manager = getattr(game, 'particle_manager', None)
        if manager is not None:
            manager.theme_palette = self.theme_palette

    def fitted_text(self, text, color, width, height, max_size=14):
        # Measure rendered glyphs, not the nominal point size (Cyrillic/descenders).
        for px in range(max_size, 5, -1):
            result = TextFont('label', px).render(text, True, color)
            bounds = result.get_bounding_rect()
            if bounds.w and bounds.h:
                result = result.subsurface(bounds).copy()
            if result.get_width() <= width and result.get_height() <= height:
                return result
        return pygame.transform.smoothscale(result, (min(width, result.get_width()), min(height, result.get_height())))

    def begin_transition(self, frame):
        self.transition_frame = frame
        self.transition_started = pygame.time.get_ticks()

    def draw_transition(self, screen):
        frame = getattr(self, 'transition_frame', None)
        if frame is None:
            return
        progress = min(1, (pygame.time.get_ticks()-self.transition_started)/280)
        if progress >= 1:
            self.transition_frame = None
            return
        frame.set_alpha(round(255*(1-progress)**3))
        screen.blit(frame, (0, round(-16*progress)))

    def button(self, screen, rect, label, index, selected):
        fg = INK if selected else PAPER
        pygame.draw.rect(screen, MINT if selected else PANEL, rect, border_radius=6)
        if not selected:
            pygame.draw.rect(screen, EDGE, rect, 1, border_radius=6)
        number = self.mono.render(f'{index+1:02}', True, fg if selected else MUTED)
        screen.blit(number, number.get_rect(midleft=(rect.left+18, rect.centery)))
        text = (self.body if rect.w < 300 else self.font).render(label, True, fg)
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
        for i, (kind, seconds) in enumerate(player.tonic_timers.items()):
            rect = pygame.Rect(UI_MARGIN + i * 66, SCREEN_HEIGHT - UI_XP_BAR_HEIGHT - 34, 62, 28)
            pygame.draw.rect(screen, INK, rect, border_radius=6)
            icon = tonic_icon(kind)
            screen.blit(icon, icon.get_rect(center=(rect.x+14, rect.centery)))
            clock = self.mono.render(str(math.ceil(seconds)), True, PAPER)
            screen.blit(clock, clock.get_rect(midright=(rect.right-6, rect.centery)))
        self.draw_slide_indicator(screen, player)
        self.draw_ult_bar(screen, player)
        self.draw_stats_mini(screen, player, enemy_count)
        self.draw_combo(screen, player)
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

        ratio = 0.0 if player.ult_cooldown_timer > 0 or player.ult_cast_timer > 0 else player.ult_charge / 100.0
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(screen, DARK_GRAY, bg_rect)

        fill_w = int(bar_w * ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        fill_color = GOLD if player.can_use_ult() else YELLOW
        pygame.draw.rect(screen, fill_color, fill_rect)
        pygame.draw.rect(screen, PAPER if player.can_use_ult() else EDGE, bg_rect, 2)

        from heroes import HEROES
        hero_id = getattr(player, 'hero_id', 'slider')
        hero_info = HEROES.get(hero_id, HEROES["slider"])
        ult_id = hero_info["ult_id"]
        ult_name = t(f"{ult_id}_name")

        if player.ult_cooldown_timer > 0:
            message = t('ULT_COOLDOWN', math.ceil(player.ult_cooldown_timer))
            color = MUTED
        elif player.ult_cast_timer > 0:
            message = t('ULT_CASTING', max(1, math.ceil(player.ult_cast_timer)))
            color = MINT
        elif player.can_use_ult():
            message = t("ULT_READY", ult_name)
            color = GOLD
        else:
            message = f"{ult_name}: {int(player.ult_charge)}%"
            color = LIGHT_GRAY
        text_s = self.fitted_text(message, color, 230 if player.can_use_ult() else bar_w-8,
                                  17 if player.can_use_ult() or player.ult_cooldown_timer else bar_h-4, 14)
        text_r = text_s.get_rect(midleft=(bar_x, bar_y+28)) if player.can_use_ult() or player.ult_cooldown_timer else text_s.get_rect(center=bg_rect.center)
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

    def draw_stats_mini(self, screen, player, enemy_count):
        if not self.setting('hud_stats'):
            return
        x, y = SCREEN_WIDTH-274, UI_MARGIN
        stats = [('KILLS', player.enemies_killed, MINT), ('ENEMIES', enemy_count, MINT),
                 ('SPEED', int(player.current_speed), CYAN), ('COMBO', player.combo_max_reached, GOLD)]
        for i, (label, value, accent) in enumerate(stats):
            rect = pygame.Rect(x+(i%2)*132, y+(i//2)*51, 126, 45)
            pygame.draw.rect(screen, INK, rect, border_radius=7)
            pygame.draw.rect(screen, EDGE, rect, 1, border_radius=7)
            pygame.draw.rect(screen, accent, (rect.x+9, rect.y+10, 2, 25), border_radius=1)
            label_s = TextFont('label', 11).render(t('HUD_'+label), True, MUTED)
            screen.blit(label_s, (rect.x+19, rect.y+5))
            value_s = self.fitted_text(str(value), accent, 98, 22, 20)
            screen.blit(value_s, (rect.x+19, rect.y+20))

    # ================================================================
    # МИНИ-КАРТА
    # ================================================================
    def draw_minimap(self, screen, player, enemies, xp_orbs, dropped_items, bosses_alive, world=None, game_time=0):
        mm_size = MINIMAP_SIZE
        mm_x = SCREEN_WIDTH - mm_size - MINIMAP_MARGIN
        mm_y = SCREEN_HEIGHT - mm_size - MINIMAP_MARGIN - UI_XP_BAR_HEIGHT - 5
        center = mm_size // 2
        radius = center - 3

        mm_surface = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)

        # Тёмный прозрачный круговой фон
        pygame.draw.circle(mm_surface, (*INK, 220), (center, center), radius)

        if world is not None:
            biome = world.biome_at(player.x, player.y)
            key = t('BIOME_'+biome.key)
            if getattr(self, '_biome_label_key', None) != key:
                self._biome_label_key = key
                self._biome_label = self.font_small.render(key, True, PAPER)
            screen.blit(self._biome_label, self._biome_label.get_rect(midbottom=(mm_x+center, mm_y-4)))

        # Радарная сетка (концентрические круги)
        pygame.draw.circle(mm_surface, (*MINT, 45), (center, center), int(radius * 0.66), 1)
        pygame.draw.circle(mm_surface, (*MINT, 25), (center, center), int(radius * 0.33), 1)

        # Перекрестие (север-юг-запад-восток)
        pygame.draw.line(mm_surface, (*MINT, 40), (center, 6), (center, mm_size - 6), 1)
        pygame.draw.line(mm_surface, (*MINT, 40), (6, center), (mm_size - 6, center), 1)

        # Вращающийся луч радара
        t_time = game_time
        sweep_angle = (t_time * 2.2) % (math.pi * 2)
        end_x = center + int(math.cos(sweep_angle) * radius)
        end_y = center + int(math.sin(sweep_angle) * radius)
        if self.setting("radar_sweep"):
            pygame.draw.line(mm_surface, (*MINT, 70), (center, center), (end_x, end_y), 2)

        # Опыт (XP gems)
        for orb in (xp_orbs if self.setting("minimap_pickups") else ()):
            dx = (orb.x - player.x) * MINIMAP_SCALE
            dy = (orb.y - player.y) * MINIMAP_SCALE
            if dx * dx + dy * dy <= radius * radius:
                mx = int(center + dx)
                my = int(center + dy)
                pygame.draw.circle(mm_surface, (255, 240, 80, 220), (mx, my), 1)

        # Выпавшие предметы (Health, Bomb, Magnet...)
        for item in (dropped_items if self.setting("minimap_pickups") else ()):
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
        pygame.draw.polygon(mm_surface, PAPER, [(p_front_x, p_front_y), (p_left_x, p_left_y), (p_right_x, p_right_y)], 1)

        # Внешнее неоновое кольцо радара
        pygame.draw.circle(mm_surface, MINT, (center, center), radius, 2)

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
        screen.fill(INK)
        for x in range(-200, SCREEN_WIDTH, 80):
            pygame.draw.line(screen, (22, 32, 46), (x, SCREEN_HEIGHT), (x+300, 0))
        screen.blit(self.mono.render('SS / '+t('ROSTER'), True, MINT), (70, 34))
        title = self.font_large.render(t("HERO_SELECT_TITLE"), True, PAPER)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title, title_rect)

        for i, key in enumerate(HERO_KEYS):
            h_data = HEROES[key]
            rect = hero_rect(i)
            bx, by, box_w = rect.x, rect.y, rect.w
            pygame.draw.rect(screen, PANEL, rect, border_radius=10)
            pygame.draw.rect(screen, MINT if i == selected_index else EDGE, rect,
                             3 if i == selected_index else 1, border_radius=10)

            screen.blit(self.mono.render(f"0{i+1}", True, MUTED), (bx+15, by+10))

            accent = h_data['color']
            pygame.draw.rect(screen, accent if i == selected_index else EDGE,
                             (bx+18, by+box_w//2+32, box_w-36, 2))
            if i == selected_index:
                pulse = 49 + int(3*math.sin(pygame.time.get_ticks()/350))
                pygame.draw.circle(screen, accent, (bx+box_w//2, by+60), pulse, 1)
            # Круг персонажа
            cx = bx + box_w // 2
            cy = by + 60
            pygame.draw.circle(screen, h_data["color"], (cx, cy), 35)
            pygame.draw.circle(screen, h_data["outline_color"], (cx, cy), 35, 3)

            pygame.draw.line(screen, INK, (cx+3,cy-9), (cx+24,cy-12), 5)
            pygame.draw.circle(screen, accent, (cx+29,cy+22), 10)
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

            for j, (label, value, maximum) in enumerate((
                    ('HERO_HP', h_data['base_hp'], 150),
                    ('HERO_SPEED', h_data['base_speed'], 260),
                    ('HERO_POWER', h_data['fist_damage_mult']*100, 150))):
                y = by+259+j*29
                screen.blit(self.font_small.render(t(label), True, MUTED), (bx+18, y))
                number = self.font_small.render(str(round(value)), True, PAPER)
                screen.blit(number, number.get_rect(topright=(rect.right-18, y)))
                pygame.draw.rect(screen, EDGE, (bx+18, y+21, box_w-36, 3), border_radius=1)
                pygame.draw.rect(screen, accent, (bx+18, y+21, round((box_w-36)*value/maximum), 3), border_radius=1)

        key = HERO_KEYS[selected_index]
        ultimate = self.body.render(t('ULT_LABEL')+' / '+t(HEROES[key]['ult_id']+'_name'), True, HEROES[key]['color'])
        screen.blit(ultimate, ultimate.get_rect(center=(SCREEN_WIDTH//2, 601)))
        hint = self.font_small.render(t("HERO_SELECT_HINT"), True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(hint, hint_rect)

    # ================================================================
    # ВЫБОР ЯЗЫКА (ПЕРВЫЙ ЗАПУСК)
    # ================================================================
    def draw_language_select_screen(self, screen, selected_option):
        screen.fill(INK)

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
    def draw_settings_screen(self, screen, selected_option, settings_manager, tab=0):
        screen.fill(INK)
        screen.blit(self.mono.render('SS / '+t('SETTINGS_TITLE'), True, MINT), (70, 35))
        pygame.draw.line(screen, EDGE, (70, 76), (1210, 76))
        for i, (name, _) in enumerate(TABS):
            self.button(screen, settings_tab_rect(i), t('TAB_'+name), i, i == tab)
        for i, (key, choices) in enumerate(TABS[tab][1]):
            rect = settings_rect(i)
            selected = i == selected_option
            pygame.draw.rect(screen, PANEL if selected else (17, 25, 38), rect, border_radius=6)
            pygame.draw.rect(screen, MINT if selected else EDGE, rect, 1, border_radius=6)
            if selected:
                pygame.draw.rect(screen, MINT, (rect.x, rect.y+9, 3, rect.h-18), border_radius=1)
            screen.blit(self.body.render(t('OPT_'+key), True, PAPER), (rect.x+20, rect.y+12))
            value = settings_manager.get(key)
            if type(value) is bool:
                text = t('SETTING_ON' if value else 'SETTING_OFF')
            elif key == 'resolution':
                text = t('NATIVE_RESOLUTION') if value == (0, 0) else f'{value[0]} × {value[1]}'
            elif key == 'language':
                text = t('LANG_RU' if value == 'ru' else 'LANG_EN')
            elif key == 'theme':
                text = t('THEME_' + str(value))
            elif key == 'fps_limit' and value == 0:
                text = t('UNLIMITED')
            elif key == 'camera_smoothing' and value == 0:
                text = t('SETTING_OFF')
            elif key == 'terrain_quality':
                text = t('QUALITY_'+value)
            elif key == 'biome_blend':
                text = t('BLEND_'+str(value))
            elif key == 'decoration_density':
                text = f'{value*100:g}%'
            elif key == 'particle_density':
                text = f'{value:g}×'
            else:
                text = str(value)
            value_color = MINT if selected else MUTED
            label = self.fitted_text(text, value_color, 164, rect.h-8, 19)
            screen.blit(label, label.get_rect(center=(rect.right-140, rect.centery)))
            left_arrow = self.body.render('‹', True, value_color)
            right_arrow = self.body.render('›', True, value_color)
            screen.blit(left_arrow, left_arrow.get_rect(center=settings_value_left_rect(i).center))
            screen.blit(right_arrow, right_arrow.get_rect(center=settings_value_right_rect(i).center))
        hint = self.body.render(t('SETTINGS_TABS_HINT'), True, MUTED)
        screen.blit(hint, (70, 674))
        note = self.font_small.render(t('SETTINGS_NOTE'), True, MUTED)
        screen.blit(note, (70, 620))

    # ================================================================
    # ДОСТИЖЕНИЯ
    # ================================================================
    ACH_LIST_RECT = pygame.Rect(70, 108, 1080, 526)
    ACH_TRACK_RECT = pygame.Rect(1164, 108, 16, 526)

    def achievement_scroll_metrics(self):
        viewport = self.ACH_LIST_RECT
        content_h = len(ACHIEVEMENTS_LIST) * 66 - 8
        maximum = max(0, content_h - viewport.h)
        scroll = max(0, min(maximum, getattr(self, 'achievement_scroll', 0)))
        self.achievement_scroll = scroll
        thumb_h = max(42, round(self.ACH_TRACK_RECT.h * viewport.h / max(viewport.h, content_h)))
        travel = self.ACH_TRACK_RECT.h - thumb_h
        thumb_y = self.ACH_TRACK_RECT.y + (round(travel * scroll / maximum) if maximum else 0)
        return maximum, pygame.Rect(self.ACH_TRACK_RECT.x, thumb_y, self.ACH_TRACK_RECT.w, thumb_h)

    def handle_achievement_event(self, event):
        maximum, thumb = self.achievement_scroll_metrics()
        if event.type == pygame.MOUSEWHEEL:
            self.achievement_scroll = max(0, min(maximum, self.achievement_scroll - event.y * 54))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (4, 5):
                self.achievement_scroll = max(0, min(maximum, self.achievement_scroll + (54 if event.button == 5 else -54)))
            elif event.button == 1 and self.ACH_TRACK_RECT.collidepoint(event.pos):
                if thumb.collidepoint(event.pos):
                    self.achievement_dragging = True
                    self.achievement_drag_offset = event.pos[1] - thumb.y
                else:
                    self.achievement_dragging = True
                    self.achievement_drag_offset = thumb.h // 2
                    self._drag_achievement_thumb(event.pos[1], maximum, thumb.h)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.achievement_dragging = False
        elif event.type == pygame.MOUSEMOTION and getattr(self, 'achievement_dragging', False):
            self._drag_achievement_thumb(event.pos[1], maximum, thumb.h)

    def _drag_achievement_thumb(self, mouse_y, maximum, thumb_h):
        travel = self.ACH_TRACK_RECT.h - thumb_h
        if maximum and travel:
            y = max(self.ACH_TRACK_RECT.y, min(self.ACH_TRACK_RECT.bottom - thumb_h,
                                               mouse_y - self.achievement_drag_offset))
            self.achievement_scroll = round((y - self.ACH_TRACK_RECT.y) * maximum / travel)

    def draw_achievements_screen(self, screen, achievement_manager):
        screen.fill(INK)
        title = self.font_large.render(t("ACH_TITLE"), True, MINT)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 48)))
        unlocked_count = sum(achievement_manager.is_unlocked(a) for a in ACHIEVEMENTS_LIST)
        status = self.body.render(f'{unlocked_count} / {len(ACHIEVEMENTS_LIST)}', True, MUTED)
        screen.blit(status, status.get_rect(topright=(1144, 34)))

        maximum, thumb = self.achievement_scroll_metrics()
        viewport = self.ACH_LIST_RECT
        old_clip = screen.get_clip()
        screen.set_clip(viewport)
        for i, ach_id in enumerate(ACHIEVEMENTS_LIST):
            y = viewport.y + i * 66 - self.achievement_scroll
            rect = pygame.Rect(viewport.x, y, viewport.w - 12, 58)
            unlocked = achievement_manager.is_unlocked(ach_id)
            bg = _mix(PANEL, self.theme_accent, .15) if unlocked else PANEL
            pygame.draw.rect(screen, bg, rect, border_radius=7)
            pygame.draw.rect(screen, MINT if unlocked else EDGE, rect, 2 if unlocked else 1, border_radius=7)
            pygame.draw.circle(screen, MINT if unlocked else EDGE, (rect.x + 25, rect.centery), 13, 2)
            # Font-independent trophy/lock mark avoids missing emoji glyphs.
            if unlocked:
                pygame.draw.rect(screen, MINT, (rect.x + 20, rect.y + 18, 10, 11), border_radius=2)
                pygame.draw.line(screen, MINT, (rect.x + 18, rect.y + 31), (rect.x + 32, rect.y + 31), 2)
                pygame.draw.line(screen, MINT, (rect.x + 25, rect.y + 29), (rect.x + 25, rect.y + 36), 2)
            else:
                pygame.draw.arc(screen, MUTED, (rect.x + 20, rect.y + 13, 10, 12), 0, math.pi, 2)
                pygame.draw.rect(screen, MUTED, (rect.x + 19, rect.y + 20, 12, 12), border_radius=2)
            title_s = self.body.render(t(f"ach_{ach_id}_title"), True, MINT if unlocked else PAPER)
            desc_s = self.font_small.render(t(f"ach_{ach_id}_desc"), True, MUTED)
            screen.blit(title_s, (rect.x + 50, rect.y + 7))
            screen.blit(desc_s, (rect.x + 50, rect.y + 32))
        screen.set_clip(old_clip)

        track = self.ACH_TRACK_RECT
        pygame.draw.rect(screen, PANEL, track, border_radius=8)
        pygame.draw.rect(screen, EDGE, track, 1, border_radius=8)
        pygame.draw.rect(screen, MINT, thumb, border_radius=8)
        hint = self.font_small.render(t('ACH_SCROLL_HINT'), True, MUTED)
        screen.blit(hint, hint.get_rect(midleft=(70, 661)))
        back = self.font_small.render(t("ESC_RETURN_HINT"), True, MUTED)
        screen.blit(back, back.get_rect(midright=(1210, 693)))

    # ================================================================
    # ГЛАВНОЕ МЕНЮ
    # ================================================================
    def draw_main_menu(self, screen, selected_option, selected_hero_index=0):
        screen.fill(INK)
        key = HERO_KEYS[selected_hero_index]
        hero = HEROES[key]
        accent = self.theme_accent
        # Scrolling lanes and little packets of light behind the stationary UI.
        seconds = pygame.time.get_ticks() / 1000
        drift = int(seconds * 18) % 68
        for lane in range(-7, SCREEN_WIDTH // 68 + 1):
            x = lane * 68 + drift
            pygame.draw.line(screen, _mix(INK, self.theme_accent, .10), (x, SCREEN_HEIGHT), (x+350, 0), 1)
            phase = seconds * 0.24 + lane * 0.618
            progress = phase % 1
            head = (int(x + progress * 350), int((1-progress) * SCREEN_HEIGHT))
            # Fade packets in/out across the loop boundary instead of making
            # their upward streaks pop out abruptly at the top of the lane.
            fade = min(1.0, progress * 6.0, (1.0-progress) * 6.0)
            streak = _mix(INK, self.theme_accent, .58 * fade)
            pygame.draw.line(screen, streak, head, (head[0]-13, head[1]+27), 2)
        screen.blit(self.mono.render('SS  /  ' + t('LOBBY'), True, MINT), (70, 40))
        guide_button = bestiary_rect()
        pygame.draw.rect(screen, PANEL, guide_button, border_radius=7)
        pygame.draw.rect(screen, MINT, guide_button, 1, border_radius=7)
        guide_label = self.body.render(t('GUIDE_BUTTON'), True, MINT)
        screen.blit(guide_label, guide_label.get_rect(center=guide_button.center))
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
        # Animated hero content must stay clear of the arrow buttons
        # (703-755 and 1116-1168): the old rect overlapped them by 6px, so
        # sliding snapshots carried arrow slivers along with the hero.
        content_rect = pygame.Rect(card.x+104, 260, card.w-208, 220)
        hero_before = screen.subsurface(content_rect).copy()
        now = pygame.time.get_ticks()
        if getattr(self, '_lobby_hero', selected_hero_index) != selected_hero_index:
            delta = (selected_hero_index - self._lobby_hero) % len(HERO_KEYS)
            self._hero_direction = 1 if delta == 1 else -1
            self._hero_started = now
            previous_card = getattr(self, '_hero_card', None)
            self._hero_old = previous_card.copy() if previous_card is not None else None
        self._lobby_hero = selected_hero_index
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
        current = screen.subsurface(content_rect).copy()
        progress = min(1, (now-getattr(self, '_hero_started', -1000))/260)
        if progress < 1 and self.setting("hero_animations"):
            screen.blit(hero_before, content_rect)
            eased = 1-(1-progress)**3
            old = getattr(self, '_hero_old', None)
            direction = getattr(self, '_hero_direction', 1)
            clip = screen.get_clip()
            screen.set_clip(content_rect)
            if old is not None:
                old_frame = old.copy()
                old_frame.set_alpha(round(255*(1-eased)))
                screen.blit(old_frame, (content_rect.x-round(direction*90*eased), content_rect.y))
            current_frame = current.copy()
            current_frame.set_alpha(round(255*eased))
            screen.blit(current_frame, (content_rect.x+round(direction*90*(1-eased)), content_rect.y))
            screen.set_clip(clip)
        current.set_alpha(255)
        self._hero_card = current.copy()
        # Arrows are drawn last so the hero transition can never move them.
        for step in (-1, 1):
            button = hero_arrow_rect(step)
            hot = button.collidepoint(getattr(self, "mouse_pos", pygame.mouse.get_pos)())
            pygame.draw.rect(screen, INK, button, border_radius=8)
            pygame.draw.rect(screen, accent if hot else EDGE, button, 2, border_radius=8)
            ax, ay = button.center
            pygame.draw.lines(screen, accent if hot else PAPER, False,
                              [(ax-step*4, ay-9), (ax+step*5, ay), (ax-step*4, ay+9)], 3)
        pygame.draw.line(screen, EDGE, (70, 646), (1210, 646))
        screen.blit(self.body.render(t('MENU_HINT'), True, MUTED), (70, 661))

    # ================================================================
    # РЕКОРДЫ
    # ================================================================
    def draw_highscores_screen(self, screen):
        screen.fill(INK)

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
        screen.fill(INK)

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
