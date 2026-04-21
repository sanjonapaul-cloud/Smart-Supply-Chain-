import requests
import os
from dotenv import load_dotenv

from utils.logger import log_error, log_info

load_dotenv()

API_KEY = os.getenv("TOMTOM_API_KEY")

BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"


def _fallback_traffic(error_message: str, status: str = "fallback"):
    return {
        "current_speed": 0,
        "free_flow_speed": 0,
        "congestion_level": "Unknown",
        "status": status,
        "error": error_message,
    }


def get_traffic(lat, lon):
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        message = "Invalid coordinates"
        log_error(f"Traffic service validation failed: {message}")
        return _fallback_traffic(message)

    if not API_KEY:
        message = "TOMTOM_API_KEY not configured"
        log_error(message)
        return _fallback_traffic(message)

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

        if current_speed is None or free_flow_speed in (None, 0):
            message = "Invalid API response"
            log_error(f"Traffic service parse failed: {message}")
            return _fallback_traffic(message)

        ratio = current_speed / free_flow_speed

        if ratio >= 0.8:
            congestion = "Low"
        elif ratio >= 0.5:
            congestion = "Moderate"
        else:
            congestion = "High"

        log_info(
            "Traffic service success: "
            f"current_speed={current_speed} free_flow_speed={free_flow_speed} congestion={congestion}"
        )

        return {
            "current_speed": current_speed,
            "free_flow_speed": free_flow_speed,
            "congestion_level": congestion,
            "status": "success",
            "error": None,
        }

    except requests.exceptions.RequestException as e:
        message = f"Request failed: {str(e)}"
        log_error(f"Traffic service request error: {message}")
        return _fallback_traffic(message)

    except Exception as e:
        message = str(e)
        log_error(f"Traffic service unexpected error: {message}")
        return _fallback_traffic(message, status="error")


if __name__ == "__main__":
    print(get_traffic(22.57, 88.36))