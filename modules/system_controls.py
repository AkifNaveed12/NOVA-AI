"""
MODULE 16 — System Controls
=============================
Full OS-level Windows control by voice: volume, brightness, power
states (shutdown/restart/sleep/lock), and system info (battery,
CPU usage, RAM usage). All Windows API calls, no Unix commands.

Tech: pycaw (audio), screen_brightness_control, psutil, os, ctypes
Output: Action confirmation or status string → TTS engine
"""

import os
import subprocess


class SystemControls:
    """Voice-driven Windows system controls."""

    # ── Volume ────────────────────────────────────────────────────────

    def _get_volume_interface(self):
        """Returns the pycaw master volume interface, or None if unavailable."""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        except Exception as e:
            print(f"[SystemControls] pycaw error: {e}")
            return None

    def get_volume(self) -> str:
        """Returns the current system volume percentage."""
        vol = self._get_volume_interface()
        if vol is None:
            return "I couldn't access the system volume."
        try:
            level = round(vol.GetMasterVolumeLevelScalar() * 100)
            return f"Current volume is {level} percent."
        except Exception as e:
            return f"Couldn't read volume: {e}"

    def set_volume(self, percent: int) -> str:
        """Sets master volume to the given percentage (0–100)."""
        percent = max(0, min(100, int(percent)))
        vol = self._get_volume_interface()
        if vol is None:
            # Fallback: use nircmd if pycaw fails
            return self._nircmd_volume(percent)
        try:
            vol.SetMasterVolumeLevelScalar(percent / 100.0, None)
            return f"Volume set to {percent} percent."
        except Exception as e:
            return f"Couldn't set volume: {e}"

    def _nircmd_volume(self, percent: int) -> str:
        """Fallback: set volume using Windows PowerShell."""
        try:
            script = f"(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
            # Use the simpler approach: PowerShell audio control
            cmd = f"powershell -command \"$volume = {percent}/100.0; $obj = New-Object -ComObject WScript.Shell; Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class Audio {{ [DllImport(\\\"winmm.dll\\\")] public static extern int waveOutSetVolume(IntPtr h, uint dw); }}'; [Audio]::waveOutSetVolume([IntPtr]::Zero, [uint](($volume * 65535) * 0x10001));\""
            subprocess.run(cmd, shell=True, capture_output=True)
            return f"Volume set to {percent} percent."
        except Exception:
            return "Volume control is unavailable on this system."

    def volume_up(self, step: int = 10) -> str:
        """Increases volume by step percent."""
        vol = self._get_volume_interface()
        if vol is None:
            return "I couldn't adjust the volume."
        try:
            current = round(vol.GetMasterVolumeLevelScalar() * 100)
            new_level = min(100, current + step)
            vol.SetMasterVolumeLevelScalar(new_level / 100.0, None)
            return f"Volume increased to {new_level} percent."
        except Exception as e:
            return f"Couldn't adjust volume: {e}"

    def volume_down(self, step: int = 10) -> str:
        """Decreases volume by step percent."""
        vol = self._get_volume_interface()
        if vol is None:
            return "I couldn't adjust the volume."
        try:
            current = round(vol.GetMasterVolumeLevelScalar() * 100)
            new_level = max(0, current - step)
            vol.SetMasterVolumeLevelScalar(new_level / 100.0, None)
            return f"Volume decreased to {new_level} percent."
        except Exception as e:
            return f"Couldn't adjust volume: {e}"

    def mute(self) -> str:
        """Mutes the system audio."""
        vol = self._get_volume_interface()
        if vol is None:
            return "I couldn't mute the audio."
        try:
            vol.SetMasterVolumeLevelScalar(0.0, None)
            return "Audio muted."
        except Exception as e:
            return f"Couldn't mute: {e}"

    def unmute(self) -> str:
        """Unmutes at a reasonable default (50%)."""
        vol = self._get_volume_interface()
        if vol is None:
            return "I couldn't unmute the audio."
        try:
            vol.SetMasterVolumeLevelScalar(0.5, None)
            return "Audio unmuted. Volume set to 50 percent."
        except Exception as e:
            return f"Couldn't unmute: {e}"

    # ── Brightness ────────────────────────────────────────────────────

    def set_brightness(self, percent: int) -> str:
        """Sets screen brightness (0–100)."""
        percent = max(0, min(100, int(percent)))
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(percent)
            return f"Brightness set to {percent} percent."
        except Exception as e:
            print(f"[SystemControls] Brightness error: {e}")
            return "Brightness control is not available on this display."

    def brightness_up(self, step: int = 10) -> str:
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness(display=0)
            if isinstance(current, list):
                current = current[0]
            new_val = min(100, current + step)
            sbc.set_brightness(new_val)
            return f"Brightness increased to {new_val} percent."
        except Exception as e:
            return "Brightness control is not available."

    def brightness_down(self, step: int = 10) -> str:
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness(display=0)
            if isinstance(current, list):
                current = current[0]
            new_val = max(0, current - step)
            sbc.set_brightness(new_val)
            return f"Brightness decreased to {new_val} percent."
        except Exception as e:
            return "Brightness control is not available."

    # ── System Info ───────────────────────────────────────────────────

    def get_battery(self) -> str:
        """Returns battery percentage and charging status."""
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery is None:
                return "This device doesn't have a battery, or battery info isn't available."
            status = "charging" if battery.power_plugged else "not charging"
            return f"Battery is at {round(battery.percent)} percent and {status}."
        except Exception as e:
            return f"Couldn't read battery status: {e}"

    def get_cpu_usage(self) -> str:
        """Returns CPU usage percentage."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            return f"CPU usage is at {cpu} percent."
        except Exception as e:
            return f"Couldn't read CPU usage: {e}"

    def get_ram_usage(self) -> str:
        """Returns RAM usage as used/total GB."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            used_gb = round(mem.used / (1024 ** 3), 1)
            total_gb = round(mem.total / (1024 ** 3), 1)
            percent = mem.percent
            return f"RAM usage is {percent} percent — {used_gb} GB used out of {total_gb} GB."
        except Exception as e:
            return f"Couldn't read RAM usage: {e}"

    # ── Power Controls ────────────────────────────────────────────────

    def shutdown(self) -> str:
        """Shuts down the computer after a 10-second delay. Call only after confirmation."""
        os.system("shutdown /s /t 10")
        return "Shutting down in 10 seconds. Say Hey NOVA cancel shutdown to abort."

    def cancel_shutdown(self) -> str:
        os.system("shutdown /a")
        return "Shutdown cancelled."

    def restart(self) -> str:
        """Restarts the computer after a 10-second delay. Call only after confirmation."""
        os.system("shutdown /r /t 10")
        return "Restarting in 10 seconds."

    def sleep(self) -> str:
        """Puts the computer to sleep."""
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Putting the computer to sleep."

    def lock_screen(self) -> str:
        """Locks the Windows screen immediately."""
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked."
