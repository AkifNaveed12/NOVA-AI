import ctypes
import pyautogui

# Ensure fail-safe is enabled so pushing mouse to corner halts it
pyautogui.FAILSAFE = True

# MOUSEEVENTF_MOVE = 0x0001
# MOUSEEVENTF_LEFTDOWN = 0x0002
# MOUSEEVENTF_LEFTUP = 0x0004
# MOUSEEVENTF_RIGHTDOWN = 0x0008
# MOUSEEVENTF_RIGHTUP = 0x0010

def move_mouse_relative(dx: float, dy: float):
    """Move cursor relatively using Windows user32 mouse_event for zero latency."""
    try:
        ctypes.windll.user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)
    except Exception as e:
        print(f"[MouseControl] Relative move error: {e}")
        # Fallback to pyautogui
        pyautogui.moveRel(dx, dy)

def click_mouse(button: str = "left"):
    """Trigger mouse clicks on the PC."""
    try:
        if button == "left":
            pyautogui.click()
        elif button == "right":
            pyautogui.rightClick()
        elif button == "double":
            pyautogui.doubleClick()
    except Exception as e:
        print(f"[MouseControl] Click error: {e}")

def scroll_mouse(amount: int):
    """Scroll the mouse wheel (positive for up, negative for down)."""
    try:
        pyautogui.scroll(amount)
    except Exception as e:
        print(f"[MouseControl] Scroll error: {e}")
