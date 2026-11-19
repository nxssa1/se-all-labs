# Rhythm Tap — Fixed + Extended

A 4-lane rhythm game. Tap the right key as notes reach the hit line.

## Setup
```
pip install -r requirements.txt
python main.py
```
(Windows: just double-click `PLAY_AFTER.bat`.)

## Controls
| Key | Lane    |
| --- | ------- |
| D   | Lane 1  |
| F   | Lane 2  |
| J   | Lane 3  |
| K   | Lane 4  |
| R   | Restart |

Hold notes (tall bars) must be **held** for 1 second — press as the head
reaches the line and keep the key down until the tail crosses it.

---

## Bug that was fixed
In the original `game/game_engine.py`, the difficulty ramp lived **inside**
the note-spawn branch and was gated on `self.frame % 600 == 0`:

```python
if self.spawn_timer >= self.spawn_interval:
    self.spawn_note()
    self.spawn_timer = 0
    if self.frame % 600 == 0:                 # <-- only checked on a spawn frame
        self.speed = min(10, self.speed + 0.5)
        self.spawn_interval = max(25, self.spawn_interval - 2)
```

Notes spawn on multiples of the spawn interval (45, 90, 135, …), which never
coincide with a multiple of 600, so the `if` never ran. **The game never sped
up** no matter how long you played (speed and spawn interval stayed at their
starting values forever).

**Fix:** the ramp now runs independently of spawning, keyed to the musical
beat, so difficulty increases reliably:

```python
if self.frame % (self.frames_per_beat * 8) == 0:
    self.speed = min(10, self.speed + 0.5)
```

The *before* video shows SPEED stuck at 5.0; the *after* video shows it
climbing to 6.0.

---

## Tasks implemented

**Task 1 — Sound effects on hit.** Short decaying tones are synthesised at
startup (no external assets or numpy) and played on each hit: PERFECT 880 Hz,
GREAT 660 Hz, OK 440 Hz, and a distinct tone when a hold starts. Audio failure
(e.g. no output device) is caught so the game still runs silently.

**Task 2 — Hold notes.** A new `kind="hold"` note renders as a tall bar. The
player presses as the head reaches the line and must keep the key down for a
full second (`HOLD_FRAMES = 60`); it is scored only when the tail crosses the
line. Releasing early breaks the hold and counts as a miss.

**Task 3 — BPM-synced spawning.** Notes spawn on exact beats of a 120 BPM
track (`frames_per_beat = FPS * 60 / BPM = 30` frames) instead of an arbitrary
timer. Every 4th beat is a hold note.

**Task 4 — Grade summary screen.** On game over the screen shows a breakdown of
PERFECT / GREAT / OK / MISS counts, accuracy %, final score and max combo.

## Files
```
main.py
requirements.txt
game/__init__.py
game/beat.py          # Note + hold-note model
game/game_engine.py   # engine: input, scoring, spawning, draw, summary
```
