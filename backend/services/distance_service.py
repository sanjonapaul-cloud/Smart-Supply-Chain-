import os

import requests
from dotenv import load_dotenv

from utils.logger import log_error, log_info

load_dotenv()

API_KEY = os.getenv("DISTANCE_API_KEY")
URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


def _fallback_distance(error_message: str, status: str = "fallback"):
    return {
        "distance_km": 0,
        "duration_min": 0,
        "route_path": [],
        "status": status,
        "error": error_message,
    }


def get_distance(source_coords, destination_coords):
    if (
        not isinstance(source_coords, list)
        or not isinstance(destination_coords, list)
        or len(source_coords) != 2
        or len(destination_coords) != 2
        or not all(isinstance(value, (int, float)) for value in source_coords)
        or not all(isinstance(value, (int, float)) for value in destination_coords)
    ):
        message = "Invalid coordinates format. Use [longitude, latitude]."
        log_error(f"Distance service validation failed: {message}")
        return _fallback_distance(message)

    if not API_KEY:
        message = "DISTANCE_API_KEY not configured"
        log_error(message)
        return _fallback_distance(message)

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "coordinates": [
            source_coords,
            destination_coords,
        ]
    }

    try:
        response = requests.post(URL, json=body, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json()

        feature = data["features"][0]
        summary = feature["properties"]["summary"]
        geometry = feature["geometry"]["coordinates"]

        route_path = []
        if isinstance(geometry, list):
            for point in geometry:
                if (
                    isinstance(point, list)
                    and len(point) >= 2
                    and isinstance(point[0], (int, float))
                    and isinstance(point[1], (int, float))
                ):
                    route_path.append([float(point[0]), float(point[1])])

        distance_km = round(summary["distance"] / 1000, 2)
        duration_min = round(summary["duration"] / 60, 2)

        result = {
            "distance_km": distance_km,
            "duration_min": duration_min,
            "route_path": route_path,
            "status": "success",
            "error": None,
        }
        log_info(
            "Distance service success: "
            f"distance_km={result['distance_km']} duration_min={result['duration_min']}"
        )
        return result

    except requests.exceptions.RequestException as e:
        message = f"Request failed: {str(e)}"
        log_error(f"Distance service request error: {message}")
        return _fallback_distance(message)

    except (KeyError, IndexError) as e:
        message = f"Invalid response format from API: {str(e)}"
        log_error(f"Distance service parse error: {message}")
        return _fallback_distance(message)

    except Exception as e:
        message = str(e)
        log_error(f"Distance service unexpected error: {message}")
        return _fallback_distance(message, status="error")


if __name__ == "__main__":
    result = get_distance([88.36, 22.57], [77.10, 28.70])
    print("RESULT:", result)
