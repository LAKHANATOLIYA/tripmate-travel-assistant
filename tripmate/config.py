from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


@dataclass
class Settings:
    llm_provider: str = "deterministic_tool_router"
    weather_data_source: str = "mock"
    rag_backend: str = "in_memory_similarity"


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parent.parent
    dotenv_values = _load_dotenv(project_root / ".env")

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", dotenv_values.get("LLM_PROVIDER", "deterministic_tool_router")),
        weather_data_source=os.getenv("WEATHER_DATA_SOURCE", dotenv_values.get("WEATHER_DATA_SOURCE", "mock")),
        rag_backend=os.getenv("RAG_BACKEND", dotenv_values.get("RAG_BACKEND", "in_memory_similarity")),
    )


settings = load_settings()
