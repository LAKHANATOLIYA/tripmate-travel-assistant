# TripMate Architecture

```mermaid
flowchart LR
    User[User Query] --> Agent[TripMate Agent / Orchestrator]
    Agent -->|Select tool(s)| Router{Tool selection logic}
    Router --> RAG[Destination Knowledge Tool\nsearch_destination_guide]
    Router --> Weather[Weather Forecast Tool\nget_weather_forecast]
    RAG --> Vector[(In-memory destination knowledge store)]
    Weather --> Data[(City + month weather lookup)]
    Vector --> RAG
    Data --> Weather
    Agent --> LLM[LLM / answer synthesis layer]
    LLM --> Response[Final natural-language response]
```

## Flow

1. User sends a natural-language question.
2. The agent decides whether the request maps to destination knowledge, weather, both, or none.
3. The selected tool(s) run and return structured context.
4. The orchestrator combines results into one final, coherent answer.
5. Logging records tool choices, arguments, and reasoning trace for debugging and review.
