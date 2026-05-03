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

# TODO: implement WeatherModule class with get_weather(city) method
