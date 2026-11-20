"""Offline UI typefaces. SDL_ttf does not automatically fall back for icons."""
import re
from functools import lru_cache
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent / 'assets' / 'fonts'
FACES = {
    'body': 'golostext/GolosText[wght].ttf',
    'display': 'russoone/RussoOne-Regular.ttf',
    'label': 'exo2/Exo2[wght].ttf',
    'mono': 'jetbrainsmono/JetBrainsMono[wght].ttf',
    'poster': 'rubikmonoone/RubikMonoOne-Regular.ttf',
    'emoji': 'notoemoji/NotoEmoji[wght].ttf',
    'symbol': 'notosanssymbols2/NotoSansSymbols2-Regular.ttf',
}
# Keep adjacent regional indicators in one run so the flag ligature is shaped.
ICONS = re.compile(r'(?P<emoji>[⚔⚠⚡⭐♥\U0001f000-\U0001faff\ufe0f\u200d]+)|(?P<symbol>[►✦]+)|(?P<mono>[←↑→↓−]+)')


@lru_cache(maxsize=64)
def face(role, size):
    return pygame.font.Font(str(ROOT / FACES[role]), size)


class TextFont:
    def __init__(self, role, size):
        self.base = face(role, size)
        self.px = size

    def runs(self, text):
        start = 0
        for token in ICONS.finditer(text):
            if token.start() > start:
                yield self.base, text[start:token.start()]
            yield face(token.lastgroup, self.px), token.group()
            start = token.end()
        if start < len(text):
            yield self.base, text[start:]

    def size(self, text):
        return sum(font.size(run)[0] for font, run in self.runs(text)), self.base.get_height()

    def render(self, text, antialias, color):
        if not ICONS.search(text):
            return self.base.render(text, antialias, color)
        spans = [(f, f.render(run, antialias, color)) for f, run in self.runs(text)]
        ascent = max(f.get_ascent() for f, _ in spans)
        height = max(ascent - f.get_ascent() + s.get_height() for f, s in spans)
        out = pygame.Surface((sum(s.get_width() for _, s in spans), height), pygame.SRCALPHA)
        x = 0
        for f, span in spans:
            out.blit(span, (x, ascent - f.get_ascent()))
            x += span.get_width()
        return out
