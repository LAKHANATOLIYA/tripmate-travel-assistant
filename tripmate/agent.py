from __future__ import annotations

import json
import re
from typing import Any, List

from .config import load_settings
from .logging_setup import setup_logger
from .rag_tool import search_destination_guide
from .weather_tool import get_weather_forecast

logger = setup_logger("tripmate.agent")


class ToolPlanner:
    """A deterministic planner that ranks candidate tools based on explicit travel intent."""

    TOOL_METADATA = {
        "destination_guide": {
            "keywords": [
                "visa", "customs", "safety", "entry", "local culture", "travel advice",
                "best time", "what to do", "visit", "stay", "guide", "recommendation",
                "packing", "weather", "where to go", "tips",
            ],
            "description": "Destination knowledge and local travel guidance",
        },
        "weather": {
            "keywords": [
                "weather", "temperature", "forecast", "rain", "snow", "cold", "hot",
                "humid", "season", "month", "january", "february", "march", "april",
                "may", "june", "july", "august", "september", "october", "november", "december",
            ],
            "description": "Weather lookup by city and month or season",
        },
    }

    OUT_OF_SCOPE_PATTERNS = [
        "book my flight",
        "book a flight",
        "reserve a hotel",
        "book hotel",
        "purchase tickets",
        "book train",
        "rent a car",
        "flight booking",
        "hotel booking",
        "make a reservation",
    ]

    @staticmethod
    def _normalize_query(query: str) -> str:
        return re.sub(r"\s+", " ", str(query).strip().lower())

    @staticmethod
    def _extract_city(query: str) -> str | None:
        match = re.search(r"\b(bangkok|tokyo|barcelona|reykjavik)\b", query, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1).title()

    def plan(self, user_query: str) -> List[str]:
        if not user_query or not str(user_query).strip():
            raise ValueError("User query cannot be empty.")

        normalized = self._normalize_query(user_query)
        if any(pattern in normalized for pattern in self.OUT_OF_SCOPE_PATTERNS):
            return []

        city = self._extract_city(normalized)
        scores: dict[str, int] = {tool: 0 for tool in self.TOOL_METADATA}

        contains_weather_intent = any(
            token in normalized for token in [
                "weather", "temperature", "forecast", "cold", "hot", "humid", "rain",
                "snow", "winter", "summer", "month", "january", "february", "march",
                "april", "may", "june", "july", "august", "september", "october",
                "november", "december"
            ]
        )
        contains_destination_intent = any(
            token in normalized for token in [
                "visa", "customs", "safety", "entry", "local culture", "stay",
                "travel advice", "what to do", "visit", "tips", "guide", "recommendation"
            ]
        )
        contains_packing_intent = any(
            token in normalized for token in ["pack", "packing", "what to wear", "clothes", "bring"]
        )

        if contains_weather_intent:
            scores["weather"] += 4
        if contains_destination_intent:
            scores["destination_guide"] += 4
        if contains_packing_intent:
            scores["destination_guide"] += 2
            scores["weather"] += 3

        for tool_name, meta in self.TOOL_METADATA.items():
            for keyword in meta["keywords"]:
                if keyword in normalized:
                    scores[tool_name] += 1

        if city and contains_packing_intent:
            scores["destination_guide"] += 2
            scores["weather"] += 2
        elif city and contains_weather_intent:
            scores["weather"] += 2
        elif city and contains_destination_intent:
            scores["destination_guide"] += 2

        selected = [name for name, score in scores.items() if score > 0]
        if not selected:
            return []

        selected.sort(key=lambda name: scores[name], reverse=True)
        if len(selected) == 1 and scores[selected[0]] <= 1:
            return []
        return selected


