"""
Walt's spoken voice. Every line he says is turned into speech with the Mac's built-in text-to-speech
(the `say` command, "Grandpa" voice), saved once as a small WAV file in data/voice/ and then played.

- Nothing is installed: `say` comes with macOS. On other computers there is no voice, only the
  speech bubbles, and the game works the same.
- The files are made in a background thread while the game starts, so the window never waits.
  A line that is not ready yet is simply shown as a bubble without sound.
- data/ is not in git, so the voice files are never committed; they can always be made again.
"""
import hashlib
import shutil
import subprocess
import threading
from pathlib import Path

import pygame

VOICE = "Grandpa (English (US))"     # an old man's voice, fits an old park mechanic
RATE = 165                           # words per minute (a bit slower than normal, he is old and tired)
GHOST_RATE = 120                     # in the finale he speaks slower and lower
CACHE = Path("data/voice")


def file_for(text, ghost=False):
    """Each line gets its own file, named after a short fingerprint of the text."""
    key = hashlib.md5((text + ("|ghost" if ghost else "")).encode("utf-8")).hexdigest()[:12]
    return CACHE / f"walt_{key}.wav"


def make_line(text, ghost=False):
    """Create the WAV file for one line with macOS `say` (skipped if it already exists)."""
    path = file_for(text, ghost)
    if path.exists():
        return path
    CACHE.mkdir(parents=True, exist_ok=True)
    rate = GHOST_RATE if ghost else RATE
    command = ["say", "-v", VOICE, "-r", str(rate), "--file-format=WAVE", "--data-format=LEI16@22050",
               "-o", str(path), text]
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    return path


class WaltVoice:
    """Prepares all of Walt's lines in the background and plays them on request."""

    def __init__(self, lines, ghost_lines, enabled=True):
        self.ready = {}                  # (text, ghost) -> pygame Sound
        self.channel = None
        self.enabled = enabled and shutil.which("say") is not None and pygame.mixer.get_init() is not None
        if self.enabled:
            jobs = [(t, False) for t in lines] + [(t, True) for t in ghost_lines]
            threading.Thread(target=self.prepare, args=(jobs,), daemon=True).start()

    def prepare(self, jobs):
        for text, ghost in jobs:
            try:
                path = make_line(text, ghost)
                self.ready[(text, ghost)] = pygame.mixer.Sound(str(path))
            except (subprocess.SubprocessError, OSError, pygame.error):
                continue                 # one line failing is fine: it stays a silent bubble

    def speak(self, text, ghost=False, muted=False):
        """Say a line (if its file is ready and sound is on). A new line interrupts the previous one."""
        sound = self.ready.get((text, ghost))
        if sound is None or muted or not self.enabled:
            return
        if self.channel is not None:
            self.channel.stop()
        self.channel = sound.play()
