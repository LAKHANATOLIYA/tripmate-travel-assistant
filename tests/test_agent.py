import pytest

from tripmate.agent import TripMateAgent


def test_tool_selection_single_tool():
    agent = TripMateAgent()
    selected = agent.select_tools("What are the visa rules for Bangkok?")
    assert selected == ["destination_guide"]


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
