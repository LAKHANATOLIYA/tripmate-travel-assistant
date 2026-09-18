from __future__ import annotations

import re
from typing import List

from .logging_setup import setup_logger
from .rag_tool import search_destination_guide
from .weather_tool import get_weather_forecast

logger = setup_logger("tripmate.agent")


class TripMateAgent:
    def __init__(self, data_dir=None):
        self.trace: list[dict] = []

    def select_tools(self, user_query: str) -> List[str]:
        if not user_query or not str(user_query).strip():
            raise ValueError("User query cannot be empty.")

        query = user_query.lower()
        out_of_scope_patterns = [
            "book my flight",
            "book a flight",
            "reserve a hotel",
            "book hotel",
            "purchase tickets",
            "book train",
            "rent a car",
            "flight booking",
            "hotel booking",
        ]
        if any(pattern in query for pattern in out_of_scope_patterns):
            self.trace.append({"decision": "out_of_scope", "reason": "Request involves booking or reservations."})
            return []

        city_match = re.search(r"\b(bangkok|tokyo|barcelona|reykjavik)\b", query)
        contains_packing = any(term in query for term in ["pack", "packing", "what to wear", "clothes", "bring"])
        contains_weather = any(term in query for term in ["weather", "temperature", "forecast", "cold", "hot", "rain", "snow", "month", "season"])
        contains_destination = any(term in query for term in ["visa", "customs", "safety", "entry", "best time", "local culture", "travel advice", "visit"])

        if contains_packing and city_match:
            self.trace.append({"decision": "multi_tool", "reason": "Packing advice depends on destination-specific guidance and weather."})
            return ["destination_guide", "weather"]

        if contains_weather and city_match:
            self.trace.append({"decision": "weather_only", "reason": "Query is weather-specific."})
            return ["weather"]

        if contains_destination and city_match:
            self.trace.append({"decision": "destination_only", "reason": "Query is destination information related."})
            return ["destination_guide"]

        if city_match:
            self.trace.append({"decision": "destination_only", "reason": "City-specific travel question detected."})
            return ["destination_guide"]

        self.trace.append({"decision": "no_tool", "reason": "No supported travel tool matches the request."})
        return []

    def _extract_city(self, query: str) -> str | None:
        match = re.search(r"\b(bangkok|tokyo|barcelona|reykjavik)\b", query, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1).title()

    def _extract_month(self, query: str) -> str | None:
        months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december"
        ]
        for month in months:
            if month in query.lower():
                return month.title()
        return None

    def answer(self, user_query: str) -> str:
        logger.info("Received user query: %s", user_query)
        tools = self.select_tools(user_query)
        logger.info("Selected tools: %s", tools)

        if not tools:
            response = (
                "I can help with travel questions about destination info, visa rules, local customs, "
                "packing advice, safety, and weather. I cannot book flights or handle reservations."
            )
            logger.info("Generated out-of-scope response.")
            return response

        context_parts = []
        city = self._extract_city(user_query)
        month = self._extract_month(user_query)

        if "destination_guide" in tools:
            logger.info("Calling destination guide tool.")
            try:
                results = search_destination_guide(user_query)
                context_parts.append("Destination guidance:\n" + "\n\n".join(results[:2]))
                logger.info("Destination guide returned %s relevant chunks.", len(results))
            except Exception as exc:
                logger.exception("Destination guide tool failed: %s", exc)
                context_parts.append("Destination guidance is unavailable right now.")

        if "weather" in tools:
            logger.info("Calling weather tool.")
            try:
                if city is None:
                    raise ValueError("Could not determine a valid city from the query.")
                weather_month = month or "December"
                weather = get_weather_forecast(city, weather_month)
                context_parts.append(
                    f"Weather for {city} in {weather_month}: {weather['conditions']} "
                    f"(temperature range: {weather['temp_range_c'][0]}°C to {weather['temp_range_c'][1]}°C)."
                )
                logger.info("Weather result: %s", weather)
            except Exception as exc:
                logger.exception("Weather tool failed: %s", exc)
                context_parts.append("Weather information is unavailable right now.")

        final_response = "\n\n".join(context_parts)
        if "pack" in user_query.lower() or "packing" in user_query.lower():
            final_response = (
                "Here is a practical packing suggestion based on the destination guide and weather:\n\n"
                + final_response
            )

        logger.info("Final response assembled.")
        return final_response


if __name__ == "__main__":
    agent = TripMateAgent()
    while True:
        query = input("TripMate> ")
        if not query.strip():
            break
        print(agent.answer(query))