class TripMateAgent:
    def __init__(self, data_dir=None):
        self.trace: list[dict[str, Any]] = []
        self.planner = ToolPlanner()
        self.settings = load_settings()

    def _append_trace(self, **payload: Any) -> None:
        self.trace.append(payload)

    def select_tools(self, user_query: str) -> List[str]:
        self.trace = []
        try:
            selected = self.planner.plan(user_query)
        except ValueError as exc:
            self._append_trace(event="validation_error", query=user_query, status="error", error=str(exc))
            raise

        self._append_trace(
            event="agent_decision",
            query=user_query,
            selected_tools=selected,
            status="success",
            decision_source=self.settings.llm_provider,
            routing_strategy="deterministic_tool_router",
        )
        return selected

    def _extract_city(self, query: str) -> str | None:
        match = re.search(r"\b(bangkok|tokyo|barcelona|reykjavik)\b", query, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1).title()

    def _extract_month(self, query: str) -> str | None:
        months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
        ]
        for month in months:
            if month in query.lower():
                return month.title()
        return None

    def _call_destination_tool(self, query: str) -> dict[str, Any]:
        args = {"query": query}
        try:
            results = search_destination_guide(query)
            self._append_trace(event="tool_call", tool="search_destination_guide", arguments=args, status="success", result_count=len(results))
            return {"status": "success", "results": results}
        except Exception as exc:
            self._append_trace(event="tool_call", tool="search_destination_guide", arguments=args, status="error", error=str(exc))
            return {"status": "error", "results": [], "error": str(exc)}

    def _call_weather_tool(self, city: str, month: str) -> dict[str, Any]:
        args = {"city": city, "date_or_month": month}
        try:
            forecast = get_weather_forecast(city, month)
            self._append_trace(event="tool_call", tool="get_weather_forecast", arguments=args, status="success", result=forecast)
            return {"status": "success", "forecast": forecast}
        except Exception as exc:
            self._append_trace(event="tool_call", tool="get_weather_forecast", arguments=args, status="error", error=str(exc))
            return {"status": "error", "forecast": None, "error": str(exc)}

    def answer(self, user_query: str) -> str:
        logger.info("Received user query: %s", user_query)
        tools = self.select_tools(user_query)
        logger.info("Selected tools: %s", tools)

        if not tools:
            response = (
                "I can help with travel questions about destination info, visa rules, local customs, "
                "packing advice, safety, and weather. I cannot book flights or handle reservations."
            )
            self._append_trace(event="final_response", status="success", response=response)
            logger.info("Generated out-of-scope response.")
            return response

        context_parts: list[str] = []
        city = self._extract_city(user_query)
        month = self._extract_month(user_query) or "December"

        if "destination_guide" in tools:
            destination_result = self._call_destination_tool(user_query)
            if destination_result["status"] == "success":
                results = destination_result["results"]
                context_parts.append("Destination guidance:\n" + "\n\n".join(results[:2]))
            else:
                context_parts.append("Destination guidance is unavailable right now.")

        if "weather" in tools:
            if city is None:
                weather_result = {"status": "error", "error": "Could not determine a valid city from the query."}
                self._append_trace(event="tool_call", tool="get_weather_forecast", arguments={"city": city, "date_or_month": month}, status="error", error="Could not determine a valid city from the query.")
            else:
                weather_result = self._call_weather_tool(city, month)

            if weather_result["status"] == "success":
                forecast = weather_result["forecast"]
                context_parts.append(
                    f"Weather for {city} in {month}: {forecast['conditions']} "
                    f"(temperature range: {forecast['temp_range_c'][0]}°C to {forecast['temp_range_c'][1]}°C)."
                )
            else:
                context_parts.append("Weather information is unavailable right now.")

        final_response = "\n\n".join(context_parts)
        if "pack" in user_query.lower() or "packing" in user_query.lower():
            final_response = (
                "Here is a practical packing suggestion based on the destination guide and weather:\n\n"
                + final_response
            )

        logger.info("Final response assembled.")
        self._append_trace(event="final_response", status="success", response=final_response)
        return final_response


if __name__ == "__main__":
    agent = TripMateAgent()
    while True:
        query = input("TripMate> ")
        if not query or not query.strip():
            print("Please enter a valid travel question.")
            continue
        if query.strip().lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        response = agent.answer(query)
        print(response)
        print("\nReasoning trace:")
        for step in agent.trace:
            print(json.dumps(step, ensure_ascii=False))
