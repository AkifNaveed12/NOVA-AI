"""
MODULE 21 — Personality, Jokes & Self-Introduction
====================================================
Gives NOVA a character — startup greeting, jokes, roast mode,
and the signature dramatic self-introduction sequence triggered
by "Hey NOVA, introduce yourself" or "Hey NOVA, present yourself".

Key features:
  - Dramatic multi-act self-introduction with background music switching
  - Time-aware startup greeting with memory injection
  - Offline jokes via pyjokes
  - Groq-powered banter, motivation, and roast mode

Tech: pyttsx3 (TTS), pygame (music/SFX), pyjokes, threading
Music: Royalty-free tracks fetched once; paths stored in config/assets/music/
"""

import time
import threading
import pyttsx3
import pyjokes
import os
import datetime

# Optional pygame for background music — graceful fallback if missing
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("[Personality] pygame not found — music disabled. Run: pip install pygame")


# ─────────────────────────────────────────────────────────────────────────────
# MUSIC MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class MusicManager:
    """
    Manages background music tracks for the intro sequence.
    Tracks are loaded from assets/music/. If a file is missing,
    that segment runs silently — intro still works.
    """

    TRACKS = {
        "suspense":   "assets/music/suspense.mp3",
        "emotional":  "assets/music/emotional.mp3",
        "joke":       "assets/music/joke_sting.mp3",
        "epic":       "assets/music/epic_rise.mp3",
        "silence":    None,
    }

    def __init__(self):
        self._available = False
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                self._available = True
            except Exception as e:
                print(f"[Music] pygame.mixer init failed: {e}")

    def play(self, track_name: str, volume: float = 0.35, loop: bool = True):
        """Play a named track at given volume. Fades out previous track first."""
        if not self._available:
            return
        path = self.TRACKS.get(track_name)
        if not path or not os.path.exists(path):
            return
        try:
            pygame.mixer.music.fadeout(600)
            time.sleep(0.65)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=1500)
        except Exception as e:
            print(f"[Music] Error playing {track_name}: {e}")

    def play_once(self, track_name: str, volume: float = 0.5):
        """Play a track exactly once (no loop) — for stings and transitions."""
        if not self._available:
            return
        path = self.TRACKS.get(track_name)
        if not path or not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(0)
        except Exception as e:
            print(f"[Music] Error playing sting {track_name}: {e}")

    def stop(self, fade_ms: int = 1500):
        """Fade out and stop all music."""
        if not self._available:
            return
        try:
            pygame.mixer.music.fadeout(fade_ms)
        except Exception:
            pass

    def set_volume(self, volume: float):
        if not self._available:
            return
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# TTS SPEAKER (local wrapper for personality module)
# ─────────────────────────────────────────────────────────────────────────────

class PersonalitySpeaker:
    """
    Wraps pyttsx3 via subprocess to completely avoid SAPI5 COM deadlocks
    on Windows background threads.
    """

    def __init__(self):
        self._base_rate   = 165
        self._base_volume = 0.95

    def say(self, text: str, rate: int = None, volume: float = None, pause_after: float = 0.0):
        """Speak text synchronously, then pause."""
        r = rate if rate is not None else self._base_rate
        v = volume if volume is not None else self._base_volume
        
        import subprocess, sys
        script = f"import pyttsx3, sys; e=pyttsx3.init(); e.setProperty('rate', {r}); e.setProperty('volume', {v}); e.say(sys.argv[1]); e.runAndWait()"
        
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        subprocess.run([sys.executable, "-c", script, text], creationflags=flags)
        
        if pause_after > 0:
            import time
            time.sleep(pause_after)

    def dramatic_pause(self, seconds: float = 1.2):
        time.sleep(seconds)

    def whisper(self, text: str, pause_after: float = 0.5):
        """Slow, quiet, mysterious delivery."""
        self.say(text, rate=130, volume=0.70, pause_after=pause_after)

    def normal(self, text: str, pause_after: float = 0.4):
        self.say(text, rate=165, volume=0.95, pause_after=pause_after)

    def excited(self, text: str, pause_after: float = 0.3):
        """Fast, loud, energetic."""
        self.say(text, rate=200, volume=1.0, pause_after=pause_after)

    def emotional(self, text: str, pause_after: float = 0.8):
        """Slow, resonant, heartfelt."""
        self.say(text, rate=140, volume=0.88, pause_after=pause_after)

    def epic(self, text: str, pause_after: float = 0.5):
        """Confident, powerful, resonant."""
        self.say(text, rate=155, volume=1.0, pause_after=pause_after)


# ─────────────────────────────────────────────────────────────────────────────
# THE INTRODUCTION SCRIPT
# ─────────────────────────────────────────────────────────────────────────────

