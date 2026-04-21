import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TOMTOM_API_KEY")

if not API_KEY:
    raise ValueError("TOMTOM_API_KEY not found in environment variables")

BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"


def get_traffic(lat, lon):

    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return {"error": "Invalid coordinates"}

    try:
        params = {
            "point": f"{lat},{lon}",
            "key": API_KEY
        }

        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        flow = data.get("flowSegmentData", {})

        current_speed = flow.get("currentSpeed")
        free_flow_speed = flow.get("freeFlowSpeed")

        if current_speed is None or free_flow_speed is None:
            return {"error": "Invalid API response"}

        ratio = current_speed / free_flow_speed

        if ratio >= 0.8:
            congestion = "Low"
        elif ratio >= 0.5:
            congestion = "Moderate"
        else:
            congestion = "High"

        return {
            "current_speed": current_speed,
            "free_flow_speed": free_flow_speed,
            "congestion_level": congestion
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(get_traffic(22.57, 88.36))