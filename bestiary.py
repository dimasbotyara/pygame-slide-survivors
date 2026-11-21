"""Offline field guide: enemies, temporary/permanent upgrades, hero abilities.

Each tab has its own filter button (right of the tabs), cycled on click / F.
All numbers come from the same objects used in a run.
"""
import math
import random
import pygame

from camera import Camera
from consumables import TONICS, TONIC_IDS
from enemies import Enemy, Boss
from heroes import HEROES, HERO_KEYS
from settings import (ENEMY_TYPES, BOSS_SPAWN_INTERVAL, EXPLOSION_FUSE,
                      GREEN, PURPLE, RED, CYAN)
from typography import TextFont
from upgrades import create_all_upgrades
from wildlife import RESIDENTS
from translations import t
from ui import INK, PANEL, EDGE, MUTED, MINT, PAPER, NUMBER_KEYS, word_lines, bestiary_rect as guide_rect

ENTRY_KEYS = tuple(ENEMY_TYPES) + tuple(RESIDENTS) + ('boss',)
PAGE_SIZE = 9
FILTERS = ('all', 'regular', 'resident', 'boss')
TABS = ('enemies', 'temporary', 'permanent', 'abilities', 'hero_upgrades')

PICKUP_KEYS = ('heal', 'magnet', 'bomb', 'speed_boost')
PICKUP_COLORS = {'heal': GREEN, 'magnet': PURPLE, 'bomb': RED, 'speed_boost': CYAN}
TEMPORARY_KEYS = tuple(TONIC_IDS) + PICKUP_KEYS

_ALL_UPGRADES = create_all_upgrades()
UPGRADE_MAP = {u.upgrade_id: u for u in _ALL_UPGRADES}
PERMANENT_KEYS = tuple(u.upgrade_id for u in _ALL_UPGRADES if u.category != 'hero')
HERO_UPGRADE_KEYS = tuple(u.upgrade_id for u in _ALL_UPGRADES if u.category == 'hero')
ABILITY_KEYS = tuple(HERO_KEYS)
TAB_FILTERS = {
    'enemies': FILTERS,
    'temporary': ('all', 'tonics', 'pickups'),
    'permanent': ('all', 'basic', 'fist', 'slide', 'utility'),
    'abilities': ('all',) + tuple(HERO_KEYS),
    'hero_upgrades': ('all',) + tuple(HERO_KEYS),
}


_CATEGORY_LABELS = {'fist': 'CAT_COMBAT', 'hero': 'CAT_HERO', 'slide': 'CAT_SLIDE',
                    'utility': 'CAT_SPECIAL', 'basic': 'CAT_BASIC'}
_TAB_NOTES = {'enemies': 'GUIDE_BASE_NOTE', 'temporary': 'GUIDE_TEMPORARY_NOTE',
              'permanent': 'GUIDE_PERMANENT_NOTE', 'abilities': 'GUIDE_ABILITIES_NOTE',
              'hero_upgrades': 'GUIDE_HERO_UPGRADES_NOTE'}


def category(key):
    return 'boss' if key == 'boss' else 'resident' if key in RESIDENTS else 'regular'


def back_rect():
    return pygame.Rect(1050, 29, 160, 38)


def tab_rect(index):
    # Five tabs share 70..974; the filter button owns 982..1210 on the same row.
    width = (904 - 4 * 8) // len(TABS)
    return pygame.Rect(70 + index * (width + 8), 103, width, 46)


def filter_button_rect():
    return pygame.Rect(982, 103, 228, 46)


def filter_rect(index=0):
    """Backward-compatible alias: the filter is now one separate button."""
    return filter_button_rect()


def row_rect(index):
    return pygame.Rect(70, 175 + index * 48, 314, 43)


def page_rect(step):
    return pygame.Rect(70 if step < 0 else 338, 617, 46, 29)


def name(key):
    return t('MOB_' + key)


