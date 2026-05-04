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

import tkinter as tk
from tkinter import scrolledtext
import datetime
import math
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

# Colors
BG_COLOR = "#0D0D0D"
TEXT_COLOR = "#C4B8FC"
CYAN = "#00D4FF"

class NOVAHud:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NOVA HUD")
        
        # Frameless, topmost, transparent
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.92)
        self.root.configure(bg=BG_COLOR)
        
        # Dimensions and placement (320px wide, full height, right docked)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = 320
        self.root.geometry(f"{width}x{screen_height}+{screen_width - width}+0")
        
        # Internal state
        self.current_state = "sleeping" # sleeping, listening, processing, speaking
        
        self._build_ui()
        self._update_clock()
        
    def _build_ui(self):
        # 1. Header Frame (Clock & Status)
        header_frame = tk.Frame(self.root, bg=BG_COLOR)
        header_frame.pack(fill=tk.X, pady=20, padx=10)
        
        self.clock_label = tk.Label(header_frame, text="00:00:00", font=("Courier New", 18, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
        self.clock_label.pack(anchor="e")
        
        self.status_label = tk.Label(header_frame, text="🔴 Sleeping", font=("Courier New", 12), bg=BG_COLOR, fg="#ff4444")
        self.status_label.pack(anchor="e", pady=5)
        
        # 2. Waveform Frame
        wave_frame = tk.Frame(self.root, bg=BG_COLOR, height=300)
        wave_frame.pack(fill=tk.X, pady=10)
        
        self.fig = Figure(figsize=(3, 3), dpi=100, facecolor=BG_COLOR)
        self.ax = self.fig.add_subplot(111, projection='polar')
        self.ax.set_facecolor(BG_COLOR)
        self.ax.axis('off')
        
        # Setup data for a circle of 64 bars
        self.N = 64
        self.theta = np.linspace(0.0, 2 * np.pi, self.N, endpoint=False)
        self.radii = np.ones(self.N) * 2
        self.width = (2 * np.pi) / self.N
        self.bars = self.ax.bar(self.theta, self.radii, width=self.width, bottom=1.0, color=CYAN, alpha=0.8)
        self.ax.set_ylim(0, 10)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=wave_frame)
        self.canvas.get_tk_widget().pack()
        
        self.ani = animation.FuncAnimation(self.fig, self._animate_waveform, interval=50, blit=True, cache_frame_data=False)
        
        # 3. Log Frame
        log_frame = tk.Frame(self.root, bg=BG_COLOR)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        log_label = tk.Label(log_frame, text="ACTIVITY LOG", font=("Courier New", 10, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
        log_label.pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=("Courier New", 9), bg="#1A1A1A", fg=TEXT_COLOR, 
                                                insertbackground=TEXT_COLOR, relief=tk.FLAT, borderwidth=0, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # Bind double-click to exit (emergency close)
        self.root.bind("<Double-Button-1>", lambda e: self.root.destroy())

    def _animate_waveform(self, frame):
        """Animates the matplotlib bars based on NOVA's state."""
        base_amplitude = 1.0
        wave_speed = frame * 0.1
        
        if self.current_state == "sleeping":
            base_amplitude = 0.5
            color = "#ff4444"
            wave_speed = frame * 0.05
        elif self.current_state == "listening":
            base_amplitude = 3.0
            color = "#ffd700"
            wave_speed = frame * 0.2
        elif self.current_state == "processing":
            base_amplitude = 1.5
            color = "#00ff00"
            wave_speed = frame * 0.4
        elif self.current_state == "speaking":
            base_amplitude = 4.0
            color = CYAN
            wave_speed = frame * 0.3
            
        for i, bar in enumerate(self.bars):
            # Generate a wave pattern
            noise = np.sin(wave_speed + i * 0.5) * base_amplitude
            # Add some randomness if speaking/listening
            if self.current_state in ["speaking", "listening"]:
                noise += np.random.rand() * base_amplitude * 0.5
            
            bar.set_height(max(0.5, 1.0 + noise))
            bar.set_color(color)
            
        return self.bars

    def _update_clock(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self._update_clock)

    def update_status(self, state: str):
        """Thread-safe state update: 'sleeping', 'listening', 'processing', 'speaking'."""
        def _update():
            self.current_state = state
            if state == "sleeping":
                self.status_label.config(text="🔴 Sleeping", fg="#ff4444")
            elif state == "listening":
                self.status_label.config(text="🟡 Listening", fg="#ffd700")
            elif state == "processing":
                self.status_label.config(text="🟢 Processing", fg="#00ff00")
            elif state == "speaking":
                self.status_label.config(text="🔵 Speaking", fg=CYAN)
        
        # Schedule the update on the main thread
        self.root.after(0, _update)

    def log_message(self, role: str, text: str):
        """Thread-safe log append."""
        def _log():
            self.log_text.config(state=tk.NORMAL)
            prefix = "[USER]" if role == "user" else "[NOVA]"
            self.log_text.insert(tk.END, f"{prefix}\n{text}\n\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            
        # Schedule the update on the main thread
        self.root.after(0, _log)

    def start(self):
        """Blocks and runs the Tkinter mainloop."""
        self.root.mainloop()
