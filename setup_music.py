"""
setup_music.py — NOVA AI Music Asset Setup
==========================================
Downloads royalty-free background music tracks used in the
NOVA self-introduction sequence (Module 21 — personality.py).

All tracks are from Pixabay (royalty-free, no attribution required).
Run this ONCE before first use:

    python setup_music.py

Tracks downloaded:
  suspense.mp3     — low drone / tension underscore
  emotional.mp3    — soft piano / heartfelt underscore
  joke_sting.mp3   — comedy sting / ba-dum-tss
  epic_rise.mp3    — cinematic swell / power reveal

Output directory: assets/music/
"""

import os
import requests

MUSIC_DIR = os.path.join("assets", "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

# Royalty-free tracks from Pixabay CDN
# You can replace these with any .mp3 URLs or local files.
TRACKS = {
    "suspense.mp3": (
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bab.mp3"
    ),
    "emotional.mp3": (
        "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"
    ),
    "joke_sting.mp3": (
        "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bede17.mp3"
    ),
    "epic_rise.mp3": (
        "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a73467.mp3"
    ),
}


def download(name: str, url: str) -> bool:
    dest = os.path.join(MUSIC_DIR, name)
    if os.path.exists(dest):
        print(f"  ✓ {name} already exists — skipping")
        return True
    print(f"  ↓ Downloading {name}...", end=" ", flush=True)
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        print(f"done ({len(r.content)//1024} KB)")
        return True
    except Exception as e:
        print(f"FAILED — {e}")
        print(f"    → Intro will run silently for this segment.")
        return False


if __name__ == "__main__":
    print("\nNOVA Music Setup")
    print("=" * 40)
    results = {name: download(name, url) for name, url in TRACKS.items()}
    print("\nSummary:")
    for name, ok in results.items():
        print(f"  {'✓' if ok else '✗'} {name}")
    print("\nDone. Run 'python modules/personality.py' to preview the introduction.\n")