def base_enemy(key):
    # Opening the guide must never advance the run's random stream.
    state = random.getstate()
    try:
        return Boss(96, 96) if key == 'boss' else Enemy(96, 96, key)
    finally:
        random.setstate(state)


def facts(key, enemy):
    """All numerical combat values come from the same objects used in a run."""
    e = enemy
    rows = [t('GUIDE_VITALS', f'{e.max_hp:g}', f'{e.base_speed:g}', e.xp_reward),
            t('GUIDE_DAMAGE', t('GUIDE_PROJECTILE') if e.shoot_range else t('GUIDE_MELEE'),
              f'{e.damage:g}', f'{e.windup_duration:g}'),
            t('GUIDE_RANGE', f'{e.shoot_range or e.strike_radius:g}', f'{e.attack_cooldown:g}')]
    if e.shoot_range:
        rows.append(t('GUIDE_SHOTS', len(e.shot_offsets), f'{e.shoot_speed:g}'))
    if e.home_biome:
        rows.append(t('GUIDE_HOME', t('BIOME_' + e.home_biome)))
    elif key == 'boss':
        rows.append(t('GUIDE_BOSS_TIME', BOSS_SPAWN_INTERVAL))
        rows.append(t('GUIDE_ANY_BIOME'))
    else:
        rows.append(t('GUIDE_SPAWN', ENEMY_TYPES[key]['min_time']))
        rows.append(t('GUIDE_ANY_BIOME'))
    if e.sprint_speed:
        rows.append(t('GUIDE_SPRINT', f'{e.sprint_speed:g}', f'{e.sprint_duration_max:g}', f'{e.sprint_cooldown_max:g}'))
    if e.revive_radius:
        rows.append(t('GUIDE_REVIVE', f'{e.revive_radius:g}', f'{e.revive_cooldown_max:g}'))
    if e.explode_radius:
        rows.append(t('GUIDE_EXPLOSION', f'{e.explode_damage:g}', f'{e.explode_radius:g}', f'{EXPLOSION_FUSE:g}'))
    if e.knockback_resist:
        rows.append(t('GUIDE_RESIST', f'{e.knockback_resist * 100:g}'))
    return rows


