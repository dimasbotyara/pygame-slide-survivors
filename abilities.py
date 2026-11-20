"""World-space effects for ice slides and player-centered auras."""
import math

import pygame

from settings import (CYAN, PINK, TEAL, ICE_RADIUS, ICE_DURATION, REPULSE_RADIUS,
                      REPULSE_PERIOD, DRAIN_RADIUS, DRAIN_PERIOD, STASIS_RADIUS)


class IceTrail:
    def __init__(self):
        self.patches = []
        self.last_patch = None
        r = ICE_RADIUS
        self.sprite = pygame.Surface((2*r+1, 2*r+1), pygame.SRCALPHA)
        pygame.draw.circle(self.sprite, (88, 174, 220, 85), (r, r), r)
        pygame.draw.lines(self.sprite, (189, 239, 255, 165), False,
                          [(r-12, r+6), (r-1, r+1), (r-3, r-5), (r+9, r-9)], 2)

    def update(self, dt, player, start):
        self.patches = [(x, y, ttl-dt) for x, y, ttl in self.patches if ttl > dt]
        level = player.stats['ice_trail']
        if not level or not player.is_sliding:
            self.last_patch = None
            return
        lifetime = ICE_DURATION + level - 1
        if self.last_patch is None:
            self.last_patch = start
            self.patches.append((*start, lifetime))
        # Space patches by distance rather than one deposit per rendered frame.
        x, y = self.last_patch
        dx, dy = player.x - x, player.y - y
        distance = math.hypot(dx, dy)
        for i in range(1, int(distance / ICE_RADIUS) + 1):
            fraction = i * ICE_RADIUS / distance
            self.last_patch = x + dx*fraction, y + dy*fraction
            self.patches.append((*self.last_patch, lifetime))

    def covers(self, enemy):
        reach_sq = (ICE_RADIUS + enemy.size) ** 2
        return any((enemy.x-x)**2 + (enemy.y-y)**2 <= reach_sq for x, y, _ in self.patches)

    def draw(self, screen, camera):
        for x, y, ttl in self.patches:
            sx, sy = camera.apply(x, y)
            self.sprite.set_alpha(int(255 * min(1, ttl / 0.5)))
            screen.blit(self.sprite, (sx-ICE_RADIUS, sy-ICE_RADIUS))


class PulseAuras:
    def __init__(self):
        self.repulse_cd = self.drain_cd = 0.0
        self.drain_tip = None

    def update(self, dt, player, enemies, deal_damage):
        self.repulse_cd = max(0, self.repulse_cd - dt)
        self.drain_cd = max(0, self.drain_cd - dt)
        push = player.stats['repulse_aura'] if not self.repulse_cd else 0
        drain = player.stats['drain_aura'] if not self.drain_cd else 0
        if player.hp <= 0 or not (push or drain):
            return
        nearest, best = None, math.inf
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx, dy = enemy.x-player.x, enemy.y-player.y
            distance = math.hypot(dx, dy)
            if push and distance <= REPULSE_RADIUS + enemy.size:
                ux, uy = (dx/distance, dy/distance) if distance else (1, 0)
                force = 200 + 100 * push
                enemy.apply_knockback(ux * force, uy * force)
                self.repulse_cd = REPULSE_PERIOD
            if drain and distance <= DRAIN_RADIUS + enemy.size and distance < best:
                nearest, best = enemy, distance
        if nearest is not None:
            self.drain_cd = DRAIN_PERIOD
            self.drain_tip = nearest.x, nearest.y
            hp_before = nearest.hp
            deal_damage(nearest, 8 * drain, source='aura', can_crit=False,
                        can_lifesteal=False, can_stun=False, particle_color=PINK)
            player.heal((hp_before - nearest.hp) / 4)

    def draw(self, screen, camera, player, time):
        center = camera.apply(player.x, player.y)
        # Broken, rotating perimeters keep the solid enemy warning rings readable.
        for stat, radius, color, sign in [('repulse_aura', REPULSE_RADIUS, TEAL, 1),
                                           ('drain_aura', DRAIN_RADIUS, PINK, -1),
                                           ('stasis_aura', STASIS_RADIUS, CYAN, 1)]:
            if not player.stats[stat]:
                continue
            rect = pygame.Rect(0, 0, radius*2, radius*2)
            rect.center = center
            for i in range(6):
                angle = sign * time * 0.45 + i * math.tau / 6
                pygame.draw.arc(screen, color, rect, angle, angle + 0.22, 2)
        elapsed = REPULSE_PERIOD - self.repulse_cd
        if elapsed < 0.25:
            pygame.draw.circle(screen, TEAL, center, int(REPULSE_RADIUS * elapsed / 0.25), 2)
        if self.drain_tip and DRAIN_PERIOD - self.drain_cd < 0.18:
            pygame.draw.aaline(screen, PINK, center, camera.apply(*self.drain_tip))
