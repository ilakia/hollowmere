"""
Visual effects for the game window. Each effect is started by an event (a hit, a death, a heal)
and then fades out by itself over time, so the drawing code only has to call draw() every frame.
"""
import math
import random
import time

import pygame

from .art import HEIGHT, WIDTH


class Particles:
    """Small dots that fly out and fade: sparks on hits, bursts when a ghost dies, heal sparkles."""

    def __init__(self):
        self.items = []     # each: [x, y, speed x, speed y, born, lifetime, colour, size, gravity]

    def burst(self, x, y, color, count=20, speed=160, lifetime=0.8, size=4, gravity=200):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            v = random.uniform(0.3, 1.0) * speed
            self.items.append([x, y, math.cos(angle) * v, math.sin(angle) * v - 60,
                               time.time(), lifetime * random.uniform(0.6, 1.0), color, size, gravity])

    def rise(self, x, y, color, count=14):
        """Sparkles drifting upwards (healing)."""
        for _ in range(count):
            self.items.append([x + random.uniform(-25, 25), y + random.uniform(-10, 30), random.uniform(-15, 15),
                               random.uniform(-90, -40), time.time(), random.uniform(0.7, 1.2), color, 3, 0])

    def draw(self, surface, dt):
        now = time.time()
        alive = []
        for p in self.items:
            age = now - p[4]
            if age > p[5]:
                continue
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += p[8] * dt                                    # gravity pulls sparks down
            fade = 1 - age / p[5]
            size = max(1, int(p[7] * fade + 0.5))
            pygame.draw.rect(surface, p[6], (int(p[0]), int(p[1]), size, size))
            alive.append(p)
        self.items = alive


class Shake:
    """Screen shake: the whole picture is drawn slightly moved for a short time."""

    def __init__(self):
        self.until = 0.0
        self.strength = 0

    def start(self, strength=8, seconds=0.3):
        self.strength = strength
        self.until = time.time() + seconds

    def offset(self):
        if time.time() > self.until:
            return (0, 0)
        return (random.randint(-self.strength, self.strength), random.randint(-self.strength, self.strength))


class Flashes:
    """Remembers until when something should flash or move (e.g. 'ghost 0 hit', 'player lunge')."""

    def __init__(self):
        self.until = {}

    def start(self, name, seconds):
        self.until[name] = time.time() + seconds

    def progress(self, name, seconds):
        """0 at the start, 1 at the end, None when not active (for animations like the lunge)."""
        end = self.until.get(name, 0)
        left = end - time.time()
        if left <= 0:
            return None
        return 1 - left / seconds

    def active(self, name):
        return time.time() < self.until.get(name, 0)


class Fog:
    """Slow drifting fog banks along the ground (transparent ellipses)."""

    def __init__(self, count=7):
        rng = random.Random(3)
        self.banks = [[rng.uniform(-200, WIDTH), rng.uniform(395, 470), rng.uniform(220, 380),
                       rng.uniform(8, 22), rng.randint(8, 16)] for _ in range(count)]
        self.layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def draw(self, surface, dt):
        self.layer.fill((0, 0, 0, 0))
        for bank in self.banks:
            bank[0] += bank[3] * dt
            if bank[0] > WIDTH + 50:
                bank[0] = -bank[2] - 50
            x, y, width, _, alpha = bank
            pygame.draw.ellipse(self.layer, (190, 180, 220, alpha), (int(x), int(y), int(width), 46))
        surface.blit(self.layer, (0, 0))


def vignette():
    """Dark edges around the picture, drawn once and laid over every frame (spooky look)."""
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(40):
        alpha = int(80 * (1 - i / 40) ** 2)
        pygame.draw.rect(layer, (0, 0, 0, alpha), (i * 3, i * 3, WIDTH - i * 6, HEIGHT - i * 6), width=3)
    return layer