class Bestiary:
    def __init__(self):
        self.tab = 0
        self.filter = 0
        self.cursor = 0
        self._enemies = {}
        self._icons = {}
        self._tab_icons = {}
        self.camera = Camera(192, 192)
        self.camera.entity_shadows = True

    # -- entries ---------------------------------------------------------
    @property
    def entries(self):
        tab = TABS[self.tab]
        selected = TAB_FILTERS[tab][self.filter % len(TAB_FILTERS[tab])]
        keys = {'enemies': ENTRY_KEYS, 'temporary': TEMPORARY_KEYS,
                'permanent': PERMANENT_KEYS, 'abilities': ABILITY_KEYS,
                'hero_upgrades': HERO_UPGRADE_KEYS}[tab]
        if selected == 'all':
            return list(keys)
        if tab == 'enemies':
            return [key for key in keys if category(key) == selected]
        if tab == 'temporary':
            return [key for key in keys if (key in TONICS) == (selected == 'tonics')]
        if tab == 'permanent':
            return [key for key in keys if UPGRADE_MAP[key].category == selected]
        if tab == 'abilities':
            return [key for key in keys if key == selected]
        return [key for key in keys if UPGRADE_MAP[key].hero_id == selected]

    @property
    def key(self):
        return self.entries[self.cursor]

    def enemy(self, key):
        if key not in self._enemies:
            self._enemies[key] = base_enemy(key)
        return self._enemies[key]

    def image(self, key, seconds=0, warning=False):
        e = self.enemy(key)
        e.anim_timer = seconds
        e.windup_left = e.windup_duration * (1 - (seconds * .7) % 1) if warning else 0
        image = pygame.Surface((192, 192), pygame.SRCALPHA)
        e.draw_windup(image, self.camera)
        e.draw(image, self.camera)
        return image

    def icon(self, key):
        if key not in self._icons:
            image = self.image(key)
            bounds = image.get_bounding_rect().inflate(8, 8).clip(image.get_rect())
            self._icons[key] = pygame.transform.smoothscale(image.subsurface(bounds), (40, 40))
        return self._icons[key]

    # -- per-tab display data --------------------------------------------
    def entry_name(self, key):
        tab = TABS[self.tab]
        if tab == 'enemies':
            return name(key)
        if tab == 'temporary':
            if key in TONICS:
                tonic = TONICS[key]
                full = t('TONIC_' + key, tonic.bonus, tonic.seconds)
                return full.split(':')[0].strip()
            return t('GUIDE_PICKUP_' + key + '_name')
        if tab in ('permanent', 'hero_upgrades'):
            return UPGRADE_MAP[key].name
        hero = HEROES[key]
        return f"{t('hero_' + key + '_name')} — {t(hero['ult_id'] + '_name')}"

    def entry_subtitle(self, key):
        tab = TABS[self.tab]
        if tab == 'enemies':
            return t('GUIDE_FILTER_' + category(key))
        if tab == 'temporary':
            if key in TONICS:
                return t('GUIDE_TEMP_DURATION', TONICS[key].seconds)
            return t('GUIDE_PICKUP_SOURCE')
        if tab == 'permanent':
            return t(_CATEGORY_LABELS[UPGRADE_MAP[key].category])
        if tab == 'abilities':
            return t('hero_' + key + '_sub')
        return t('hero_' + UPGRADE_MAP[key].hero_id + '_name')

    def entry_description(self, key):
        tab = TABS[self.tab]
        if tab == 'enemies':
            e = self.enemy(key)
            return t('GUIDE_BEHAVIOR_' + ('boss' if key == 'boss' else e.archetype))
        if tab == 'temporary':
            if key in TONICS:
                tonic = TONICS[key]
                return t('TONIC_' + key, tonic.bonus, tonic.seconds)
            return t('GUIDE_PICKUP_' + key + '_desc')
        if tab in ('permanent', 'hero_upgrades'):
            return UPGRADE_MAP[key].description
        return t(HEROES[key]['ult_id'] + '_desc')

    def entry_facts(self, key):
        tab = TABS[self.tab]
        if tab == 'enemies':
            return facts(key, self.enemy(key))
        if tab == 'temporary':
            if key in TONICS:
                tonic = TONICS[key]
                stat = t('GUIDE_STAT_' + tonic.stat)
                return [t('GUIDE_TEMP_EFFECT', stat, tonic.bonus),
                        t('GUIDE_TEMP_DURATION', tonic.seconds)]
            return [t('GUIDE_PICKUP_SOURCE')]
        if tab in ('permanent', 'hero_upgrades'):
            u = UPGRADE_MAP[key]
            cap = t('GUIDE_UPGRADE_MAX_LEVEL', u.max_level) if u.max_level else t('GUIDE_UPGRADE_UNLIMITED')
            return [t('GUIDE_UPGRADE_VALUE', f'{u.value:g}'), cap]
        h = HEROES[key]
        return [f"{t('HERO_HP')}: {h['base_hp']}",
                f"{t('HERO_SPEED')}: {h['base_speed']}",
                t('GUIDE_HERO_SLIDE_CHARGES', h['slide_charges']),
                t('GUIDE_HERO_CRIT', h['crit_chance'], h['crit_mult']),
                t('GUIDE_HERO_LIFESTEAL', h['lifesteal']),
                t('GUIDE_HERO_FIST_MULT', f"{h['fist_damage_mult'] * 100:g}"),
                t('GUIDE_HERO_SLIDE_MODS', f"{h['slide_speed_mult']:g}", f"{h['slide_cooldown_mult']:g}")]

    def entry_color(self, key):
        tab = TABS[self.tab]
        if tab == 'enemies':
            return getattr(self.enemy(key), 'color', MINT)
        if tab == 'temporary':
            return TONICS[key].color if key in TONICS else PICKUP_COLORS[key]
        if tab in ('permanent', 'hero_upgrades'):
            return UPGRADE_MAP[key].icon_color
        return HEROES[key]['color']

    def _mark(self, surface, key, center, scale):
        """Draw font-independent high-contrast marks for guide entries."""
        tab = TABS[self.tab]
        cx, cy = center
        if tab == 'temporary':
            if key in TONICS:
                stat = TONICS[key].stat
                abbreviations = {
                    'armor': 'AR', 'damage': 'DM', 'attack_speed': 'AS',
                    'crit_chance': 'CR', 'attack_range': 'RG',
                    'fist_lifesteal': 'LS', 'xp_multiplier': 'XP',
                    'xp_radius': 'XR', 'slide_turn_speed': 'TR',
                    'slide_speed': 'SS', 'fist_stun_chance': 'ST',
                    'slide_damage': 'SD',
                }
                label = abbreviations.get(stat, '?')
            else:
                label = {'heal': '+', 'magnet': 'M', 'bomb': 'B', 'speed_boost': 'S'}[key]
            font = TextFont('body', max(10, int(scale * 0.72)))
            glyph = font.render(label, True, PAPER)
            surface.blit(glyph, glyph.get_rect(center=center))
        elif tab == 'hero_upgrades':
            r = scale * 0.62
            points = []
            for i in range(10):
                angle = -1.5708 + i * math.pi / 5
                radius = r if i % 2 == 0 else r * 0.44
                points.append((int(cx + radius * math.cos(angle)),
                               int(cy + radius * math.sin(angle))))
            pygame.draw.polygon(surface, PAPER, points)
        elif tab == 'abilities':
            r = scale * 0.67
            pygame.draw.polygon(surface, PAPER, [
                (int(cx + r * .15), int(cy - r)),
                (int(cx - r * .48), int(cy + r * .03)),
                (int(cx - r * .05), int(cy + r * .03)),
                (int(cx - r * .25), int(cy + r)),
                (int(cx + r * .52), int(cy - r * .1)),
                (int(cx + r * .12), int(cy - r * .1)),
            ])
        else:
            r = scale * 0.6
            pygame.draw.polygon(surface, PAPER, [
                (int(cx - r * .18), int(cy + r)),
                (int(cx - r * .18), int(cy - r * .12)),
                (int(cx - r * .65), int(cy - r * .12)),
                (int(cx), int(cy - r)),
                (int(cx + r * .65), int(cy - r * .12)),
                (int(cx + r * .18), int(cy - r * .12)),
                (int(cx + r * .18), int(cy + r)),
            ])

    def entry_icon(self, key):
        """40x40 list icon for the current tab (enemies reuse the live sprite)."""
        if TABS[self.tab] == 'enemies':
            return self.icon(key)
        cache_key = (TABS[self.tab], key)
        if cache_key not in self._tab_icons:
            color = self.entry_color(key)
            surface = pygame.Surface((40, 40), pygame.SRCALPHA)
            # Coloured ring + dark disc: the glyph stays readable for every
            # accent colour (a same-colour glyph on a same-colour disc is not).
            pygame.draw.circle(surface, color, (20, 20), 16)
            pygame.draw.circle(surface, (27, 29, 44), (20, 20), 12)
            self._mark(surface, key, (20, 20), 18)
            self._tab_icons[cache_key] = surface
        return self._tab_icons[cache_key]

    def entry_preview(self, key, seconds=0, warning=False):
        """192x192 detail preview for the current tab."""
        if TABS[self.tab] == 'enemies':
            return self.image(key, seconds, warning)
        color = self.entry_color(key)
        surface = pygame.Surface((192, 192), pygame.SRCALPHA)
        cx, cy = 96, 96
        pygame.draw.circle(surface, EDGE, (cx, cy), 60, 1)
        for j in range(4):
            ang = seconds * 0.6 + j * 3.14159 / 2
            pygame.draw.arc(surface, color, (cx - 61, cy - 61, 122, 122), ang, ang + 0.38, 3)
        pygame.draw.circle(surface, color, (cx, cy), 36)
        pygame.draw.circle(surface, INK, (cx, cy), 36, 2)
        self._mark(surface, key, (cx, cy), 40)
        return surface

    # -- navigation --------------------------------------------------------
    def move(self, amount):
        self.cursor = max(0, min(len(self.entries) - 1, self.cursor + amount))

    def filter_label(self):
        key = TAB_FILTERS[TABS[self.tab]][self.filter]
        if key in HERO_KEYS:
            return t('hero_' + key + '_name')
        if key in _CATEGORY_LABELS:
            return t(_CATEGORY_LABELS[key])
        return t('GUIDE_FILTER_' + key)

    def cycle_filter(self):
        self.filter = (self.filter + 1) % len(TAB_FILTERS[TABS[self.tab]])
        self.cursor = 0

    def handle(self, events):
        """Return True when the reader requests the lobby; never start a run."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    return True
                if key in NUMBER_KEYS and NUMBER_KEYS[key] < len(TABS):
                    self.tab, self.cursor, self.filter = NUMBER_KEYS[key], 0, 0
                elif key == pygame.K_f:
                    self.cycle_filter()
                elif key in (pygame.K_UP, pygame.K_w):
                    self.move(-1)
                elif key in (pygame.K_DOWN, pygame.K_s):
                    self.move(1)
                elif key in (pygame.K_LEFT, pygame.K_PAGEUP):
                    self.move(-PAGE_SIZE)
                elif key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                    self.move(PAGE_SIZE)
                elif key == pygame.K_HOME:
                    self.cursor = 0
                elif key == pygame.K_END:
                    self.cursor = len(self.entries) - 1
                elif key == pygame.K_TAB:
                    step = -1 if getattr(event, 'mod', 0) & pygame.KMOD_SHIFT else 1
                    self.tab, self.cursor, self.filter = (self.tab + step) % len(TABS), 0, 0
            elif event.type == pygame.MOUSEWHEEL:
                self.move(-event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5):
                    self.move(-1 if event.button == 4 else 1)
                elif event.button == 1:
                    if back_rect().collidepoint(event.pos):
                        return True
                    for i in range(len(TABS)):
                        if tab_rect(i).collidepoint(event.pos):
                            self.tab, self.cursor, self.filter = i, 0, 0
                            break
                    if filter_button_rect().collidepoint(event.pos):
                        self.cycle_filter()
                    start = self.cursor // PAGE_SIZE * PAGE_SIZE
                    for i in range(min(PAGE_SIZE, len(self.entries) - start)):
                        if row_rect(i).collidepoint(event.pos):
                            self.cursor = start + i
                            break
                    for step in (-1, 1):
                        if page_rect(step).collidepoint(event.pos):
                            self.move(step * PAGE_SIZE)
        return False

    def draw(self, screen, ui):
        screen.fill(INK)
        screen.blit(ui.font_medium.render(t('GUIDE_TITLE'), True, PAPER), (70, 29))
        pygame.draw.line(screen, EDGE, (70, 77), (1210, 77))
        pygame.draw.rect(screen, PANEL, back_rect(), border_radius=6)
        text = ui.body.render(t('GUIDE_BACK'), True, MINT)
        screen.blit(text, text.get_rect(center=back_rect().center))
        # Tabs (1-5 / Tab) replace the old filter row.
        for i, tab in enumerate(TABS):
            rect = tab_rect(i)
            selected = i == self.tab
            pygame.draw.rect(screen, MINT if selected else PANEL, rect, border_radius=6)
            if not selected:
                pygame.draw.rect(screen, EDGE, rect, 1, border_radius=6)
            number = ui.mono.render(f'{i + 1:02}', True, INK if selected else MUTED)
            screen.blit(number, number.get_rect(midleft=(rect.left + 10, rect.centery)))
            label = ui.fitted_text(t('GUIDE_TAB_' + tab), INK if selected else PAPER, rect.w - 52, 22, 16)
            screen.blit(label, label.get_rect(midleft=(rect.left + 42, rect.centery)))
        # Filter for the current tab.
        rect = filter_button_rect()
        pygame.draw.rect(screen, PANEL, rect, border_radius=6)
        pygame.draw.rect(screen, MINT, rect, 1, border_radius=6)
        label = ui.fitted_text(t('GUIDE_FILTER_BUTTON', self.filter_label()),
                               MINT, rect.w - 20, 22, 16)
        screen.blit(label, label.get_rect(center=rect.center))
        entries = self.entries
        start = self.cursor // PAGE_SIZE * PAGE_SIZE
        for i, key in enumerate(entries[start:start + PAGE_SIZE]):
            rect = row_rect(i)
            selected = start + i == self.cursor
            pygame.draw.rect(screen, PANEL, rect, border_radius=6)
            pygame.draw.rect(screen, MINT if selected else EDGE, rect, 1, border_radius=6)
            screen.blit(self.entry_icon(key), (rect.x + 4, rect.y + 1))
            label = ui.fitted_text(self.entry_name(key), PAPER if selected else MUTED, 253, 24, 18)
            screen.blit(label, label.get_rect(midleft=(rect.x + 50, rect.centery)))
        for step in (-1, 1):
            rect = page_rect(step)
            pygame.draw.rect(screen, PANEL, rect, border_radius=5)
            text = ui.body.render('‹' if step < 0 else '›', True, MINT)
            screen.blit(text, text.get_rect(center=rect.center))
        page = ui.mono.render(f'{self.cursor + 1:02} / {len(entries):02}', True, MUTED)
        screen.blit(page, page.get_rect(center=(227, 632)))

        key = self.key
        tab = TABS[self.tab]
        panel = pygame.Rect(410, 175, 800, 471)
        pygame.draw.rect(screen, PANEL, panel, border_radius=10)
        pygame.draw.rect(screen, EDGE, panel, 1, border_radius=10)
        title = ui.fitted_text(self.entry_name(key), PAPER, 746, 30, 24)
        screen.blit(title, (436, 193))
        subtitle = ui.fitted_text(self.entry_subtitle(key), MINT, 746, 20, 14)
        screen.blit(subtitle, (438, 234))
        preview = pygame.Rect(438, 269, 192, 192)
        pygame.draw.rect(screen, INK, preview, border_radius=9)
        seconds = pygame.time.get_ticks() / 1000 if ui.setting('menu_animations') else .5
        image = self.entry_preview(key, seconds, warning=True)
        if tab == 'enemies':
            e = self.enemy(key)
            extent = min(90, max(e.size + 18, e.strike_radius if not e.shoot_range else e.size + 5))
            crop = pygame.Rect(96 - extent, 96 - extent, extent * 2, extent * 2)
            screen.blit(pygame.transform.scale(image.subsurface(crop), preview.size), preview)
        else:
            screen.blit(pygame.transform.scale(image, preview.size), preview)
        for i, line in enumerate(self.entry_facts(key)):
            highlight = (i == 1) if tab == 'enemies' else (i == 0)
            text = ui.fitted_text(line, PAPER if highlight else MUTED, 532, 22, 18)
            screen.blit(text, (650, 273 + i * 26))
        description = self.entry_description(key)
        for i, line in enumerate(word_lines(ui.body, description, 746)):
            screen.blit(ui.body.render(line, True, PAPER), (438, 484 + i * 24))
        if tab == 'enemies' and self.enemy(key).home_biome:
            for i, line in enumerate(word_lines(ui.font_small, t('GUIDE_NATIVE_RULE'), 746)):
                screen.blit(ui.font_small.render(line, True, MINT), (438, 593 + i * 21))
        note = ui.font_small.render(t(_TAB_NOTES[tab]), True, MUTED)
        screen.blit(note, (70, 658))
        hint = ui.mono.render(t('GUIDE_HINT'), True, MUTED)
        screen.blit(hint, (70, 690))
