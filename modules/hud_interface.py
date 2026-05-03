"""
MODULE 23 — HUD Interface
===========================
NOVA's visual face — a frameless, always-on-top, semi-transparent
dark overlay docked to the right side of the screen (320px wide,
full screen height). Displays animated waveform, status indicator,
live clock, last 5 command/response pairs, reminders ticker, and
optional gesture camera feed.

Window: Tkinter, overrideredirect(True), -topmost, alpha=0.92
Background: #0D0D0D | Width: 320px | Docked: right
Colors: #7B6CF6 violet, #00D4FF cyan, #5DCAA5 teal, #C4B8FC lavender
Waveform: matplotlib FuncAnimation, 64 bars, polar/circular, 20fps
Font: Courier New (monospace) throughout — no proportional fonts

Tech: Tkinter (built-in), matplotlib FuncAnimation
IMPORTANT: Tkinter mainloop MUST run on main thread
"""

# TODO: implement NOVAHud class with update_status(), update_display(),
#       update_ticker(), update_gesture_cam(), safe_update() methods
