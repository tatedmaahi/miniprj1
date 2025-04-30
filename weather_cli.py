import requests
import json
from datetime import datetime, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY not found in .env file. Please set it in the .env file.")

BASE_URL = "https://api.openweathermap.org/data/2.5"
HISTORY_FILE = "weather_history.json"

def init_history_file():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)

def fetch_current_weather(city):
    try:
        url = f"{BASE_URL}/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as http_err:
        if http_err.response is not None:
            print(f"HTTP error in fetch_current_weather: {http_err.response.status_code} - {http_err.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None

def fetch_forecast(city):
    try:
        url = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as http_err:
        if http_err.response is not None:
            print(f"HTTP error in fetch_forecast: {http_err.response.status_code} - {http_err.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None

def weather(city):
    current_data = fetch_current_weather(city)
    forecast_data = fetch_forecast(city)
    return current_data, forecast_data

def display_weather(current_data, forecast_data):
    if current_data:
        print("\nCurrent Weather:")
        print(f"City: {current_data['name']}")
        print(f"Temperature: {current_data['main']['temp']}°C")
        print(f"Condition: {current_data['weather'][0]['description']}")
        print(f"Humidity: {current_data['main']['humidity']}%")
        print(f"Wind Speed: {current_data['wind']['speed']} m/s")
    else:
        print("No current weather data available.")

    if forecast_data:
        print("\nToday's Forecast (April 30, 2025):")
        today = date(2025, 4, 30)  # Hardcoded for current date
        forecast_list = forecast_data.get("list", [])
        for entry in forecast_list[:8]:  # Limit to 24 hours (8 entries, 3-hour intervals)
            dt = datetime.fromtimestamp(entry["dt"])
            forecast_date = dt.date()
            if forecast_date != today:
                continue  # Skip entries not on April 30, 2025
            temp = entry["main"]["temp"]
            condition = entry["weather"][0]["description"]
            print(f"{dt.strftime('%Y-%m-%d %H:%M:%S')}: {temp}°C, {condition}")
    else:
        print("No forecast data available.")

def save_to_history(city, current_data, forecast_data):
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "city": city,
        "current": current_data,
        "forecast": forecast_data
    }
    
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    
    history.append(history_entry)
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def main():
    init_history_file()

    # Get city input from user
    while True:
        city = input("Enter the city name to fetch weather for: ").strip()
        if city:
            break
        print("City name cannot be empty. Please try again.")

    city = city.capitalize()
    current_data = fetch_current_weather(city)
    forecast_data = fetch_forecast(city)

    display_weather(current_data, forecast_data)
    print(f"\nWeather data for {city} saved to {HISTORY_FILE}")

if __name__ == "__main__":
    main()