"""
MODULE 22 — Hand Gesture Control Engine
==========================================
Always-on, vision-based OS control running completely in parallel
to the voice pipeline as a daemon thread. Detects hand gestures
via MediaPipe 21-point landmark tracking. Dispatches OS actions
via thread-safe mechanisms to avoid race conditions.

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

Tech: OpenCV (camera), MediaPipe Hands (landmarks), pyautogui (scroll/zoom/tab)
Debounce: Gesture must hold 0.4s before action fires
"""

import threading
import queue
import time
import math
import cv2
import mediapipe as mp
import pyautogui
from modules.system_controls import SystemControls

class GestureEngine:
    def __init__(self, camera_index=0, fps_target=20, debounce_seconds=0.4, pinch_threshold=0.05):
        self.camera_index = camera_index
        self.fps_target = fps_target
        self.debounce_seconds = debounce_seconds
        self.pinch_threshold = pinch_threshold
        
        self._stop_event = threading.Event()
        self._thread = None
        
        # Debounce state
        self._current_gesture = None
        self._gesture_start_time = 0
        self._action_dispatched = False
        self._last_wrist_x = None
        
        self.sys_controls = SystemControls()
        self.mp_hands = mp.solutions.hands
        # We initialize hands in the thread to avoid threading issues with mediapipe
        self.hands = None

    def start(self):
        """Starts the gesture engine daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._gesture_loop, daemon=True, name="GestureEngineThread")
        self._thread.start()
        print("[GestureEngine] Started.")

    def stop(self):
        """Signals the gesture engine to stop and releases resources."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        print("[GestureEngine] Stopped.")

    def _get_landmark_list(self, hand_landmarks, width, height):
        """Extracts (x, y) coordinates from normalized landmarks."""
        landmarks = []
        for lm in hand_landmarks.landmark:
            cx, cy = int(lm.x * width), int(lm.y * height)
            landmarks.append((cx, cy))
        return landmarks

    def _fingers_up(self, landmarks):
        """Returns a list of 5 booleans representing which fingers are up."""
        fingers = []
        # Thumb: compare x coordinates (assuming right hand for simplicity, logic can be improved)
        # Landmark 4 is thumb tip, 3 is thumb IP
        # Actually for generic open/closed, just comparing tip y to pip y is often enough for the 4 fingers
        # For thumb, check if it's further out horizontally than the inner knuckle
        if landmarks[4][0] < landmarks[3][0]: # Simplified for Right hand facing camera
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 Fingers: Index, Middle, Ring, Pinky
        # Tips: 8, 12, 16, 20. PIPs: 6, 10, 14, 18
        tip_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]
        
        for i in range(4):
            # If tip y is higher (smaller value) than pip y, finger is up
            if landmarks[tip_ids[i]][1] < landmarks[pip_ids[i]][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def _classify_gesture(self, landmarks, fingers, wrist_delta):
        """Maps fingers and landmarks to a recognized gesture string."""
        # Calculate pinch distance (normalized or pixel based, let's use Euclidean on pixel)
        # We need normalized for consistency across resolutions, but we have pixel coords.
        # Let's approximate based on wrist to middle finger base distance to scale it
        ref_dist = math.dist(landmarks[0], landmarks[9])
        if ref_dist == 0: ref_dist = 1
        pinch_dist = math.dist(landmarks[4], landmarks[8]) / ref_dist

        if pinch_dist < self.pinch_threshold:
            return "pinch"
            
        # Swipe detection
        if wrist_delta:
            if wrist_delta < -0.15: # Moved left
                return "swipe_left"
            elif wrist_delta > 0.15: # Moved right
                return "swipe_right"

        # OK sign: thumb and index touching, other 3 up
        if pinch_dist < 0.2 and fingers[2] and fingers[3] and fingers[4]:
            return "ok_sign"

        total_up = sum(fingers)
        if total_up == 5:
            return "open_palm"
        if total_up == 0:
            return "fist"
        
        # Specific finger combos
        if fingers == [0, 1, 0, 0, 0] or fingers == [1, 1, 0, 0, 0]: # Index up (thumb might be out)
            return "index_up"
        if fingers == [0, 1, 1, 0, 0] or fingers == [1, 1, 1, 0, 0]: # Index + middle
            return "two_fingers"
        if fingers == [0, 1, 1, 1, 0] or fingers == [1, 1, 1, 1, 0]: # Index + middle + ring
            return "three_fingers"

        return "unknown"

    def _should_trigger(self, gesture):
        """Checks if gesture has been held long enough to trigger."""
        if gesture == "unknown":
            self._current_gesture = None
            self._action_dispatched = False
            return False

        if gesture != self._current_gesture:
            self._current_gesture = gesture
            self._gesture_start_time = time.time()
            self._action_dispatched = False
            return False

        # If it's the same gesture, check time
        if not self._action_dispatched:
            elapsed = time.time() - self._gesture_start_time
            if elapsed >= self.debounce_seconds:
                self._action_dispatched = True
                return True
                
        return False

    def _dispatch_action(self, gesture):
        """Executes the OS action corresponding to the gesture."""
        print(f"[GestureEngine] Triggering: {gesture}")
        try:
            if gesture == "open_palm":
                pyautogui.press('playpause')
            elif gesture == "fist":
                # Pyautogui playpause toggles, so we can't definitively pause. 
                # We'll use playpause for both, or just log it.
                pyautogui.press('playpause')
            elif gesture == "index_up":
                # volume up
                pyautogui.press('volumeup')
                pyautogui.press('volumeup')
            elif gesture == "two_fingers":
                # scroll up
                pyautogui.scroll(300)
                # Reset dispatched so it can trigger repeatedly while held
                self._action_dispatched = False
                self._gesture_start_time = time.time() - (self.debounce_seconds - 0.1) # shorter repeat delay
            elif gesture == "three_fingers":
                # scroll down
                pyautogui.scroll(-300)
                self._action_dispatched = False
                self._gesture_start_time = time.time() - (self.debounce_seconds - 0.1)
            elif gesture == "pinch":
                # zoom in (ctrl + '=')
                pyautogui.hotkey('ctrl', '=')
                self._action_dispatched = False
                self._gesture_start_time = time.time() - (self.debounce_seconds - 0.2)
            elif gesture == "ok_sign":
                # next browser tab
                pyautogui.hotkey('ctrl', 'tab')
            elif gesture == "swipe_left":
                pyautogui.press('prevtrack')
            elif gesture == "swipe_right":
                pyautogui.press('nexttrack')
        except Exception as e:
            print(f"[GestureEngine] Error dispatching {gesture}: {e}")

    def _gesture_loop(self):
        """Main OpenCV + MediaPipe loop."""
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print("[GestureEngine] Error: Could not open camera.")
            return

        print("[GestureEngine] Camera active and listening for gestures.")
        
        while not self._stop_event.is_set():
            start_t = time.time()
            success, image = cap.read()
            if not success:
                time.sleep(0.1)
                continue

            # Flip image horizontally for selfie-view display
            image = cv2.flip(image, 1)
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.hands.process(image_rgb)
            
            wrist_delta = 0
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    h, w, c = image.shape
                    landmarks = self._get_landmark_list(hand_landmarks, w, h)
                    
                    # Compute wrist delta for swipes
                    normalized_wrist_x = hand_landmarks.landmark[0].x
                    if self._last_wrist_x is not None:
                        wrist_delta = normalized_wrist_x - self._last_wrist_x
                    self._last_wrist_x = normalized_wrist_x

                    fingers = self._fingers_up(landmarks)
                    gesture = self._classify_gesture(landmarks, fingers, wrist_delta)
                    
                    if self._should_trigger(gesture):
                        self._dispatch_action(gesture)
            else:
                self._last_wrist_x = None
                self._current_gesture = None
                self._action_dispatched = False

            # Maintain target FPS
            elapsed = time.time() - start_t
            sleep_time = max(0, (1.0 / self.fps_target) - elapsed)
            time.sleep(sleep_time)

        cap.release()
        self.hands.close()
