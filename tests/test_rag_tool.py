from pathlib import Path

from tripmate.rag_tool import DestinationRAG


def test_search_destination_guide_returns_relevant_chunks():
    data_dir = Path(__file__).resolve().parents[1] / "tripmate-destination-data"
    rag = DestinationRAG(data_dir=data_dir)

    results = rag.search("what should I pack for Tokyo in winter?")

    assert len(results) > 0
    assert any("TOKYO" in chunk.upper() or "PACKING" in chunk.upper() for chunk in results)


def test_search_destination_guide_excludes_readme_content():
    data_dir = Path(__file__).resolve().parents[1] / "tripmate-destination-data"
    rag = DestinationRAG(data_dir=data_dir)

    results = rag.search("what should I pack for Tokyo in winter?")

    assert not any("tripmate destination data pack" in chunk.lower() for chunk in results)
    assert not any("this folder contains" in chunk.lower() for chunk in results)


def test_search_destination_guide_deduplicates_city_label():
    data_dir = Path(__file__).resolve().parents[1] / "tripmate-destination-data"
    rag = DestinationRAG(data_dir=data_dir)

    results = rag.search("what should I pack for Tokyo in winter?")

    assert sum("city: tokyo" in chunk.lower() for chunk in results) <= 1


def test_search_destination_guide_filters_to_requested_city():
    data_dir = Path(__file__).resolve().parents[1] / "tripmate-destination-data"
    rag = DestinationRAG(data_dir=data_dir)

    results = rag.search("what should I pack for Tokyo in December?")

    assert results
    assert all("tokyo" in chunk.lower() for chunk in results)
    assert not any("bangkok" in chunk.lower() for chunk in results)
    assert not any("reykjavik" in chunk.lower() for chunk in results)