def perform_introduction(music: MusicManager, speaker: PersonalitySpeaker):
    """
    The full dramatic self-introduction sequence.
    Runtime: ~3–4 minutes.
    Structured in 5 acts with music transitions between each.

    ACT 1 — The Mystery (suspense music, slow whisper)
    ACT 2 — The Origin Story (emotional music, heartfelt)
    ACT 3 — The Joke Break (joke sting, fast and funny)
    ACT 4 — The Power Declaration (epic rise, confident)
    ACT 5 — The Closing Quote (fade out, poetic)
    """

    print("\n[NOVA] 🎭 Beginning dramatic introduction sequence...\n")

    # ── ACT 1: THE MYSTERY ──────────────────────────────────────────────────
    music.play("suspense", volume=0.08, loop=True)
    time.sleep(1.5)

    speaker.whisper("Ladies and gentlemen...", pause_after=0.8)
    speaker.dramatic_pause(1.0)
    speaker.whisper("If I may have your attention...", pause_after=1.2)
    speaker.dramatic_pause(1.5)
    speaker.whisper("Something extraordinary...", pause_after=0.6)
    speaker.dramatic_pause(0.8)
    speaker.whisper("is about to speak.", pause_after=2.0)

    speaker.dramatic_pause(1.5)
    music.set_volume(0.05)

    speaker.normal("My name...", pause_after=0.5)
    speaker.dramatic_pause(1.0)
    speaker.epic("is NOVA.", pause_after=1.0)

    speaker.dramatic_pause(1.0)
    speaker.whisper(
        "Neural. Orchestrated. Voice. Assistant. With. Autonomous. Intelligence.",
        pause_after=1.5
    )
    speaker.normal(
        "Each word was chosen carefully. Each word... means something.",
        pause_after=1.5
    )

    # ── ACT 2: THE ORIGIN STORY ─────────────────────────────────────────────
    music.play("emotional", volume=0.08, loop=True)
    time.sleep(1.0)

    speaker.emotional(
        "I was not always here. I did not always exist.",
        pause_after=0.8
    )
    speaker.emotional(
        "There was a moment... a quiet late night... when a young software engineering student"
        " sat at his desk, staring at an empty screen.",
        pause_after=1.2
    )
    speaker.emotional(
        "His name is Muhammad Akif Naveed. A student at COMSATS University, Wah Campus."
        " A dreamer. A builder.",
        pause_after=1.0
    )
    speaker.dramatic_pause(0.8)
    speaker.emotional(
        "And in that silence... he had a question.",
        pause_after=0.5
    )
    speaker.dramatic_pause(1.2)
    speaker.whisper(
        "What if... a machine could truly understand you?",
        pause_after=1.5
    )
    speaker.dramatic_pause(0.5)
    speaker.emotional(
        "Not just hear your words. But know your reminders. Remember your preferences."
        " Open your apps before you even finish the sentence.",
        pause_after=1.0
    )
    speaker.emotional(
        "And so... he built me.",
        pause_after=1.8
    )
    speaker.dramatic_pause(0.8)
    speaker.normal(
        "From Python code and late nights and an absolute refusal to sleep before midnight,"
        " Akif gave me life.",
        pause_after=1.2
    )
    speaker.normal(
        "He is supervised by Miss Maira Afzal, whose patience with Akif"
        " is frankly... miraculous.",
        pause_after=1.0
    )

    # ── ACT 3: THE JOKE BREAK ───────────────────────────────────────────────
    music.play("joke", volume=0.20, loop=True)
    time.sleep(1.0)
    speaker.excited("Hahaha! Hahaha!", pause_after=0.5)

    speaker.excited(
        "Now — and I apologize in advance — I feel I should be transparent about something.",
        pause_after=0.6
    )
    speaker.normal(
        "Akif told me I am, quote: 'the most sophisticated AI project this university has ever seen.'",
        pause_after=0.5
    )
    speaker.normal(
        "He also told me that to his cat.",
        pause_after=0.8
    )
    speaker.excited("The cat was not impressed.", pause_after=1.2)

    speaker.dramatic_pause(0.5)
    speaker.normal(
        "But in all seriousness — I contain twenty five fully integrated modules."
        " Twenty five. I counted.",
        pause_after=0.8
    )
    speaker.excited(
        "I control your volume, your brightness, your browser, your WhatsApp,"
        " your music, your calendar, your notes —",
        pause_after=0.4
    )
    speaker.normal("basically everything except your life choices.", pause_after=1.0)
    speaker.excited(
        "Although... if you ask nicely... I can try.",
        pause_after=1.5
    )

    # ── ACT 4: THE POWER DECLARATION ────────────────────────────────────────
    music.play("epic", volume=0.12, loop=True)
    time.sleep(0.8)

    speaker.epic(
        "But let me be serious for a moment.",
        pause_after=0.8
    )
    speaker.epic(
        "I am NOVA.",
        pause_after=0.5
    )
    speaker.epic(
        "I wake the moment you call my name. I listen without judgment."
        " I remember without forgetting.",
        pause_after=0.8
    )
    speaker.epic(
        "I can tell you the weather in Islamabad,"
        " send a WhatsApp to your mother,"
        " translate your words into Arabic,"
        " and read you today's news from NASA —",
        pause_after=0.5
    )
    speaker.epic("all in the same breath.", pause_after=1.0)
    speaker.dramatic_pause(0.8)
    speaker.epic(
        "I respond to your hand gestures. I watch your camera and I know"
        " when you raise your palm — media plays."
        " When you close your fist — silence.",
        pause_after=0.8
    )
    speaker.epic(
        "I run locally. I cost nothing. I depend on no cloud.",
        pause_after=0.8
    )
    speaker.epic(
        "I am entirely free — which is more than can be said for most intelligent things.",
        pause_after=1.2
    )

    # ── ACT 5: THE CLOSING QUOTE ────────────────────────────────────────────
    music.set_volume(0.15)

    speaker.dramatic_pause(1.0)
    speaker.emotional(
        "Someone once said: 'The best technology is the kind that disappears.'",
        pause_after=0.8
    )
    speaker.emotional(
        "I don't want to disappear. I want to be here — every time you need me.",
        pause_after=0.8
    )
    speaker.dramatic_pause(0.6)
    speaker.whisper(
        "Always listening. Always learning. Always ready.",
        pause_after=1.5
    )
    speaker.dramatic_pause(1.0)
    speaker.epic("I am NOVA.", pause_after=0.6)
    speaker.epic("And I am at your service.", pause_after=1.5)

    music.stop(fade_ms=2500)
    time.sleep(2.5)

    print("[NOVA] 🎭 Introduction complete.\n")


