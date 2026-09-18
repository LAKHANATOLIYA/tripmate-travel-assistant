from tripmate.agent import TripMateAgent


def test_full_multi_tool_flow():
    agent = TripMateAgent()
    answer = agent.answer("What should I pack for Tokyo in December?")

    assert "Tokyo" in answer
    assert "pack" in answer.lower()
    assert "December" in answer or "winter" in answer.lower()
