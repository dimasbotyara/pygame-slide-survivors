"""Resizable physical window with a fixed logical canvas and mapped input."""
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class DisplayManager:
    def __init__(self, settings):
        self.settings = settings
        self.window = None
        self.viewport = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.apply()

    def apply(self):
        size = tuple(self.settings.get('resolution'))
        if size == (0, 0):
            desktops = pygame.display.get_desktop_sizes()
            size = desktops[0] if desktops else (1280, 720)
        fullscreen = self.settings.get('fullscreen')
        try:
            self.window = pygame.display.set_mode(size, pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE)
            self.error = False
        except pygame.error:
            # Unsupported modes must not leave the player with an unusable window.
            self.settings.settings.update(fullscreen=False, resolution=(1280, 720))
            self.window = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
            self.settings.save()
            self.error = True
        self.scaled_frame = None
        self.update_viewport()

    def update_viewport(self):
        w, h = self.window.get_size()
        scale = min(w / SCREEN_WIDTH, h / SCREEN_HEIGHT)
        size = max(1, round(SCREEN_WIDTH * scale)), max(1, round(SCREEN_HEIGHT * scale))
        self.viewport = pygame.Rect((w-size[0])//2, (h-size[1])//2, *size)

    def logical_pos(self, pos):
        self.update_viewport()
        return (round((pos[0]-self.viewport.x)*SCREEN_WIDTH/self.viewport.w),
                round((pos[1]-self.viewport.y)*SCREEN_HEIGHT/self.viewport.h))

    def mouse_pos(self):
        return self.logical_pos(pygame.mouse.get_pos())

    def events(self, events):
        mapped = []
        for event in events:
            if event.type == pygame.VIDEORESIZE and not self.settings.get('fullscreen'):
                size = max(640, min(7680, event.w)), max(360, min(4320, event.h))
                self.settings.settings['resolution'] = size
                self.apply()
                self.settings.save()
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and getattr(event, 'mod', 0) & pygame.KMOD_ALT:
                self.settings.set('fullscreen', not self.settings.get('fullscreen'))
                self.apply()
                continue
            if hasattr(event, 'pos'):
                attrs = event.dict.copy()
                attrs['pos'] = self.logical_pos(event.pos)
                if 'rel' in attrs:
                    attrs['rel'] = (event.rel[0]*SCREEN_WIDTH/self.viewport.w,
                                    event.rel[1]*SCREEN_HEIGHT/self.viewport.h)
                event = pygame.event.Event(event.type, attrs)
            mapped.append(event)
        return mapped

    def present(self, canvas):
        self.update_viewport()
        if self.viewport.size != self.window.get_size():
            self.window.fill((5, 8, 13))
        if canvas.get_size() == self.viewport.size:
            image = canvas
        else:
            transform = pygame.transform.smoothscale if self.settings.get('smooth_scaling') else pygame.transform.scale
            if self.scaled_frame is None or self.scaled_frame.get_size() != self.viewport.size:
                self.scaled_frame = pygame.Surface(self.viewport.size).convert()
            image = transform(canvas, self.viewport.size, self.scaled_frame)
        self.window.blit(image, self.viewport)
        pygame.display.flip()
