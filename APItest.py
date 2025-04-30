import unittest
from unittest.mock import patch, Mock
import json
import os
from weather_cli import fetch_current_weather, fetch_forecast, init_history_file, save_to_history, HISTORY_FILE

SAMPLE_CURRENT_WEATHER = {
    "name": "Chennai",
    "main": {"temp": 15, "humidity": 70},
    "weather": [{"description": "light rain"}],
    "wind": {"speed": 4.5}
}

SAMPLE_FORECAST = {
    "list": [
        {
            "dt": 1746019200,  # timestamp for 2025-04-30 00:00:00
            "main": {"temp": 14},
            "weather": [{"description": "cloudy"}]
        },
    ]
}

class TestWeatherCLI(unittest.TestCase):

    @patch('weather_cli.requests.get')
    def test_fetch_current_weather_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_CURRENT_WEATHER
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_current_weather("Chennai")
        self.assertEqual(result['name'], "Chennai")
        self.assertEqual(result['main']['temp'], 15)

    @patch('weather_cli.requests.get')
    def test_fetch_forecast_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_FORECAST
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_forecast("Chennai")
        self.assertEqual(result['list'][0]['main']['temp'], 14)

    @patch('weather_cli.requests.get')
    def test_fetch_weather_http_error(self, mock_get):
        from requests.exceptions import HTTPError

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("Mocked HTTP error")
        mock_get.return_value = mock_response

        result = fetch_current_weather("InvalidCity")
        self.assertIsNone(result)

    def test_init_history_file_creates_file(self):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        init_history_file()
        self.assertTrue(os.path.exists(HISTORY_FILE))
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            self.assertEqual(data, [])

    def test_save_to_history_appends_data(self):
        init_history_file()
        city = "Chennai"
        save_to_history(city, SAMPLE_CURRENT_WEATHER, SAMPLE_FORECAST)
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        self.assertTrue(any(entry["city"] == city for entry in history))

if __name__ == '__main__':
    unittest.main()
