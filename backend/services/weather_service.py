# weather_service.py

import requests
import os
from dotenv import load_dotenv

from utils.logger import log_error, log_info

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def _fallback_weather(error_message: str, status: str = "fallback"):
    return {
        "temperature_celsius": None,
        "condition": "Unavailable",
        "humidity": None,
        "wind_speed_mps": None,
        "status": status,
        "error": error_message,
    }


def get_weather(city_name):
    if not isinstance(city_name, str) or not city_name.strip():
        message = "Invalid city name"
        log_error(f"Weather service validation failed: {message}")
        return _fallback_weather(message)

    if not API_KEY:
        message = "WEATHER_API_KEY not configured"
        log_error(message)
        return _fallback_weather(message)

    try:
        params = {
            "q": city_name,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        result = {
            "temperature_celsius": data["main"]["temp"],
            "condition": data["weather"][0]["main"],
            "humidity": data["main"]["humidity"],
            "wind_speed_mps": data["wind"]["speed"],
            "status": "success",
            "error": None,
        }
        log_info(
            "Weather service success: "
            f"condition={result['condition']} temp={result['temperature_celsius']}"
        )
        return result

    except requests.exceptions.HTTPError as exc:
        message = f"City not found or invalid API request: {str(exc)}"
        log_error(f"Weather service http error: {message}")
        return _fallback_weather(message)

    except requests.exceptions.RequestException as e:
        message = f"Network error: {str(e)}"
        log_error(f"Weather service request error: {message}")
        return _fallback_weather(message)

    except (KeyError, IndexError) as e:
        message = f"Unexpected response format: {str(e)}"
        log_error(f"Weather service parse error: {message}")
        return _fallback_weather(message)

    except Exception as e:
        message = str(e)
        log_error(f"Weather service unexpected error: {message}")
        return _fallback_weather(message, status="error")