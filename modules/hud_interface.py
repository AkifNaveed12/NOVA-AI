"""
MODULE 23 — HUD Interface (pywebview edition)
=============================================
Replaces the Tkinter + matplotlib implementation with a pywebview
window that renders nova_hud.html — a fully self-contained cinematic
dark UI with animated SVG logo, canvas waveform, live clock, command
log, and reminders ticker.

Public API is IDENTICAL to the old Tkinter version so main.py
requires zero changes:
    hud = NOVAHud()
    hud.update_status("listening")
    hud.log_message("user", "open chrome")
    hud.log_message("nova", "Opening Chrome.")
    hud.start()          # blocks — call in main thread

Architecture:
    - pywebview opens a native OS window (frameless, always-on-top)
    - Python calls webview.evaluate_js() to push state updates to JS
    - JS functions novaSetStatus() / novaAppendLog() / novaSetTicker()
      are defined in nova_hud.html and respond immediately
    - Thread-safety: evaluate_js() is thread-safe in pywebview 4.x;
      we additionally queue calls and flush after DOM-ready to be safe

Dependencies:
    pip install pywebview

nova_hud.html must be in the same directory as this file (modules/).
If running from project root, the path is resolved automatically.
"""

import queue
import threading
import time
from pathlib import Path
import webview  # pip install pywebview


# ── Resolve path to the HTML file ─────────────────────────────────
_HERE = Path(__file__).parent          # …/modules/
_ROOT = _HERE.parent                   # project root
_HTML = _HERE / "nova_hud.html"

# Fallback: check project root too
if not _HTML.exists():
    _HTML = _ROOT / "nova_hud.html"

if not _HTML.exists():
    raise FileNotFoundError(
        f"nova_hud.html not found. Expected at: {_HERE / 'nova_hud.html'}"
    )

# pywebview on Windows requires file:// URI for local HTML files
# Path.as_uri() gives the correct 'file:///D:/...' form on all platforms
HTML_PATH = _HTML.as_uri()


class NOVAHudAPI:
    """JS-accessible API for the pywebview window."""
    def __init__(self):
        self._window = None
        self.updates_queue = queue.Queue()

    def close_app(self):
        """Called from JS to close the window gracefully."""
        if self._window:
            self._window.destroy()

    def get_updates(self):
        """Called by JS every 200ms to fetch UI updates safely on the UI thread."""
        updates = []
        while not self.updates_queue.empty():
            try:
                updates.append(self.updates_queue.get_nowait())
            except queue.Empty:
                break
        return updates


class NOVAHud:
    """
    Cinematic HUD window for NOVA AI using pywebview.

    Drop-in replacement for the old Tkinter NOVAHud.
    Thread-safe: update_status() and log_message() can be called
    from any background thread.
    """

    def __init__(self):
        self._window   = None          # set after start()
        self._ready    = False         # True once DOM is fully loaded
        self._queue    = queue.Queue() # buffered JS calls before ready
        self._state    = "sleeping"
        self._api      = NOVAHudAPI()

        # Create the pywebview window immediately (not shown until start())
        self._window = webview.create_window(
            title       = "NOVA AI",
            url         = HTML_PATH,
            js_api      = self._api,
            width       = 380,
            height      = 900,
            x           = None,        # pywebview will centre or use OS default
            y           = None,
            resizable   = False,
            frameless   = True,        # no title bar — matches original design
            on_top      = True,        # always-on-top
            background_color = "#0D0D0D",
            transparent = True,        # allow semi-transparency on supported platforms
            min_size    = (320, 600),
        )

        self._api._window = self._window

        # Register the loaded callback
        self._window.events.loaded += self._on_loaded

    # ── DOM-ready callback ─────────────────────────────────────────
    def _on_loaded(self):
        """Called by pywebview once the HTML/JS is fully loaded."""
        self._ready = True

    # ── Public API (identical to old Tkinter NOVAHud) ──────────────

    def update_status(self, state: str):
        """
        Update NOVA's status indicator and waveform colour.
        state: 'sleeping' | 'listening' | 'processing' | 'speaking'
        Thread-safe via JS polling.
        """
        if self._state == state:
            return
            
        self._state = state
        self._api.updates_queue.put({"type": "status", "data": state})

    def log_message(self, role: str, text: str):
        """
        Append a command/response pair to the conversation log.
        role: 'user' | 'nova'
        Thread-safe via JS polling.
        """
        self._api.updates_queue.put({"type": "log", "role": role, "text": text})

    def update_ticker(self, text: str):
        """
        Update the scrolling reminders ticker.
        Thread-safe via JS polling.
        """
        self._api.updates_queue.put({"type": "ticker", "data": text})

    def start(self):
        """
        Start the pywebview event loop. BLOCKS until the window is closed.
        Must be called from the main thread (same requirement as Tkinter).
        """
        webview.start(
            debug        = False,   # set True during development to open DevTools
            private_mode = False,   # allow storage so page loads consistently
            http_server  = False,   # not needed — file:// URI works directly
        )


# ── Standalone test ────────────────────────────────────────────────
if __name__ == "__main__":
    """Quick smoke-test: open HUD, cycle through all states."""
    hud = NOVAHud()

    def _demo():
        time.sleep(1.5)
        for state, cmd, resp in [
            ("listening",  "Hey NOVA, what time is it?",       ""),
            ("processing", "Hey NOVA, what time is it?",       ""),
            ("speaking",   "Hey NOVA, what time is it?",       "It is 09:42 PM."),
            ("sleeping",   "",                                  ""),
            ("listening",  "Open Chrome",                       ""),
            ("processing", "Open Chrome",                       ""),
            ("speaking",   "Open Chrome",                       "Opening Chrome."),
            ("sleeping",   "",                                  ""),
        ]:
            hud.update_status(state)
            if cmd:
                hud.log_message("user", cmd)
            if resp:
                hud.log_message("nova", resp)
            time.sleep(1.2)

        hud.update_ticker("⏰ 10:00 PM — Review NOVA modules   ⏰ 11:00 PM — Push to GitHub")

    t = threading.Thread(target=_demo, daemon=True)
    t.start()

    hud.start()  # blocks