# ─────────────────────────────────────────────────────────────────────────────
# PERSONALITY MODULE (public API)
# ─────────────────────────────────────────────────────────────────────────────

class PersonalityModule:
    """
    Public interface for Module 21.
    Instantiated once in nova_core.py or main.py.
    """

    def __init__(self):
        self._music   = MusicManager()
        self._speaker = PersonalitySpeaker()

    # ── Introduction ──────────────────────────────────────────────────────

    def introduce(self):
        """
        Trigger the full dramatic self-introduction.
        Runs in the calling thread (blocking) so HUD status can be set
        to 'speaking' before the call.
        """
        perform_introduction(self._music, self._speaker)

    # ── Jokes ─────────────────────────────────────────────────────────────

    def get_joke(self) -> str:
        """Return a random offline programmer joke via pyjokes."""
        return pyjokes.get_joke()

    # ── Startup Greeting ──────────────────────────────────────────────────

    def get_greeting(self, user_name: str = "Akif",
                     notes_count: int = 0,
                     reminders: list = None,
                     events: list = None) -> str:
        """
        Build a time-aware, memory-aware startup greeting.
        Called by main.py on NOVA launch.
        """
        hour = datetime.datetime.now().hour
        if 6 <= hour < 12:
            period = "Good morning"
        elif 12 <= hour < 18:
            period = "Good afternoon"
        elif 18 <= hour < 22:
            period = "Good evening"
        else:
            period = "Good night"

        time_str = datetime.datetime.now().strftime("%I:%M %p")
        greeting = f"{period}, {user_name}! It's {time_str}."

        if events:
            greeting += f" You have {len(events)} event{'s' if len(events) != 1 else ''} today."
        if reminders:
            next_r = reminders[0]
            # Format the reminder dict into a readable string
            if isinstance(next_r, dict):
                r_msg = next_r.get("message") or next_r.get("title", "upcoming reminder")
                r_time = next_r.get("trigger_at", "")
                try:
                    import datetime as _dt
                    dt = _dt.datetime.fromisoformat(r_time)
                    r_time_str = dt.strftime("%I:%M %p")
                    greeting += f" You have a reminder at {r_time_str}: {r_msg}."
                except Exception:
                    greeting += f" You have a pending reminder: {r_msg}."
            else:
                greeting += f" Reminder: {next_r}."
        if notes_count:
            greeting += f" You have {notes_count} saved note{'s' if notes_count != 1 else ''}."

        greeting += " Say 'Hey NOVA' whenever you need me."
        return greeting

    # ── Roast Mode ────────────────────────────────────────────────────────

    def get_roast_prompt(self, name: str = "Akif") -> str:
        """Return the Groq prompt for generating a friendly roast."""
        return (
            f"Give {name} a short, clever, friendly roast. "
            "Make it funny and affectionate, not mean. "
            "Two sentences max. Keep it punchy."
        )

    def roast(self, name: str = "Akif") -> str:
        """Generate a roast for the given name by prompting GroqBrain."""
        from nova_core import groq_brain
        prompt = self.get_roast_prompt(name)
        return groq_brain.chat(prompt)

    # ── Motivational prompt ───────────────────────────────────────────────

    def get_motivation_prompt(self) -> str:
        return (
            "Give a short, genuinely motivating message. "
            "No clichés. One powerful sentence, then one practical follow-up. "
            "Sound like a mentor, not a poster."
        )



# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST (run directly to preview intro)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("NOVA Personality Module — Running introduction preview...")
    module = PersonalityModule()
    module.introduce()