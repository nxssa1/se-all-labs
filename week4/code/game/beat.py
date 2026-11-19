import pygame

LANES = 4
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
LANE_LABELS = ['D', 'F', 'J', 'K']
LANE_COLORS = [(220, 80, 80), (80, 180, 220), (100, 220, 100), (220, 180, 60)]

# How long (in frames) a HOLD note must be held to score. 60 frames @ 60 FPS = 1 second.
HOLD_FRAMES = 60


class Note:
    WIDTH = 70
    HEIGHT = 20

    def __init__(self, lane, y=-30, speed=4, kind="tap"):
        self.lane = lane
        self.y = y
        self.speed = speed
        self.kind = kind            # "tap" or "hold"
        self.hit = False
        self.missed = False
        self.scored = False         # hold note already credited

        # Hold-note state
        if kind == "hold":
            # Visual length so the whole bar takes HOLD_FRAMES to cross the line.
            self.length = int(speed * HOLD_FRAMES)
        else:
            self.length = self.HEIGHT
        self.holding = False        # player is currently holding this note
        self.hold_started = False    # head was pressed in time

    def update(self):
        self.y += self.speed

    # Leading (bottom) edge of the note — this is what crosses the hit line first.
    def lead_edge(self):
        return self.y + self.length

    # Trailing (top) edge — for hold notes, the line the tail must reach to finish.
    def tail_edge(self):
        return self.y

    def get_rect(self, lane_x):
        return pygame.Rect(lane_x - self.WIDTH // 2, int(self.y), self.WIDTH, self.length)
