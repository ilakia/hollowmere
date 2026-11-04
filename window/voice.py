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

VOICE = "Grandpa (English (US))"     # default: an old man's voice, fits an old park mechanic
# voices the player can choose on the title screen (name shown, macOS voice name)
VOICE_OPTIONS = [("Grandpa", "Grandpa (English (US))"), ("Grandpa UK", "Grandpa (English (UK))"),
                 ("Fred", "Fred"), ("Ralph", "Ralph"), ("Rocko", "Rocko (English (US))"),
                 ("Reed", "Reed (English (US))"), ("Daniel", "Daniel")]
RATE = 165                           # words per minute (a bit slower than normal, he is old and tired)
GHOST_RATE = 120                     # in the finale he speaks slower and lower
CACHE = Path("data/voice")


def file_for(text, ghost=False, voice=VOICE):
    """Each line (per voice) gets its own file, named after a short fingerprint of the text."""
    key = hashlib.md5((voice + "|" + text + ("|ghost" if ghost else "")).encode("utf-8")).hexdigest()[:12]
    return CACHE / f"walt_{key}.wav"


def make_line(text, ghost=False, voice=VOICE):
    """Create the WAV file for one line with macOS `say` (skipped if it already exists)."""
    path = file_for(text, ghost, voice)
    if path.exists():
        return path
    CACHE.mkdir(parents=True, exist_ok=True)
    rate = GHOST_RATE if ghost else RATE
    command = ["say", "-v", voice, "-r", str(rate), "--file-format=WAVE", "--data-format=LEI16@22050",
               "-o", str(path), text]
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    return path


class WaltVoice:
    """Prepares all of Walt's lines in the background and plays them on request."""

    def __init__(self, lines, ghost_lines, enabled=True, voice=VOICE):
        self.ready = {}                  # (text, ghost) -> pygame Sound
        self.channel = None
        self.wanted = None               # the line Walt should be saying right now
        self.preview_process = None
        self.voice = voice
        self.generation = 0              # goes up when the voice changes, so old background work is ignored
        self.jobs = [(t, False) for t in lines] + [(t, True) for t in ghost_lines]
        self.enabled = enabled and shutil.which("say") is not None and pygame.mixer.get_init() is not None
        if self.enabled:
            self.start_preparing()

    def start_preparing(self):
        threading.Thread(target=self.prepare, args=(self.voice, self.generation), daemon=True).start()

    def prepare(self, voice, generation):
        for text, ghost in self.jobs:
            if generation != self.generation:
                return                   # the player chose another voice meanwhile
            try:
                path = make_line(text, ghost, voice)
                sound = pygame.mixer.Sound(str(path))
            except (subprocess.SubprocessError, OSError, pygame.error):
                continue                 # one line failing is fine: it stays a silent bubble
            if generation == self.generation:
                self.ready[(text, ghost)] = sound

    def set_voice(self, voice):
        """Switch Walt's voice: forget the old sounds and prepare the lines in the new voice."""
        if voice == self.voice or not self.enabled:
            self.voice = voice
            return
        self.voice = voice
        self.generation += 1
        self.ready = {}
        self.start_preparing()

    def preview(self, voice, text):
        """Let the player hear a voice straight away (macOS speaks it directly, nothing is saved)."""
        if not self.enabled:
            return
        if self.preview_process is not None and self.preview_process.poll() is None:
            self.preview_process.terminate()
        self.preview_process = subprocess.Popen(["say", "-v", voice, "-r", str(RATE), text])

    def is_speaking(self):
        """True while Walt is still saying his current line (scenes wait for it before moving on)."""
        return self.channel is not None and self.channel.get_busy()

    def stop(self):
        """Stop the current line (the player skipped the scene with Space)."""
        if self.channel is not None:
            self.channel.stop()

    def speak(self, text, ghost=False, muted=False):
        """Say a line (if sound is on). A new line interrupts the previous one. A line that was not
        prepared at the start (e.g. a sentence LLM Walt just made up) is made now in the background
        and played as soon as it is ready (about a second), unless Walt has moved on to another line."""
        self.wanted = (text, ghost)
        if muted or not self.enabled or not text:
            return
        sound = self.ready.get((text, ghost))
        if sound is None:
            threading.Thread(target=self.make_and_play, args=(text, ghost, self.voice), daemon=True).start()
            return
        if self.channel is not None:
            self.channel.stop()
        self.channel = sound.play()

    def make_and_play(self, text, ghost, voice):
        """Background thread for a new line: make the WAV, then play it if it is still wanted."""
        try:
            path = make_line(text, ghost, voice)
            sound = pygame.mixer.Sound(str(path))
        except (subprocess.SubprocessError, OSError, pygame.error):
            return
        self.ready[(text, ghost)] = sound
        if self.wanted == (text, ghost) and voice == self.voice:
            if self.channel is not None:
                self.channel.stop()
            self.channel = sound.play()
