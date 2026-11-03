"""
Sound effects and music, generated as sound waves in code (numpy), so there are no audio files
and no licence questions. If the computer has no sound device, everything stays silent and the
game still runs.

How a sound is made: a tone is a sine wave (numbers going up and down FREQUENCY times per second);
"decay" makes it fade out; noise is random numbers (good for hits). The numbers are scaled to
16-bit integers and handed to pygame.
"""
import numpy as np
import pygame

RATE = 22050                     # samples per second (enough for simple game sounds, small to compute)


def tone(freq, seconds, volume=0.4, slide_to=None, decay=6.0, wave="sine"):
    """A tone that fades out. slide_to = end frequency (rising or falling pitch)."""
    t = np.linspace(0, seconds, int(RATE * seconds), endpoint=False)
    end = freq if slide_to is None else slide_to
    freqs = np.linspace(freq, end, t.size)
    phase = 2 * np.pi * np.cumsum(freqs) / RATE
    if wave == "square":
        signal = np.sign(np.sin(phase))
    else:
        signal = np.sin(phase)
    return signal * np.exp(-decay * t) * volume


def noise(seconds, volume=0.4, decay=12.0, seed=0):
    t = np.linspace(0, seconds, int(RATE * seconds), endpoint=False)
    return np.random.default_rng(seed).uniform(-1, 1, t.size) * np.exp(-decay * t) * volume


def join(*parts):
    return np.concatenate(parts)


def make_music():
    """A slow music-box melody in A minor over a low hum, about 10 seconds, played in a loop."""
    a_minor = [220.0, 261.6, 329.6, 440.0, 392.0, 329.6, 293.7, 261.6,
               220.0, 246.9, 261.6, 329.6, 293.7, 246.9, 207.7, 220.0]
    note_seconds = 0.6
    melody = join(*[tone(f * 2, note_seconds, 0.12, decay=4.0) + tone(f * 4, note_seconds, 0.03, decay=7.0)
                    for f in a_minor])
    t = np.linspace(0, melody.size / RATE, melody.size, endpoint=False)
    hum = 0.05 * np.sin(2 * np.pi * 55 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * t))
    echo = np.zeros_like(melody)
    delay = int(RATE * 0.3)
    echo[delay:] = melody[:-delay] * 0.35                        # a simple echo makes it sound like a big empty park
    return melody + echo + hum


def build_sounds():
    """All game sounds as wave arrays. Output: dict name -> numpy array."""
    return {
        "click": tone(880, 0.06, 0.2, decay=40),
        "hit": join(noise(0.06, 0.5, decay=40, seed=1), tone(180, 0.12, 0.35, slide_to=90, decay=20)),
        "miss": noise(0.18, 0.18, decay=14, seed=2),
        "hurt": tone(140, 0.25, 0.5, slide_to=60, decay=10, wave="square") * 0.6,
        "block": join(tone(600, 0.05, 0.3, decay=30), tone(300, 0.1, 0.25, decay=25)),
        "charge": tone(200, 0.6, 0.25, slide_to=700, decay=1.5),
        "heal": join(tone(523, 0.12, 0.25, decay=8), tone(659, 0.12, 0.25, decay=8), tone(784, 0.3, 0.25, decay=6)),
        "potion": join(*[tone(300 + 120 * i, 0.07, 0.2, decay=20) for i in range(5)]),
        "defeat": join(tone(500, 0.12, 0.3, slide_to=250, decay=10), noise(0.25, 0.25, decay=10, seed=3)),
        "death": tone(220, 1.2, 0.4, slide_to=55, decay=2.5),
        "win": join(*[tone(f, 0.18, 0.25, decay=6) for f in (392, 494, 587, 784)]),
    }


class SoundBank:
    """Plays the sounds. enabled=False (or no sound device) -> every call does nothing."""

    def __init__(self, enabled=True):
        self.sounds = {}
        self.music = None
        self.muted = not enabled
        if not enabled:
            return
        try:
            pygame.mixer.init(frequency=RATE, size=-16, channels=1)
            channels = pygame.mixer.get_init()[2]
            for name, wave in build_sounds().items():
                self.sounds[name] = self.to_sound(wave, channels)
            self.music = self.to_sound(make_music(), channels)
        except (pygame.error, NotImplementedError):      # no sound device: play silently
            self.sounds = {}
            self.music = None

    def to_sound(self, wave, channels):
        samples = np.int16(np.clip(wave, -1, 1) * 32000)
        if channels == 2:
            samples = np.column_stack([samples, samples])   # same sound on left and right
        return pygame.sndarray.make_sound(samples.copy(order="C"))

    def play(self, name):
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

    def start_music(self):
        if not self.muted and self.music is not None:
            self.music.play(loops=-1)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.music is None:
            return
        if self.muted:
            pygame.mixer.stop()
        else:
            self.music.play(loops=-1)
