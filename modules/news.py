"""
MODULE 6 — Space & Science News
=================================
Fetches NASA Astronomy Picture of the Day (APOD) and reads the
title and explanation via TTS. Also provides offline science facts
as a fallback when the API is unavailable.

Tech: requests, NASA Open API (APOD endpoint — free, DEMO_KEY works)
API Key: NASA_API_KEY from .env
Output: Formatted news/fact string → TTS engine
"""

import os
import random
import re
import requests


# 20 offline science facts used as fallback when the NASA API is unavailable
SCIENCE_FACTS = [
    "A day on Venus is longer than a year on Venus. It takes 243 Earth days to rotate once, but only 225 Earth days to orbit the Sun.",
    "Honey never spoils. Archaeologists have found 3,000-year-old honey in Egyptian tombs that was still edible.",
    "The human brain generates about 20 watts of electrical power — enough to light a dim LED bulb.",
    "Light from the Sun takes about 8 minutes and 20 seconds to reach Earth.",
    "Neutron stars are so dense that a teaspoon of their material would weigh about 10 million tonnes.",
    "Octopuses have three hearts, blue blood, and nine brains — one central brain and one in each arm.",
    "The observable universe contains an estimated 2 trillion galaxies.",
    "A single bolt of lightning is five times hotter than the surface of the Sun.",
    "Water can exist in all three states — solid, liquid, and gas — simultaneously at its triple point.",
    "DNA from a single human cell, if stretched out, would be about 2 metres long.",
    "The speed of light in a vacuum is exactly 299,792,458 metres per second.",
    "Sharks are older than trees. Sharks have existed for around 450 million years, while trees emerged about 350 million years ago.",
    "The Milky Way galaxy completes one rotation every 225–250 million years — called a galactic year.",
    "An electron has no known size — it is a point particle with zero radius.",
    "There are more possible iterations of a game of chess than there are atoms in the observable universe.",
    "Bananas are slightly radioactive because they contain potassium-40.",
    "Sound travels about 4 times faster through water than through air.",
    "The Great Wall of China is NOT visible from space with the naked eye — a common myth.",
    "1 day on Mercury is 59 Earth days long, but a Mercury year is only 88 Earth days.",
    "The human stomach gets a new lining roughly every 4 to 5 days to protect itself from its own acid.",
]


class NewsModule:
    APOD_URL = "https://api.nasa.gov/planetary/apod"

    def __init__(self, config: dict = None):
        self.api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
        self._last_apod_cache: str = ""  # Cache last successful APOD result

    def get_nasa_apod(self) -> str:
        """
        Fetches NASA's Astronomy Picture of the Day.
        Extracts the title and first 3 sentences of the explanation.
        Falls back to cached result → science fact on error.
        """
        params = {"api_key": self.api_key}

        try:
            resp = requests.get(self.APOD_URL, params=params, timeout=6)
            resp.raise_for_status()
            data = resp.json()

            title       = data.get("title", "Today's Space Story")
            explanation = data.get("explanation", "")
            date        = data.get("date", "")

            # Extract first 3 sentences using a simple regex
            sentences = re.split(r'(?<=[.!?])\s+', explanation.strip())
            summary = " ".join(sentences[:3])

            result = f"NASA's Astronomy Picture of the Day for {date}: {title}. {summary}"
            self._last_apod_cache = result  # Cache for offline fallback
            return result

        except requests.exceptions.ConnectionError:
            if self._last_apod_cache:
                return "I'm offline, but here's the last NASA update I fetched: " + self._last_apod_cache
            return "I can't reach NASA right now. Here's a science fact instead: " + self.get_science_fact()
        except requests.exceptions.Timeout:
            return "NASA's servers are slow right now. Here's a science fact: " + self.get_science_fact()
        except Exception as e:
            print(f"[News] NASA APOD error: {e}")
            return "Here's an interesting science fact: " + self.get_science_fact()

    def get_science_fact(self) -> str:
        """Returns a random science fact from the offline list."""
        return random.choice(SCIENCE_FACTS)
