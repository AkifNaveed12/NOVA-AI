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

        if not self.api_key or "your_key" in self.api_key:
            return "My weather service is not configured. Please add an OpenWeatherMap API key."

        params = {
            "q": city,
            "appid": self.api_key,
            "units": self.units,
        }

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=5)

            # 404 = city not found
            if resp.status_code == 404:
                return f"I couldn't find weather data for {city}. Please check the city name."

            # 401 = invalid API key
            if resp.status_code == 401:
                return "My weather API key is invalid. Please update it in the configuration."

            resp.raise_for_status()
            data = resp.json()

            temp        = round(data["main"]["temp"])
            feels_like  = round(data["main"]["feels_like"])
            humidity    = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            wind_speed  = data["wind"]["speed"]  # m/s for metric
            city_name   = data["name"]
            country     = data["sys"]["country"]

            unit_symbol = "°C" if self.units == "metric" else "°F"
            wind_unit   = "m/s" if self.units == "metric" else "mph"

            return (
                f"The weather in {city_name}, {country} is currently {description}. "
                f"Temperature is {temp}{unit_symbol}, feels like {feels_like}{unit_symbol}. "
                f"Humidity is {humidity}%, wind speed {wind_speed} {wind_unit}."
            )

        except requests.exceptions.ConnectionError:
            return "I can't reach the weather service. Please check your internet connection."
        except requests.exceptions.Timeout:
            return "The weather service took too long to respond. Please try again."
        except Exception as e:
            print(f"[Weather] Unexpected error: {e}")
            return f"Sorry, I couldn't get the weather for {city} right now."
