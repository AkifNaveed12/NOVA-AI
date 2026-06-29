"""
MODULE — Context Scanner (NOVA Flagship Feature 1)
====================================================
Autonomous PC Awareness — polls the machine state every 10 seconds and
builds a rolling 30-minute context buffer.

At every voice interaction, get_context_summary() returns a single-line
string injected into the Groq prompt so NOVA can answer questions like
"what am I working on?" or "why is my PC slow?" without the user having
to explain anything.

Why Gemini / ChatGPT cannot do this:
    They have no access to Windows APIs, process lists, active window
    titles, clipboard, or recent file activity.

Architecture:
    - Daemon thread polling every SCAN_INTERVAL seconds (default 10)
    - context_buffer: deque(maxlen=180) → 30 minutes at 10s intervals
    - latest: dict → most recent snapshot (used for Groq injection)
    - Exposed as singleton `context_scanner`
    - Started by main.py alongside wake_word and gesture threads

API endpoint:
    GET /api/context/current → returns context_scanner.latest as JSON
    (added to modules/api_server.py)

Dependencies: psutil (already in requirements), pygetwindow, pyperclip
"""

import os
import time
import threading
from collections import deque
from pathlib import Path


class ContextScanner:
    """Lightweight 10s polling daemon — builds a live PC context model.

    Singleton pattern: import and use `context_scanner` directly.
    """

    SCAN_INTERVAL = 10      # seconds between scans
    BUFFER_MINUTES = 30     # rolling window length

    def __init__(self):
        self.context_buffer = deque(
            maxlen=int(self.BUFFER_MINUTES * 60 / self.SCAN_INTERVAL)
        )
        self.latest: dict = {}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # ── Internal scanners ─────────────────────────────────────────────

    def _get_active_window(self) -> dict:
        try:
            import pygetwindow as gw
            win = gw.getActiveWindow()
            if win and win.title:
                return {"title": win.title}
        except Exception:
            pass
        return {}

    def _get_clipboard(self) -> str:
        try:
            import pyperclip
            text = pyperclip.paste()
            return (text or "")[:500]   # cap at 500 chars for safety
        except Exception:
            return ""

    def _get_top_processes(self, n: int = 5) -> list:
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    procs.append(p.info)
                except Exception:
                    pass
            return sorted(
                procs, key=lambda x: x.get("cpu_percent", 0), reverse=True
            )[:n]
        except Exception:
            return []

    def _get_recent_files(self, minutes: int = 10) -> list:
        """Scan Desktop, Documents, Downloads for recently modified files."""
        recent = []
        cutoff = time.time() - minutes * 60
        safe_dirs = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
        ]
        for d in safe_dirs:
            if not d.exists():
                continue
            try:
                for f in d.iterdir():
                    try:
                        if f.is_file() and f.stat().st_mtime > cutoff:
                            recent.append({
                                "name": f.name,
                                "path": str(f),
                                "modified": f.stat().st_mtime,
                            })
                    except Exception:
                        pass
            except PermissionError:
                pass
        return sorted(recent, key=lambda x: x["modified"], reverse=True)[:10]

    def _get_battery(self) -> dict:
        try:
            import psutil
            b = psutil.sensors_battery()
            if b:
                return {"percent": round(b.percent, 1), "plugged": b.power_plugged}
        except Exception:
            pass
        return {}

    def _get_system_stats(self) -> dict:
        """CPU and RAM snapshot for quick health overview."""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "ram_percent": psutil.virtual_memory().percent,
            }
        except Exception:
            return {}

    # ── Core scan ─────────────────────────────────────────────────────

    def _scan(self) -> dict:
        snapshot = {
            "timestamp": time.time(),
            "active_window": self._get_active_window(),
            "clipboard": self._get_clipboard(),
            "top_processes": self._get_top_processes(),
            "recent_files": self._get_recent_files(),
            "battery": self._get_battery(),
            "system": self._get_system_stats(),
        }
        self.context_buffer.append(snapshot)
        self.latest = snapshot
        return snapshot

    # ── Public API ────────────────────────────────────────────────────

    def get_context_summary(self) -> str:
        """Returns a concise single-line string for Groq prompt injection.

        Example output:
            "Active window: VS Code - main.py | Clipboard: AttributeError: 'NoneType'...
             | Recently modified: main.py, requirements.txt | High CPU: python.exe"
        """
        c = self.latest
        if not c:
            return ""

        parts = []

        # Active window
        win_title = c.get("active_window", {}).get("title", "")
        if win_title:
            parts.append(f"Active window: {win_title}")

        # Clipboard (only if non-empty and looks meaningful)
        clipboard = c.get("clipboard", "").strip()
        if clipboard and len(clipboard) > 3:
            parts.append(f"Clipboard: {clipboard[:200]}")

        # Recently modified files
        files = c.get("recent_files", [])
        if files:
            names = [f["name"] for f in files[:3]]
            parts.append(f"Recently modified: {', '.join(names)}")

        # High-CPU processes (> 5% threshold)
        top_procs = [
            p["name"] for p in c.get("top_processes", [])
            if p.get("cpu_percent", 0) > 5
        ]
        if top_procs:
            parts.append(f"High CPU: {', '.join(top_procs[:3])}")

        # System health
        sys_stats = c.get("system", {})
        if sys_stats.get("ram_percent", 0) > 85:
            parts.append(f"RAM usage: {sys_stats['ram_percent']}%")

        return " | ".join(parts) if parts else ""

    def get_latest_snapshot(self) -> dict:
        """Returns the full latest scan dict (for API endpoint serialization)."""
        # Convert Path objects to strings for JSON serialisation
        import copy
        snap = copy.deepcopy(self.latest)
        return snap

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self):
        """Start the background scanning daemon thread."""
        if self._thread and self._thread.is_alive():
            return  # Already running

        self._stop.clear()

        def _loop():
            print("[ContextScanner] Daemon started — scanning every "
                  f"{self.SCAN_INTERVAL}s.")
            # Do an immediate first scan so context is available right away
            try:
                self._scan()
            except Exception as e:
                print(f"[ContextScanner] Initial scan error: {e}")

            while not self._stop.is_set():
                self._stop.wait(self.SCAN_INTERVAL)
                if not self._stop.is_set():
                    try:
                        self._scan()
                    except Exception as e:
                        print(f"[ContextScanner] Scan error: {e}")

            print("[ContextScanner] Daemon stopped.")

        self._thread = threading.Thread(
            target=_loop, daemon=True, name="ContextScannerThread"
        )
        self._thread.start()

    def stop(self):
        """Signal the scanning daemon to stop."""
        self._stop.set()


# ── Singleton ─────────────────────────────────────────────────────────────
context_scanner = ContextScanner()
