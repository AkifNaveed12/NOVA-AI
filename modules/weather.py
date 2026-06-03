"""
MODULE 5 — Weather Information
================================
Fetches real-time weather for any city using OpenWeatherMap API.
Default city is Wah Cantt (configurable via config.json).
NLP extracts the city entity from the voice command.

Tech: requests, OpenWeatherMap API (free tier, 60 calls/min)
API Key: OPENWEATHER_API_KEY from .env
Config: default_city, units in config.json
Output: Formatted weather string → TTS engine
"""

import os
import requests


class WeatherModule:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, config: dict = None):
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        cfg = (config or {}).get("weather", {})
        self.default_city = cfg.get("default_city", "Wah Cantt")
        self.units = cfg.get("units", "metric")  # metric = °C, imperial = °F

    def get_weather(self, city: str = None) -> str:
        """
        Fetches real-time weather for the given city.
        Falls back to default_city from config when city is None or empty.

        Returns a natural-language string ready for TTS.
        """
        city = (city or self.default_city).strip()

        # Try OpenWeatherMap first if a key is configured
        if self.api_key and "your_key" not in self.api_key and len(self.api_key) > 10:
            result = self._get_openweather(city)
            if result:
                return result

        # Free fallback: wttr.in (no API key required)
        return self._get_wttr(city)

    def _get_openweather(self, city: str):
        """Fetch from OpenWeatherMap. Returns None on auth/not-found errors so caller falls back."""
        params = {"q": city, "appid": self.api_key, "units": self.units}
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=5)
            if resp.status_code in (401, 404):
                return None
            resp.raise_for_status()
            data = resp.json()
            temp        = round(data["main"]["temp"])
            feels_like  = round(data["main"]["feels_like"])
            humidity    = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            wind_speed  = data["wind"]["speed"]
            city_name   = data["name"]
            country     = data["sys"]["country"]
            unit_symbol = "°C" if self.units == "metric" else "°F"
            wind_unit   = "m/s" if self.units == "metric" else "mph"
            return (
                f"The weather in {city_name}, {country} is currently {description}. "
                f"Temperature is {temp}{unit_symbol}, feels like {feels_like}{unit_symbol}. "
                f"Humidity is {humidity}%, wind speed {wind_speed} {wind_unit}."
            )
        except Exception:
            return None

    def _get_wttr(self, city: str) -> str:
        """Fetch from wttr.in — completely free, no API key needed."""
        try:
            url = f"https://wttr.in/{requests.utils.quote(city)}?format=j1"
            resp = requests.get(url, timeout=6,
                                headers={"User-Agent": "NOVA-AI/1.0"})
            if resp.status_code != 200:
                return f"Sorry, I couldn't get the weather for {city} right now."
            data = resp.json()
            current = data["current_condition"][0]
            area    = data["nearest_area"][0]

            temp_c      = current["temp_C"]
            feels_c     = current["FeelsLikeC"]
            humidity    = current["humidity"]
            wind_kmh    = current["windspeedKmph"]
            description = current["weatherDesc"][0]["value"]
            city_name   = area["areaName"][0]["value"]
            country     = area["country"][0]["value"]

            unit_symbol = "°C"
            if self.units == "imperial":
                temp_c    = current.get("temp_F", temp_c)
                feels_c   = current.get("FeelsLikeF", feels_c)
                unit_symbol = "°F"

            return (
                f"The weather in {city_name}, {country} is currently {description}. "
                f"Temperature is {temp_c}{unit_symbol}, feels like {feels_c}{unit_symbol}. "
                f"Humidity is {humidity}%, wind {wind_kmh} km/h."
            )
        except requests.exceptions.ConnectionError:
            return "I can't reach the weather service. Please check your internet connection."
        except requests.exceptions.Timeout:
            return "The weather service took too long to respond. Please try again."
        except Exception as e:
            print(f"[Weather] wttr.in error: {e}")
            return f"Sorry, I couldn't get the weather for {city} right now."
