"""
Tests for Module 22: Hand Gesture Engine
"""
import unittest
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modules.gesture_engine import GestureEngine

class DummyLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class DummyHandLandmarks:
    def __init__(self, landmarks):
        self.landmark = [DummyLandmark(x, y) for x, y in landmarks]

class TestGestureEngine(unittest.TestCase):
    def setUp(self):
        # Initialize without starting the thread
        self.engine = GestureEngine(debounce_seconds=0.1)

    def test_fingers_up_open_palm(self):
        # Mock 21 landmarks for an open palm (tips above PIPs)
        # 0: wrist, 1-4: thumb, 5-8: index, 9-12: middle, 13-16: ring, 17-20: pinky
        # y coordinates decrease as they go UP the screen
        landmarks = [(0, 0)] * 21
        
        # Thumb: x is further left than knuckle (for right hand)
        landmarks[3] = (100, 100) # Thumb PIP
        landmarks[4] = (50, 100)  # Thumb Tip (left of PIP -> up)

        # Index
        landmarks[6] = (100, 100) # PIP
        landmarks[8] = (100, 50)  # Tip (above PIP)

        # Middle
        landmarks[10] = (100, 100)
        landmarks[12] = (100, 50)

        # Ring
        landmarks[14] = (100, 100)
        landmarks[16] = (100, 50)

        # Pinky
        landmarks[18] = (100, 100)
        landmarks[20] = (100, 50)

        fingers = self.engine._fingers_up(landmarks)
        self.assertEqual(fingers, [1, 1, 1, 1, 1], "Open palm should have all 5 fingers up")
        
        # Classification
        # Set wrist and middle finger base for pinch distance reference
        landmarks[0] = (100, 200) # Wrist
        landmarks[9] = (100, 100) # Middle base
        gesture = self.engine._classify_gesture(landmarks, fingers, 0)
        self.assertEqual(gesture, "open_palm")

    def test_fingers_up_fist(self):
        # Mock 21 landmarks for a fist (tips below PIPs)
        landmarks = [(0, 0)] * 21
        
        # Thumb: Tip right of PIP
        landmarks[3] = (100, 100)
        landmarks[4] = (150, 100)

        # Index: Tip below PIP
        landmarks[6] = (100, 100)
        landmarks[8] = (100, 150)

        # Middle
        landmarks[10] = (100, 100)
        landmarks[12] = (100, 150)

        # Ring
        landmarks[14] = (100, 100)
        landmarks[16] = (100, 150)

        # Pinky
        landmarks[18] = (100, 100)
        landmarks[20] = (100, 150)

        fingers = self.engine._fingers_up(landmarks)
        self.assertEqual(fingers, [0, 0, 0, 0, 0], "Fist should have 0 fingers up")

        landmarks[0] = (100, 200)
        landmarks[9] = (100, 100)
        gesture = self.engine._classify_gesture(landmarks, fingers, 0)
        self.assertEqual(gesture, "fist")

    def test_pinch_gesture(self):
        landmarks = [(0, 0)] * 21
        # Set reference distance
        landmarks[0] = (100, 200)
        landmarks[9] = (100, 100)
        
        # Set thumb tip and index tip close
        landmarks[4] = (100, 100)
        landmarks[8] = (102, 102)
        
        # Doesn't matter what fingers are up for pinch if distance is small enough
        fingers = [0, 0, 0, 0, 0]
        
        gesture = self.engine._classify_gesture(landmarks, fingers, 0)
        self.assertEqual(gesture, "pinch")

    def test_debounce_logic(self):
        # Should not trigger immediately
        triggered = self.engine._should_trigger("open_palm")
        self.assertFalse(triggered, "Should not trigger on first frame")

        # Wait for debounce time
        time.sleep(0.15)
        
        # Should trigger now
        triggered2 = self.engine._should_trigger("open_palm")
        self.assertTrue(triggered2, "Should trigger after debounce period")

        # Should not trigger again immediately
        triggered3 = self.engine._should_trigger("open_palm")
        self.assertFalse(triggered3, "Should not trigger again immediately after dispatch")

if __name__ == '__main__':
    unittest.main()
