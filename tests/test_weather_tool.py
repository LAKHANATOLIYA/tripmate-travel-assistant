import pytest

from tripmate.weather_tool import get_weather_forecast


def test_get_weather_forecast_known_city_and_month():
    result = get_weather_forecast("Tokyo", "December")

    assert "conditions" in result
    assert "temp_range_c" in result
    assert isinstance(result["temp_range_c"], list)
    assert len(result["temp_range_c"]) == 2


def test_get_weather_forecast_supports_bangkok_august():
    result = get_weather_forecast("Bangkok", "August")

    assert "conditions" in result
    assert result["temp_range_c"] == [28, 34]


def test_get_weather_forecast_invalid_city():
    with pytest.raises(ValueError):
        get_weather_forecast("Atlantis", "December")
