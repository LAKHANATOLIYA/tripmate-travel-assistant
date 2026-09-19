# TripMate AI Travel Assistant

A small, clean agentic travel assistant built for the TripMate technical assessment. The solution includes:

- destination-aware RAG search across local travel data
- weather lookup by city and month
- multi-tool reasoning for packing and travel advice
- scope awareness for unsupported queries
- structured logging and tests

## Project structure

```text
tripmate/
  __init__.py
  __main__.py
  agent.py
  logging_setup.py
  rag_tool.py
  weather_tool.py

docs/
  architecture.md

tests/
  test_agent.py
  test_integration.py
  test_rag_tool.py
  test_weather_tool.py

tripmate-destination-data/
  bangkok.txt
  barcelona.txt
  README.txt
  reykjavik.txt
  tokyo.txt
```

## Setup

1. Clone or open the project folder.
2. Ensure Python 3.10+ is installed.
3. Create a virtual environment if needed.
4. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run locally

### Interactive CLI

```bash
python -m tripmate
```

### Direct script run

```bash
python tripmate/agent.py
```

## Architecture overview

See [docs/architecture.md](docs/architecture.md) for the architecture diagram.

## Tool schemas used by the agent

### 1) `search_destination_guide(query: str) -> List[str]`

Purpose:
- retrieves the most relevant travel information chunks from the destination dataset

Inputs:
- natural-language question or topic

Output:
- a list of relevant text chunks, ranked by similarity

### 2) `get_weather_forecast(city: str, date_or_month: str) -> dict`

Purpose:
- returns a basic weather summary for a city and month

Example output:

```python
{
  "conditions": "cold and dry, with crisp winter air",
  "temp_range_c": [3, 10]
}
```

## Example runs and traces

### Example 1: single-tool destination query

Input:

```text
What are the visa rules for Bangkok?
```

Trace:

```text
Selected tools: ['destination_guide']
Calling destination guide tool.
Destination guide returned 1 relevant chunk.
```

Output:

```text
Destination guidance:
City: Bangkok

DESTINATION GUIDE: BANGKOK, THAILAND
```

### Example 2: multi-tool packing query

Input:

```text
What should I pack for Tokyo in December?
```

Trace:

```text
Selected tools: ['destination_guide', 'weather']
Calling destination guide tool.
Calling weather tool.
Weather result: {'conditions': 'cold and dry, with crisp winter air', 'temp_range_c': [3, 10]}
```

Output:

```text
Here is a practical packing suggestion based on the destination guide and weather:

Destination guidance:
City: Tokyo

DESTINATION GUIDE: TOKYO, JAPAN

Weather for Tokyo in December: cold and dry, with crisp winter air (temperature range: 3°C to 10°C).
```

### Example 3: weather-only query

Input:

```text
How cold is Reykjavik in January?
```

Trace:

```text
Selected tools: ['weather']
Calling weather tool.
```

Output:

```text
Weather for Reykjavik in January: very cold and windy with short daylight hours (temperature range: -6°C to 1°C).
```

### Example 4: out-of-scope query

Input:

```text
Please book my flight to Paris.
```

Trace:

```text
Request involves booking or reservations.
```

Output:

```text
I can help with travel questions about destination info, visa rules, local customs, packing advice, safety, and weather. I cannot book flights or handle reservations.
```

## Design decisions and assumptions

- The destination knowledge base is local and static, so an in-memory similarity search is enough for this assessment.
- The weather data is intentionally implemented as a small mock table to keep the project reliable and easy to test.
- The orchestration logic is intentionally implemented as a deterministic tool router, because this project is meant to be transparent, explainable, and testable without requiring an external LLM provider.
- The agent is built to be transparent: every tool decision and relevant reasoning step is logged.

## Known limitations

- The weather tool is a mock lookup, not a live external API integration.
- The RAG tool uses a simple similarity approach rather than embeddings + FAISS/Chroma.
- The dataset is limited to four cities and simplified travel notes.
- The tool router is rule-based and works best for the assessment scenarios listed in the prompt.

## Scalability considerations

### If the knowledge base grows from 4 cities to several hundred

- Move from a simple in-memory search to a vector database such as FAISS or Chroma.
- Precompute embeddings offline for each chunk.
- Add metadata filters such as city, category, and language.
- If a hosted LLM or external provider is introduced later, the same tool interfaces can be preserved while swapping the planner implementation.

### Avoiding redundant tool calls

- Cache repeated query embeddings or final answer results by normalized query text.
- Deduplicate similar queries before dispatching tools.
- Use a lightweight LRU cache for frequent travel questions.

### Reducing LLM/API cost at higher query volume

- Keep the router deterministic and local when possible.
- Only call the LLM for final answer synthesis when needed.
- Batch repeated requests or precompute summaries for common destinations.

### Keeping tool-selection latency low as the tool list grows

- Use lightweight intent detection first, then call only relevant tools.
- Keep tool metadata short and structured.
- Prefer rule-based classification or a small classification model over expensive vector-heavy matching per query.

## Testing

The project includes automated tests for:

- RAG retrieval relevance
- weather tool behavior
- tool selection logic
- end-to-end multi-tool flow

Run:

```bash
pytest -q
```

## Verification

This project was validated with the following test result:

```text
11 passed in 0.11s
```

## Future improvements

- Integrate a real weather API like Open-Meteo.
- Add true embedding-based retrieval with FAISS or ChromaDB.
- Add a real LLM provider for final answer synthesis.
- Improve the router with a small intent-classification model.
- Add richer logging and telemetry for production-like observability.

## Final note

This solution is intentionally simple, explainable, and testable so it can serve as a strong assessment submission without unnecessary complexity.
