import pygame
import random
import io
import math
import struct
import wave
from game.beat import (
    Note, LANES, LANE_KEYS, LANE_LABELS, LANE_COLORS, HOLD_FRAMES
)

WIDTH, HEIGHT = 480, 640
FPS = 60
HIT_Y = HEIGHT - 80
HIT_WINDOW = 30
BG = (15, 10, 25)
LANE_W = WIDTH // LANES

# Task 3: BPM-synced spawning
BPM = 120                     # notes fall on the beat of a 120 BPM track
HOLD_EVERY = 4                # every 4th beat is a hold note


def _make_tone(freq, ms=120, volume=0.5, sample_rate=44100):
    """Synthesize a short decaying sine tone and return it as WAV bytes.
    No external assets or numpy needed."""
    n = int(sample_rate * ms / 1000)
    buf = io.BytesIO()
    w = wave.open(buf, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)          # 16-bit
    w.setframerate(sample_rate)
    frames = bytearray()
    for i in range(n):
        env = 1.0 - (i / n)                      # linear decay so it sounds like a tap
        sample = volume * env * math.sin(2 * math.pi * freq * i / sample_rate)
        frames += struct.pack("<h", int(sample * 32767))
    w.writeframes(frames)
    w.close()
    buf.seek(0)
    return buf


