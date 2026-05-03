"""
MODULE 22 — Hand Gesture Control Engine
==========================================
Always-on, vision-based OS control running completely in parallel
to the voice pipeline as a daemon thread. Detects 9 hand gestures
via MediaPipe 21-point landmark tracking. Dispatches OS actions
via thread-safe queue.Queue to avoid race conditions.

Gesture map:
  Open palm     → Play/resume media
  Fist          → Pause media
  Index only    → Volume up +5%
  Index+middle  → Scroll up
  Three fingers → Scroll down
  Pinch         → Zoom in
  OK sign       → Next browser tab
  Swipe left    → Previous track
  Swipe right   → Next track

Tech: OpenCV (camera), MediaPipe Hands (landmarks), pycaw (volume),
      pyautogui (scroll/zoom/tab), threading, queue
Debounce: Gesture must hold 0.4s before action fires
"""

# TODO: implement GestureEngine class with start(), stop(),
#       _gesture_loop(), _classify_gesture(), _dispatch_action(),
#       _should_trigger() methods
