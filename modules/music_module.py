"""
MODULE 12 — Music / Spotify Player
=================================
Automates Spotify playback. Uses PyAutoGUI for keyboard automation 
(works for Free and Premium accounts without an API key) as the 
primary method, and Spotipy API as a fallback if credentials exist.

Tech: pyautogui, subprocess, spotipy
Output: Confirmation string → TTS engine
"""

import os
import time
import subprocess
import threading
try:
    import pyautogui
except ImportError:
    pyautogui = None

import spotipy
from spotipy.oauth2 import SpotifyOAuth

class MusicModule:
    def __init__(self, config: dict = None):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        self.sp = None
        self._init_api()

    def _init_api(self):
        """Initializes Spotipy client if credentials are present."""
        if self.client_id and self.client_secret:
            try:
                auth_manager = SpotifyOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    scope="user-modify-playback-state user-read-playback-state"
                )
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
            except Exception as e:
                print(f"[MusicModule] Spotipy init failed: {e}")
                self.sp = None

    def handle_music_command(self, original: str, entities: dict, speak_func, listen_func) -> str:
        """
        Extracts song name from the command, attempts to play it via keyboard automation,
        and then asks the user if they want to adjust the volume.
        """
        import re
        song_name = ""
        
        # Extract song name from commands like "play [song] on spotify" or "open spotify and play [song]"
        match = re.search(r"play\s+(.*?)(?:\s+on\s+spotify)?$", original, re.IGNORECASE)
        if match:
            song_name = match.group(1).strip()
            
        if not song_name:
            # Fallback to named entity if available
            song_name = entities.get("name", "")
            
        if not song_name:
            speak_func("What song would you like me to play?")
            song_name = listen_func().strip()
            if song_name.lower().startswith("play "):
                song_name = song_name[5:].strip()
                
            if not song_name:
                return "Playback cancelled. No song provided."

        speak_func(f"Opening Spotify and playing {song_name}.")
        
        # Run playback in a background thread so it doesn't block the UI
        threading.Thread(target=self._play_song_automation, args=(song_name,), daemon=True).start()
        
        time.sleep(4) # Give it time to start playing
        
        # Interactive volume prompt
        speak_func("Should I increase the volume?")
        response = listen_func().lower()
        if "yes" in response or "yeah" in response:
            if pyautogui:
                for _ in range(5):
                    pyautogui.press("volumeup")
            return "Volume increased."
        elif "no" in response or "down" in response or "decrease" in response:
            if pyautogui:
                for _ in range(5):
                    pyautogui.press("volumedown")
            return "Volume adjusted."
            
        return "Playing your music."

    def _play_song_automation(self, song_name: str):
        """Uses PyAutoGUI to open Spotify and search for the song."""
        if not pyautogui:
            print("[MusicModule] pyautogui not installed, trying API fallback...")
            self._play_song_api(song_name)
            return

        try:
            # Launch Spotify using environment variable
            spotify_path = os.path.expandvars("%APPDATA%\\Spotify\\Spotify.exe")
            if os.path.exists(spotify_path):
                subprocess.Popen([spotify_path])
            else:
                # Try opening via Windows search if path not found
                pyautogui.press("win")
                time.sleep(0.5)
                pyautogui.write("spotify", interval=0.05)
                time.sleep(0.5)
                pyautogui.press("enter")
            
            # Wait for Spotify to load and come to foreground
            time.sleep(4.0)
            
            # Ctrl+L to focus search bar
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            
            # Type song name
            pyautogui.write(song_name, interval=0.05)
            time.sleep(2.0) # Wait for search results to fully load
            
            # Navigate to the top result and play
            # Using down arrow focuses the 'Top Result' section reliably
            pyautogui.press('down')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(0.5)
            pyautogui.press('enter')
            
            # Also press tab and enter just in case it requires a button click
            pyautogui.press('tab')
            pyautogui.press('enter')
            
        except Exception as e:
            print(f"[MusicModule] Automation failed: {e}")
            self._play_song_api(song_name)

    def _play_song_api(self, song_name: str):
        """Fallback: uses Spotify API to play the song."""
        if not self.sp:
            print("[MusicModule] Spotify API not configured.")
            return
            
        try:
            results = self.sp.search(q=song_name, limit=1, type='track')
            tracks = results.get('tracks', {}).get('items', [])
            if tracks:
                track_uri = tracks[0]['uri']
                # Requires an active device. If none active, this might throw an error
                self.sp.start_playback(uris=[track_uri])
                print(f"[MusicModule] Started API playback for {tracks[0]['name']}")
            else:
                print(f"[MusicModule] Song '{song_name}' not found on Spotify via API.")
        except spotipy.exceptions.SpotifyException as e:
            print(f"[MusicModule] Spotipy playback error: {e}")
        except Exception as e:
            print(f"[MusicModule] API playback error: {e}")
