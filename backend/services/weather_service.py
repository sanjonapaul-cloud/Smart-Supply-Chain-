# weather_service.py

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    raise ValueError("WEATHER_API_KEY not found in environment variables")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city_name):

    if not isinstance(city_name, str) or not city_name.strip():
        return {"error": "Invalid city name"}

    try:
        params = {
            "q": city_name,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        return {
            "temperature_celsius": data["main"]["temp"],
            "condition": data["weather"][0]["main"],
            "humidity": data["main"]["humidity"],
            "wind_speed_mps": data["wind"]["speed"]
        }

    except requests.exceptions.HTTPError:
        return {"error": "City not found or invalid API request"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}

    except (KeyError, IndexError):
        return {"error": "Unexpected response format"}