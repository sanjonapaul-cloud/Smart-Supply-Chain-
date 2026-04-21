# weather_service.py

import requests

# Replace with your actual OpenWeather API key
API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city_name):
    """
    Fetch weather details for a given city.

    Args:
        city_name (str): Name of the city

    Returns:
        dict: Weather details (temperature in Celsius, condition, humidity, wind speed)
              OR error message in case of failure
    """
    try:
        params = {
            "q": city_name,
            "appid": API_KEY
        }

        response = requests.get(BASE_URL, params=params)

        # Handle HTTP errors
        if response.status_code != 200:
            return {
                "error": "City not found or API request failed"
            }

        data = response.json()

        # Extract required fields
        temperature_kelvin = data["main"]["temp"]
        temperature_celsius = round(temperature_kelvin - 273.15, 2)

        weather_condition = data["weather"][0]["main"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return {
            "temperature": temperature_celsius,
            "condition": weather_condition,
            "humidity": humidity,
            "wind_speed": wind_speed
        }

    except requests.exceptions.RequestException:
        return {
            "error": "API request failed due to network issue"
        }
    except KeyError:
        return {
            "error": "Unexpected response format"
        }