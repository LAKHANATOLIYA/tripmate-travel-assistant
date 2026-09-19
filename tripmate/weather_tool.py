from __future__ import annotations

import re
from typing import Dict, List

WEATHER_DATA: Dict[str, Dict[str, Dict[str, object]]] = {
    "tokyo": {
        "december": {"conditions": "cold and dry, with crisp winter air", "temp_range_c": [3, 10]},
        "january": {"conditions": "cold and dry, with occasional clear skies", "temp_range_c": [1, 8]},
        "february": {"conditions": "cool and dry, pleasant for city walks", "temp_range_c": [2, 10]},
        "march": {"conditions": "cool with springlike weather", "temp_range_c": [6, 15]},
        "july": {"conditions": "hot and humid with frequent rain showers", "temp_range_c": [25, 31]},
        "august": {"conditions": "hot and humid with tropical summer weather", "temp_range_c": [26, 32]},
        "summer": {"conditions": "hot and humid with occasional rain", "temp_range_c": [22, 31]},
    },
    "bangkok": {
        "december": {"conditions": "warm and comfortable with lower humidity", "temp_range_c": [24, 32]},
        "january": {"conditions": "cooler and more comfortable than the hot season", "temp_range_c": [25, 33]},
        "february": {"conditions": "warm and dry, generally pleasant", "temp_range_c": [26, 34]},
        "march": {"conditions": "hot and humid before the monsoon", "temp_range_c": [28, 35]},
        "july": {"conditions": "very hot and humid with daily rain showers", "temp_range_c": [28, 34]},
        "august": {"conditions": "very hot and humid with tropical downpours", "temp_range_c": [28, 34]},
        "summer": {"conditions": "very hot and humid", "temp_range_c": [28, 36]},
    },
    "barcelona": {
        "december": {"conditions": "mild and cool, with occasional rain", "temp_range_c": [8, 15]},
        "january": {"conditions": "cool and crisp, often clear", "temp_range_c": [7, 14]},
        "february": {"conditions": "cool and slightly wetter than other months", "temp_range_c": [8, 16]},
        "march": {"conditions": "mild with spring warmth developing", "temp_range_c": [10, 18]},
        "july": {"conditions": "hot and crowded with long sunny days", "temp_range_c": [24, 30]},
        "august": {"conditions": "hot and crowded, especially in peak summer", "temp_range_c": [25, 31]},
        "summer": {"conditions": "hot and crowded, especially in July and August", "temp_range_c": [25, 30]},
    },
    "reykjavik": {
        "december": {"conditions": "very cold, windy, and dark with snow possible", "temp_range_c": [-5, 2]},
        "january": {"conditions": "very cold and windy with short daylight hours", "temp_range_c": [-6, 1]},
        "february": {"conditions": "cold, windy, and icy with possible snow", "temp_range_c": [-5, 2]},
        "march": {"conditions": "cold and variable with improving daylight", "temp_range_c": [-3, 4]},
        "july": {"conditions": "mild weather with long daylight and occasional rain", "temp_range_c": [9, 15]},
        "august": {"conditions": "mild weather with long daylight and cool evenings", "temp_range_c": [8, 14]},
        "summer": {"conditions": "mild weather with long daylight and occasional rain", "temp_range_c": [9, 15]},
    },
}

MONTH_MAP = {
    "jan": "january", "january": "january",
    "feb": "february", "february": "february",
    "mar": "march", "march": "march",
    "apr": "april", "april": "april",
    "may": "may",
    "jun": "june", "june": "june",
    "jul": "july", "july": "july",
    "aug": "august", "august": "august",
    "sep": "september", "sept": "september", "september": "september",
    "oct": "october", "october": "october",
    "nov": "november", "november": "november",
    "dec": "december", "december": "december",
}


def normalize_city(city: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z\s]", "", city.strip().lower())
    return " ".join(cleaned.split())


def normalize_month(date_or_month: str) -> str:
    cleaned = date_or_month.strip().lower()
    if cleaned in MONTH_MAP:
        return MONTH_MAP[cleaned]
    if cleaned in {"summer", "winter", "spring", "autumn", "fall"}:
        return cleaned
    return cleaned


def get_weather_forecast(city: str, date_or_month: str) -> dict:
    if not city or not str(city).strip():
        raise ValueError("City name is required.")
    if not date_or_month or not str(date_or_month).strip():
        raise ValueError("Date or month is required.")

    city_key = normalize_city(city)
    month_key = normalize_month(date_or_month)

    if city_key not in WEATHER_DATA:
        raise ValueError(f"Weather data is not available for '{city}'.")

    city_weather = WEATHER_DATA[city_key]
    if month_key not in city_weather:
        raise ValueError(
            f"Weather data for '{city}' is not available for '{date_or_month}'."
        )

    return dict(city_weather[month_key])