class GameEngine:
    def __init__(self):
        pygame.init()
        self.audio = True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        except pygame.error:
            self.audio = False

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rhythm Tap")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 26, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 20, bold=True)

        # Task 1: sound effects, generated once at startup
        self.sounds = {}
        if self.audio:
            try:
                self.sounds = {
                    "PERFECT": pygame.mixer.Sound(file=_make_tone(880)),
                    "GREAT":   pygame.mixer.Sound(file=_make_tone(660)),
                    "OK":      pygame.mixer.Sound(file=_make_tone(440)),
                    "HOLD":    pygame.mixer.Sound(file=_make_tone(990, ms=160)),
                }
                for s in self.sounds.values():
                    s.set_volume(0.6)
            except pygame.error:
                self.audio = False

        self.reset()

    def reset(self):
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0
        self.speed = 5
        self.frame = 0
        self.beat = 0
        self.bpm = BPM
        self.frames_per_beat = int(round(FPS * 60 / self.bpm))  # 30 frames @ 120 BPM
        self.feedback = []  # [text, color, ttl, x, y]
        self.game_over = False
        self.key_down = [False] * LANES

        # Task 4: per-grade tally for the summary screen
        self.counts = {"PERFECT": 0, "GREAT": 0, "OK": 0, "MISS": 0}

    # ---------- sound ----------
    def play(self, name):
        if self.audio and name in self.sounds:
            self.sounds[name].play()

    # ---------- spawning (Task 3: BPM-synced) ----------
    def spawn_on_beat(self):
        lane = random.randint(0, LANES - 1)
        kind = "hold" if (self.beat % HOLD_EVERY == 0) else "tap"
        self.notes.append(Note(lane, y=-30, speed=self.speed, kind=kind))
        self.beat += 1

    # ---------- input ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif not self.game_over:
                    for i, key in enumerate(LANE_KEYS):
                        if event.key == key:
                            self.key_down[i] = True
                            self.process_tap(i)
            if event.type == pygame.KEYUP:
                for i, key in enumerate(LANE_KEYS):
                    if event.key == key:
                        self.key_down[i] = False
                        self.release_hold(i)
        return True

    def process_tap(self, lane):
        # Find closest unresolved note in this lane near the hit zone.
        best = None
        best_dist = 9999
        for note in self.notes:
            if note.lane == lane and not note.hit and not note.missed and not note.hold_started:
                # tap notes judge on their centre; hold notes judge on the leading edge
                if note.kind == "hold":
                    ref = note.lead_edge()
                else:
                    ref = note.y + Note.HEIGHT // 2
                dist = abs(ref - HIT_Y)
                if dist < best_dist:
                    best_dist = dist
                    best = note
        lane_x = lane * LANE_W + LANE_W // 2

        if best and best_dist <= HIT_WINDOW:
            if best.kind == "hold":
                # Task 2: begin holding; it is scored only once the tail crosses the line.
                best.hold_started = True
                best.holding = True
                self.feedback.append(["HOLD…", (180, 180, 255), 40, lane_x, HIT_Y - 30])
                self.play("HOLD")
            else:
                best.hit = True
                if best_dist < 8:
                    grade, pts, col = "PERFECT", 300, (255, 220, 0)
                elif best_dist < 18:
                    grade, pts, col = "GREAT", 200, (100, 220, 100)
                else:
                    grade, pts, col = "OK", 100, (180, 180, 255)
                self.register_hit(grade, pts, col, lane_x)
        else:
            self.register_miss(lane_x)

    def release_hold(self, lane):
        # Releasing a hold before the tail reaches the line breaks it.
        for note in self.notes:
            if (note.lane == lane and note.kind == "hold"
                    and note.holding and not note.scored and not note.missed):
                note.holding = False
                note.missed = True
                lane_x = lane * LANE_W + LANE_W // 2
                self.register_miss(lane_x, text="BROKE")

    def register_hit(self, grade, pts, col, lane_x):
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.score += pts * max(1, self.combo // 5)
        self.counts[grade] = self.counts.get(grade, 0) + 1
        self.feedback.append([grade, col, 40, lane_x, HIT_Y - 30])
        self.play(grade)

    def register_miss(self, lane_x, text="MISS"):
        self.combo = 0
        self.misses += 1
        self.counts["MISS"] += 1
        self.feedback.append([text, (220, 60, 60), 40, lane_x, HIT_Y - 30])

    # ---------- update ----------
    def update(self):
        if self.game_over:
            return
        self.frame += 1

        # Task 3: spawn exactly on the beat instead of on an arbitrary timer.
        if self.frame % self.frames_per_beat == 0:
            self.spawn_on_beat()

        # --- BUG FIX ---
        # The original ramp was nested inside the spawn branch and gated on
        # `frame % 600 == 0`, which never coincided with a spawn frame, so the
        # game never sped up. It now runs every 8 beats, independent of spawning.
        if self.frame % (self.frames_per_beat * 8) == 0:
            self.speed = min(10, self.speed + 0.5)

        for note in self.notes:
            note.update()

            if note.kind == "hold":
                # Completed hold: tail (top edge) has reached the line while held.
                if note.hold_started and note.holding and not note.scored \
                        and note.tail_edge() >= HIT_Y:
                    note.scored = True
                    note.hit = True
                    lane_x = note.lane * LANE_W + LANE_W // 2
                    self.register_hit("PERFECT", 300, (255, 220, 0), lane_x)
                # Hold whose head passed the window without ever being pressed.
                elif not note.hold_started and not note.missed \
                        and note.lead_edge() > HIT_Y + HIT_WINDOW + Note.HEIGHT:
                    note.missed = True
                    lane_x = note.lane * LANE_W + LANE_W // 2
                    self.register_miss(lane_x)
            else:
                if not note.hit and not note.missed \
                        and note.y > HIT_Y + HIT_WINDOW + Note.HEIGHT:
                    note.missed = True
                    lane_x = note.lane * LANE_W + LANE_W // 2
                    self.register_miss(lane_x)

        # Keep notes until they are resolved and off-screen.
        self.notes = [n for n in self.notes
                      if not (n.hit or (n.missed and n.y > HEIGHT + 10))]
        self.feedback = [[t, c, ttl - 1, x, y]
                         for t, c, ttl, x, y in self.feedback if ttl > 1]

        if self.misses >= 15:
            self.game_over = True

    # ---------- draw ----------
    def draw(self):
        self.screen.fill(BG)
        for i in range(LANES + 1):
            pygame.draw.line(self.screen, (40, 40, 60), (i * LANE_W, 0), (i * LANE_W, HEIGHT), 1)

        pygame.draw.line(self.screen, (80, 80, 100), (0, HIT_Y), (WIDTH, HIT_Y), 2)
        for i in range(LANES):
            lx = i * LANE_W + LANE_W // 2
            glow = (255, 255, 255) if self.key_down[i] else LANE_COLORS[i]
            pygame.draw.rect(self.screen, glow,
                pygame.Rect(lx - Note.WIDTH // 2, HIT_Y - 12, Note.WIDTH, 24), border_radius=6)
            lbl = self.font.render(LANE_LABELS[i], True, (20, 20, 20))
            self.screen.blit(lbl, (lx - lbl.get_width() // 2, HIT_Y - 10))

        for note in self.notes:
            if note.hit or self.game_over:
                continue
            lx = note.lane * LANE_W + LANE_W // 2
            rect = note.get_rect(lx)
            col = LANE_COLORS[note.lane]
            if note.kind == "hold":
                # brighten a hold while it is being held correctly
                col = (255, 255, 255) if note.holding else tuple(min(255, c + 30) for c in col)
                pygame.draw.rect(self.screen, col, rect, border_radius=8)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, width=2, border_radius=8)
            else:
                pygame.draw.rect(self.screen, col, rect, border_radius=5)

        for text, color, ttl, x, y in self.feedback:
            surf = self.font.render(text, True, color)
            surf.set_alpha(min(255, ttl * 7))
            self.screen.blit(surf, (x - surf.get_width() // 2, y))

        sc = self.font.render(f"Score: {self.score}", True, (220, 220, 220))
        co = self.font.render(f"Combo: {self.combo}x", True, (255, 220, 80))
        mi = self.font.render(f"Misses: {self.misses}/15", True, (220, 100, 100))
        self.screen.blit(sc, (10, 10))
        self.screen.blit(co, (10, 40))
        self.screen.blit(mi, (WIDTH - 170, 10))

        if self.game_over:
            self.draw_summary()
        pygame.display.flip()

    # Task 4: grade summary screen
    def draw_summary(self):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))

        title = self.big_font.render("GAME OVER", True, (220, 60, 60))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))

        rows = [
            ("PERFECT", self.counts["PERFECT"], (255, 220, 0)),
            ("GREAT",   self.counts["GREAT"],   (100, 220, 100)),
            ("OK",      self.counts["OK"],      (180, 180, 255)),
            ("MISS",    self.counts["MISS"],    (220, 60, 60)),
        ]
        y = 170
        for label, count, col in rows:
            lbl = self.small_font.render(label, True, col)
            val = self.small_font.render(str(count), True, (230, 230, 230))
            self.screen.blit(lbl, (110, y))
            self.screen.blit(val, (WIDTH - 140, y))
            y += 40

        hits = self.counts["PERFECT"] + self.counts["GREAT"] + self.counts["OK"]
        total = hits + self.counts["MISS"]
        acc = (hits / total * 100) if total else 0.0

        y += 10
        acc_txt = self.font.render(f"Accuracy: {acc:.1f}%", True, (255, 255, 255))
        self.screen.blit(acc_txt, (WIDTH // 2 - acc_txt.get_width() // 2, y))
        y += 40
        sc_txt = self.font.render(f"Score: {self.score}", True, (210, 210, 210))
        self.screen.blit(sc_txt, (WIDTH // 2 - sc_txt.get_width() // 2, y))
        y += 32
        mc_txt = self.small_font.render(f"Max Combo: {self.max_combo}x", True, (255, 220, 80))
        self.screen.blit(mc_txt, (WIDTH // 2 - mc_txt.get_width() // 2, y))

        restart = self.small_font.render("Press R to Restart", True, (160, 160, 160))
        self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT - 60))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
