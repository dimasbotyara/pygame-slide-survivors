"""Offline field guide: real enemy renderers and live base combat attributes."""
import random
import pygame

from camera import Camera
from enemies import Enemy, Boss
from settings import ENEMY_TYPES, BOSS_SPAWN_INTERVAL, EXPLOSION_FUSE
from wildlife import RESIDENTS
from translations import t
from ui import INK, PANEL, EDGE, MUTED, MINT, PAPER, NUMBER_KEYS, word_lines, bestiary_rect as guide_rect

ENTRY_KEYS = tuple(ENEMY_TYPES) + tuple(RESIDENTS) + ('boss',)
PAGE_SIZE = 9
FILTERS = ('all', 'regular', 'resident', 'boss')


def category(key):
    return 'boss' if key == 'boss' else 'resident' if key in RESIDENTS else 'regular'


def back_rect():
    return pygame.Rect(1050, 29, 160, 38)


def filter_rect(index):
    return pygame.Rect(70+index*287, 103, 279, 46)


def row_rect(index):
    return pygame.Rect(70, 175+index*48, 314, 43)


def page_rect(step):
    return pygame.Rect(70 if step < 0 else 338, 617, 46, 29)


def name(key):
    return t('MOB_'+key)


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
        rows.append(t('GUIDE_HOME', t('BIOME_'+e.home_biome)))
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
        rows.append(t('GUIDE_RESIST', f'{e.knockback_resist*100:g}'))
    return rows


class Bestiary:
    def __init__(self):
        self.filter = 0
        self.cursor = 0
        self._enemies = {}
        self._icons = {}
        self.camera = Camera(192, 192)
        self.camera.entity_shadows = True

    @property
    def entries(self):
        selected = FILTERS[self.filter]
        return [key for key in ENTRY_KEYS if selected == 'all' or category(key) == selected]

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
        e.windup_left = e.windup_duration*(1-(seconds*.7)%1) if warning else 0
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

    def move(self, amount):
        self.cursor = max(0, min(len(self.entries)-1, self.cursor+amount))

    def handle(self, events):
        """Return True when the reader requests the lobby; never start a run."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_ESCAPE:
                    return True
                if key in NUMBER_KEYS and NUMBER_KEYS[key] < len(FILTERS):
                    self.filter, self.cursor = NUMBER_KEYS[key], 0
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
                    self.cursor = len(self.entries)-1
                elif key == pygame.K_TAB:
                    step = -1 if getattr(event, 'mod', 0) & pygame.KMOD_SHIFT else 1
                    self.filter, self.cursor = (self.filter+step)%len(FILTERS), 0
            elif event.type == pygame.MOUSEWHEEL:
                self.move(-event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5):
                    self.move(-1 if event.button == 4 else 1)
                elif event.button == 1:
                    if back_rect().collidepoint(event.pos):
                        return True
                    for i in range(len(FILTERS)):
                        if filter_rect(i).collidepoint(event.pos):
                            self.filter, self.cursor = i, 0
                            break
                    start = self.cursor//PAGE_SIZE*PAGE_SIZE
                    for i in range(min(PAGE_SIZE, len(self.entries)-start)):
                        if row_rect(i).collidepoint(event.pos):
                            self.cursor = start+i
                            break
                    for step in (-1, 1):
                        if page_rect(step).collidepoint(event.pos):
                            self.move(step*PAGE_SIZE)
        return False

    def draw(self, screen, ui):
        screen.fill(INK)
        screen.blit(ui.font_medium.render(t('GUIDE_TITLE'), True, PAPER), (70, 29))
        pygame.draw.line(screen, EDGE, (70, 77), (1210, 77))
        pygame.draw.rect(screen, PANEL, back_rect(), border_radius=6)
        text = ui.body.render(t('GUIDE_BACK'), True, MINT)
        screen.blit(text, text.get_rect(center=back_rect().center))
        for i, group in enumerate(FILTERS):
            ui.button(screen, filter_rect(i), t('GUIDE_FILTER_'+group), i, self.filter == i)
        entries = self.entries
        start = self.cursor//PAGE_SIZE*PAGE_SIZE
        for i, key in enumerate(entries[start:start+PAGE_SIZE]):
            rect = row_rect(i)
            selected = start+i == self.cursor
            pygame.draw.rect(screen, PANEL, rect, border_radius=6)
            pygame.draw.rect(screen, MINT if selected else EDGE, rect, 1, border_radius=6)
            screen.blit(self.icon(key), (rect.x+4, rect.y+1))
            label = ui.fitted_text(name(key), PAPER if selected else MUTED, 253, 24, 18)
            screen.blit(label, label.get_rect(midleft=(rect.x+50, rect.centery)))
        for step in (-1, 1):
            rect = page_rect(step)
            pygame.draw.rect(screen, PANEL, rect, border_radius=5)
            text = ui.body.render('‹' if step < 0 else '›', True, MINT)
            screen.blit(text, text.get_rect(center=rect.center))
        page = ui.mono.render(f'{self.cursor+1:02} / {len(entries):02}', True, MUTED)
        screen.blit(page, page.get_rect(center=(227, 632)))

        key = self.key
        e = self.enemy(key)
        panel = pygame.Rect(410, 175, 800, 471)
        pygame.draw.rect(screen, PANEL, panel, border_radius=10)
        pygame.draw.rect(screen, EDGE, panel, 1, border_radius=10)
        screen.blit(ui.font_medium.render(name(key), True, PAPER), (436, 193))
        screen.blit(ui.mono.render(t('GUIDE_FILTER_'+category(key)), True, MINT), (438, 234))
        preview = pygame.Rect(438, 269, 192, 192)
        pygame.draw.rect(screen, INK, preview, border_radius=9)
        seconds = pygame.time.get_ticks()/1000 if ui.setting('menu_animations') else .5
        image = self.image(key, seconds, warning=True)
        extent = min(90, max(e.size+18, e.strike_radius if not e.shoot_range else e.size+5))
        crop = pygame.Rect(96-extent, 96-extent, extent*2, extent*2)
        screen.blit(pygame.transform.scale(image.subsurface(crop), preview.size), preview)
        for i, line in enumerate(facts(key, e)):
            text = ui.fitted_text(line, PAPER if i == 1 else MUTED, 532, 22, 18)
            screen.blit(text, (650, 273+i*26))
        description = t('GUIDE_BEHAVIOR_'+('boss' if key == 'boss' else e.archetype))
        for i, line in enumerate(word_lines(ui.body, description, 746)):
            screen.blit(ui.body.render(line, True, PAPER), (438, 484+i*24))
        if e.home_biome:
            for i, line in enumerate(word_lines(ui.font_small, t('GUIDE_NATIVE_RULE'), 746)):
                screen.blit(ui.font_small.render(line, True, MINT), (438, 593+i*21))
        note = ui.font_small.render(t('GUIDE_BASE_NOTE'), True, MUTED)
        screen.blit(note, (70, 658))
        hint = ui.mono.render(t('GUIDE_HINT'), True, MUTED)
        screen.blit(hint, (70, 690))
