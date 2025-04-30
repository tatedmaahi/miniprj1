# Weather Dashboard CLI

A command-line Python tool that fetches current weather and 24-hour forecasts for any city using the OpenWeatherMap API. It also maintains a local history of past queries.

## Features

- Current weather conditions (temperature, humidity, wind, etc.)
- 24-hour forecast (next 8 data points, 3-hour interval)
- JSON-based history logging
- Easy-to-use CLI interface
- Environment variable support for API key security

## Requirements

- Python 3.7+
- [OpenWeatherMap API Key](https://openweathermap.org/api)
- Internet connection

## Installation

1. Clone the repository or download the script.
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate        # On Windows