"""Small reusable world-space effects used by hero ultimate abilities."""
import math
import random
from functools import lru_cache

import pygame


@lru_cache(maxsize=96)
def corpse_sprite(size, color):
    """Create a tiny readable ragdoll silhouette, cached by size and tint."""
    w, h = size * 3, size * 2
    image = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    body = pygame.Rect(cx-size, cy-size//2, size*2, size)
    pygame.draw.ellipse(image, color, body)
    pygame.draw.ellipse(image, (235, 230, 215), body, max(1, size//8))
    pygame.draw.circle(image, color, (cx+size, cy-size//3), max(3, size//2))
    pygame.draw.circle(image, (235, 230, 215), (cx+size, cy-size//3), max(3, size//2), 1)
    pygame.draw.line(image, color, (cx-size//2, cy+size//3), (cx-size, cy+size), max(2, size//4))
    pygame.draw.line(image, color, (cx+size//2, cy+size//3), (cx+size, cy+size), max(2, size//4))
    return image


class CorpseProjectile:
    """A launched enemy remnant that can ricochet through several enemies."""
    def __init__(self, x, y, vx, vy, color, size, damage, ttl=1.35, max_hits=3):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.color = tuple(color[:3])
        self.size = max(8, int(size))
        self.damage = float(damage)
        self.ttl = self.max_ttl = ttl
        self.angle = math.atan2(vy, vx)
        self.spin = 8.0 if vx * vy >= 0 else -8.0
        self.hit_targets = set()
        self.hits_left = max_hits
        self.alive = True

    @property
    def radius(self):
        return self.size * .72

    def update(self, dt):
        if not self.alive:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt
        damping = max(0.0, 1.0 - .38 * dt)
        self.vx *= damping
        self.vy *= damping
        self.ttl -= dt
        if self.ttl <= 0 or self.hits_left <= 0:
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive:
            return
        sx, sy = camera.apply(self.x, self.y)
        p = self.ttl / self.max_ttl
        tail = (int(sx-self.vx*.035), int(sy-self.vy*.035))
        pygame.draw.line(screen, self.color, tail, (int(sx), int(sy)), max(1, self.size//4))
        image = pygame.transform.rotate(corpse_sprite(self.size, self.color), -math.degrees(self.angle))
        image.set_alpha(round(255 * min(1.0, p * 1.8)))
        screen.blit(image, image.get_rect(center=(round(sx), round(sy))))


def fracture_lines(x, y, seed, arms=17, radius=430):
    """Generate jagged radial fissures in world coordinates."""
    rng = random.Random(seed)
    lines = []
    for i in range(arms):
        angle = math.tau * i / arms + rng.uniform(-.11, .11)
        length = rng.uniform(radius*.52, radius)
        steps = rng.randint(4, 7)
        points = [(x, y)]
        for j in range(1, steps+1):
            angle += rng.uniform(-.22, .22)
            distance = length / steps
            px, py = points[-1]
            points.append((px + math.cos(angle)*distance, py + math.sin(angle)*distance))
        lines.extend(zip(points, points[1:]))
        if rng.random() < .72:
            bx, by = points[rng.randint(2, len(points)-2)]
            branch = angle + rng.choice((-1, 1)) * rng.uniform(.45, 1.0)
            end = (bx + math.cos(branch)*rng.uniform(55, 125),
                   by + math.sin(branch)*rng.uniform(55, 125))
            lines.append(((bx, by), end))
    return lines


def lightning_segments(start, end, seed, steps=8):
    """Return a crooked polyline between two world-space lightning anchors."""
    rng = random.Random(seed)
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2-x1, y2-y1
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy/length, dx/length
    points = [(x1, y1)]
    for i in range(1, steps):
        t = i / steps
        jitter = rng.uniform(-min(34, length*.12), min(34, length*.12))
        points.append((x1+dx*t+nx*jitter, y1+dy*t+ny*jitter))
    points.append((x2, y2))
    return list(zip(points, points[1:]))
