"""
MODULE 8 — Web Automation & Browser Control
=============================================
Opens websites by voice and performs Selenium browser interactions.
Simple URL opens use webbrowser (fast). Complex interactions
(like, comment, scroll, YouTube search) use Selenium with Chrome.
Site registry loaded from config/sites.json.

Tech: webbrowser (built-in), selenium, rapidfuzz, sites.json
Output: Confirmation string → TTS engine
"""

import json
import os
import webbrowser
import urllib.parse
from rapidfuzz import process, fuzz


class WebAutomation:
    def __init__(self, config: dict = None):
        # Load sites registry
        sites_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "sites.json")
        try:
            with open(sites_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.sites = data.get("sites", [])
        except Exception as e:
            print(f"[Web] Error loading sites.json: {e}")
            self.sites = []

        # Build a flat lookup: alias → {name, url}
        self._alias_map = {}
        for site in self.sites:
            name = site["name"]
            url = site["url"]
            self._alias_map[name.lower()] = {"name": name, "url": url}
            for alias in site.get("aliases", []):
                self._alias_map[alias.lower()] = {"name": name, "url": url}

        # Selenium driver (lazy init)
        self.driver = None

    def open_site(self, name: str) -> str:
        """
        Opens a website by name. Uses fuzzy matching against sites.json.
        Falls back to webbrowser for speed (no Selenium overhead).
        """
        if not name or not name.strip():
            return "Which website would you like me to open?"

        query = name.lower().strip()

        # Direct match first
        if query in self._alias_map:
            entry = self._alias_map[query]
            webbrowser.open(entry["url"])
            return f"Opening {entry['name']}."

        # Fuzzy match against all aliases
        all_aliases = list(self._alias_map.keys())
        match = process.extractOne(query, all_aliases, scorer=fuzz.WRatio, score_cutoff=65)

        if match:
            matched_alias, score, _ = match
            entry = self._alias_map[matched_alias]
            webbrowser.open(entry["url"])
            return f"Opening {entry['name']}."

        # Unknown site — try opening as a raw URL or Google search
        if "." in query:
            url = query if query.startswith("http") else f"https://{query}"
            webbrowser.open(url)
            return f"Opening {query}."

        return f"I don't know a website called '{name}'. You can say open google dot com or add it to sites.json."

    def is_site_known(self, name: str) -> bool:
        """Helper to check if a site name matches known sites above the threshold."""
        if not name or not name.strip():
            return False
        query = name.lower().strip()
        if query in self._alias_map:
            return True
        all_aliases = list(self._alias_map.keys())
        if not all_aliases:
            return False
        match = process.extractOne(query, all_aliases, scorer=fuzz.WRatio, score_cutoff=65)
        return bool(match)

    def search_youtube(self, query: str, play: bool = False) -> str:
        """Searches YouTube for the given query. If play is True, extracts the first video ID and plays it directly."""
        import urllib.request
        import urllib.parse
        import re
        
        if not query or not query.strip():
            return "What would you like me to search on YouTube?"

        encoded = urllib.parse.quote_plus(query.strip())
        
        if play:
            try:
                html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={encoded}")
                video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
                if video_ids:
                    url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                    webbrowser.open(url)
                    return f"Playing {query} on YouTube."
            except Exception as e:
                print(f"[WebAutomation] YouTube play error: {e}")
                
        # Fallback to normal search page
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        return f"Searching YouTube for: {query}."

    def search_google(self, query: str) -> str:
        """Searches Google for the given query."""
        if not query or not query.strip():
            return "What would you like me to search for?"

        encoded = urllib.parse.quote_plus(query.strip())
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        return f"Searching Google for: {query}."

    def _get_driver(self):
        """Lazily initializes a Selenium Chrome driver."""
        if self.driver is None:
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options

                opts = Options()
                opts.add_argument("--start-maximized")
                opts.add_experimental_option("detach", True)  # Keep browser open
                self.driver = webdriver.Chrome(options=opts)
                self.driver.implicitly_wait(5)
            except Exception as e:
                print(f"[Web] Selenium driver init failed: {e}")
                return None
        return self.driver

    def scroll_down(self, amount: int = 3) -> str:
        """Scrolls the active Selenium browser window down."""
        driver = self._get_driver()
        if not driver:
            return "I couldn't control the browser for scrolling."
        for _ in range(amount):
            driver.execute_script("window.scrollBy(0, 500);")
        return f"Scrolled down {amount} steps."

    def scroll_up(self, amount: int = 3) -> str:
        """Scrolls the active Selenium browser window up."""
        driver = self._get_driver()
        if not driver:
            return "I couldn't control the browser for scrolling."
        for _ in range(amount):
            driver.execute_script("window.scrollBy(0, -500);")
        return f"Scrolled up {amount} steps."

    def close_browser(self):
        """Closes the Selenium browser cleanly."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def get_site_list(self) -> list:
        """Returns all registered site names."""
        return [s["name"] for s in self.sites]
