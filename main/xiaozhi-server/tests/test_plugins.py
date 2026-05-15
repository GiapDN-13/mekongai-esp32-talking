"""Tests for plugin functions — get_weather parsing with mocked HTTP."""

from unittest.mock import patch, MagicMock
from plugins_func.register import Action, ActionResponse


SAMPLE_WTTR_RESPONSE = {
    "current_condition": [{
        "temp_C": "32",
        "FeelsLikeC": "35",
        "humidity": "70",
        "windspeedKmph": "15",
        "lang_vi": [{"value": "Nắng nhẹ"}],
        "weatherDesc": [{"value": "Partly cloudy"}],
    }],
    "nearest_area": [{
        "areaName": [{"value": "Hanoi"}],
    }],
    "weather": [
        {
            "date": "2025-01-15",
            "maxtempC": "34",
            "mintempC": "26",
            "hourly": [
                {},
                {"lang_vi": [{"value": "Mưa rào"}]},
                {},
            ],
        }
    ],
}


class TestGetWeather:
    @patch("core.utils.cache.manager.cache_manager")
    @patch("requests.get")
    def test_successful_weather_fetch(self, mock_get, mock_cache):
        mock_cache.get.return_value = None
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_WTTR_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from plugins_func.functions.get_weather import get_weather
        result = get_weather(conn=MagicMock(), location="Hanoi")

        assert isinstance(result, ActionResponse)
        assert result.action == Action.REQLLM
        assert "Hanoi" in result.result
        assert "32°C" in result.result
        assert "70%" in result.result

    @patch("core.utils.cache.manager.cache_manager")
    @patch("requests.get")
    def test_weather_http_failure(self, mock_get, mock_cache):
        mock_cache.get.return_value = None
        mock_get.side_effect = Exception("Network error")

        from plugins_func.functions.get_weather import get_weather
        result = get_weather(conn=MagicMock(), location="Hanoi")

        assert isinstance(result, ActionResponse)
        assert result.action == Action.REQLLM
        assert "Không thể" in result.result

    @patch("core.utils.cache.manager.cache_manager")
    def test_weather_cache_hit(self, mock_cache):
        mock_cache.get.return_value = "Cached weather report"

        from plugins_func.functions.get_weather import get_weather
        result = get_weather(conn=MagicMock(), location="Hanoi")

        assert result.result == "Cached weather report"

    @patch("core.utils.cache.manager.cache_manager")
    @patch("requests.get")
    def test_weather_forecast_included(self, mock_get, mock_cache):
        mock_cache.get.return_value = None
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_WTTR_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from plugins_func.functions.get_weather import get_weather
        result = get_weather(conn=MagicMock(), location="Hanoi")

        assert "Dự báo" in result.result
        assert "26~34°C" in result.result
