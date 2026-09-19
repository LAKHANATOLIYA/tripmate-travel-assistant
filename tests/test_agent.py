import importlib

import pytest

from tripmate import config
from tripmate.agent import TripMateAgent


def test_provider_configuration_can_be_overridden(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock_llm")
    monkeypatch.setenv("WEATHER_DATA_SOURCE", "live_api")
    importlib.reload(config)
    assert config.settings.llm_provider == "mock_llm"
    assert config.settings.weather_data_source == "live_api"
    importlib.reload(config)


def test_tool_selection_single_tool():
    agent = TripMateAgent()
    selected = agent.select_tools("What are the visa rules for Bangkok?")
    assert selected == ["destination_guide"]


def test_tool_selection_destination_only_for_visa_query():
    agent = TripMateAgent()
    selected = agent.select_tools("What are the visa rules for Bangkok?")
    assert selected == ["destination_guide"]


def test_tool_selection_weather_only_for_weather_query():
    agent = TripMateAgent()
    selected = agent.select_tools("How cold is Reykjavik in January?")
    assert selected == ["weather"]


def test_tool_selection_multi_tool():
    agent = TripMateAgent()
    selected = agent.select_tools("What should I pack for Tokyo in December?")
    assert selected == ["destination_guide", "weather"]


def test_tool_selection_out_of_scope():
    agent = TripMateAgent()
    selected = agent.select_tools("Please book my flight to Paris")
    assert selected == []


def test_empty_query_raises_value_error():
    agent = TripMateAgent()
    with pytest.raises(ValueError):
        agent.select_tools("   ")
