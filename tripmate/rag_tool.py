from __future__ import annotations

import math
import re
from pathlib import Path
from typing import List


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?", text.lower())


def _normalize_chunk(chunk: str) -> str:
    return " ".join(_tokenize(chunk))


class DestinationRAG:
    def __init__(self, data_dir: str | Path = "tripmate-destination-data"):
        self.data_dir = Path(data_dir)
        self.chunks = self._load_chunks()

    @staticmethod
    def _is_valid_destination_chunk(chunk_text: str) -> bool:
        lower = chunk_text.lower()
        blacklist = (
            "tripmate destination data pack",
            "this folder contains",
            "destination guide documents",
            "search_destination_guide",
        )
        if any(term in lower for term in blacklist):
            return False
        if lower.startswith("city: readme"):
            return False
        return True

    @staticmethod
    def _format_chunk(city_name: str, section: str) -> str:
        cleaned = section.strip()
        city_label = f"City: {city_name}"

        cleaned = re.sub(r"(?is)^.*?destination guide\s*:\s*.*?\n+", "", cleaned, count=1)
        cleaned = re.sub(rf"(?im)^\s*(?:city\s*:\s*)?{re.escape(city_name)}\s*$", "", cleaned)
        cleaned = re.sub(rf"(?i)city\s*:\s*{re.escape(city_name)}", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*note\s*:\s*", "", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        if not cleaned:
            return city_label
        return f"{city_label}\n\n{cleaned}".strip()

    def _load_chunks(self) -> list[dict]:
        chunks = []
        for file_path in sorted(self.data_dir.glob("*.txt")):
            city_name = file_path.stem.title()
            if file_path.name.lower().startswith("readme") or city_name.lower() == "readme":
                continue

            text = file_path.read_text(encoding="utf-8")
            sections = [section.strip() for section in re.split(r"\n\s*\n", text) if section.strip()]
            for section in sections:
                if not self._is_valid_destination_chunk(section):
                    continue

                combined = self._format_chunk(city_name, section)
                chunks.append({"city": city_name, "text": combined})
        return chunks

    def _similarity(self, query: str, chunk_text: str) -> float:
        query_tokens = _tokenize(query)
        chunk_tokens = _tokenize(chunk_text)
        if not query_tokens or not chunk_tokens:
            return 0.0

        query_counter = {}
        chunk_counter = {}
        city_name = re.search(r"\b[A-Za-z]+\b", chunk_text)

        for token in query_tokens:
            query_counter[token] = query_counter.get(token, 0) + 1
        for token in chunk_tokens:
            chunk_counter[token] = chunk_counter.get(token, 0) + 1

        boosted_terms = {"tokyo": 2.5, "bangkok": 2.5, "barcelona": 2.5, "reykjavik": 2.5,
                         "packing": 2.0, "pack": 2.0, "visa": 1.8, "safety": 1.8,
                         "customs": 1.8, "weather": 1.8, "winter": 1.5, "summer": 1.5, "december": 1.5}

        weighted_tokens = 0.0
        for token, count in query_counter.items():
            boost = boosted_terms.get(token, 1.0)
            weighted_tokens += count * chunk_counter.get(token, 0) * boost

        dot_product = sum(query_counter.get(token, 0) * chunk_counter.get(token, 0) for token in set(query_counter) | set(chunk_counter))
        query_norm = math.sqrt(sum(value * value for value in query_counter.values()))
        chunk_norm = math.sqrt(sum(value * value for value in chunk_counter.values()))
        if query_norm == 0 or chunk_norm == 0:
            return 0.0

        base_similarity = dot_product / (query_norm * chunk_norm)
        return base_similarity + (weighted_tokens / max(query_norm * chunk_norm, 1.0))

    def search(self, query: str, top_k: int = 3) -> List[str]:
        if not query or not str(query).strip():
            raise ValueError("Search query cannot be empty.")

        target_city = None
        city_match = re.search(r"\b(bangkok|tokyo|barcelona|reykjavik)\b", query, flags=re.IGNORECASE)
        if city_match:
            target_city = city_match.group(1).title()

        scored = []
        for chunk in self.chunks:
            if not self._is_valid_destination_chunk(chunk["text"]):
                continue
            if target_city and chunk["city"].lower() != target_city.lower():
                continue
            score = self._similarity(query, chunk["text"])
            scored.append((score, chunk["city"], chunk["text"]))

        if not scored and target_city:
            for chunk in self.chunks:
                if not self._is_valid_destination_chunk(chunk["text"]):
                    continue
                score = self._similarity(query, chunk["text"])
                scored.append((score, chunk["city"], chunk["text"]))

        scored.sort(key=lambda item: item[0], reverse=True)

        selected = []
        seen_cities = set()
        for _, city_name, text in scored:
            if city_name in seen_cities:
                continue
            if not _normalize_chunk(text):
                continue
            selected.append(text)
            seen_cities.add(city_name)
            if len(selected) >= top_k:
                break

        if not selected:
            raise ValueError("No relevant destination information found.")
        return selected


def search_destination_guide(query: str) -> List[str]:
    base_dir = Path(__file__).resolve().parent.parent / "tripmate-destination-data"
    rag = DestinationRAG(data_dir=base_dir)
    return rag.search(query)
