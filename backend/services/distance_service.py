import os

import requests
from dotenv import load_dotenv

from utils.logger import log_error, log_info

load_dotenv()

API_KEY = (os.getenv("DISTANCE_API_KEY") or "").strip()
URL_GEOJSON = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
URL_JSON = "https://api.openrouteservice.org/v2/directions/driving-car"


def _fallback_distance(error_message: str, status: str = "fallback"):
    return {
        "distance_km": 0,
        "duration_min": 0,
        "route_path": [],
        "status": status,
        "error": error_message,
    }


def _extract_route_points(geometry):
    route_path = []

    if isinstance(geometry, dict):
        geometry = geometry.get("coordinates", [])

    if isinstance(geometry, list):
        for point in geometry:
            if (
                isinstance(point, list)
                and len(point) >= 2
                and isinstance(point[0], (int, float))
                and isinstance(point[1], (int, float))
            ):
                route_path.append([float(point[0]), float(point[1])])

    return route_path


def _parse_distance_response(data):
    if isinstance(data, dict) and isinstance(data.get("features"), list) and data["features"]:
        feature = data["features"][0]
        summary = feature["properties"]["summary"]
        geometry = feature.get("geometry", {}).get("coordinates", [])
        return summary, _extract_route_points(geometry)

    if isinstance(data, dict) and isinstance(data.get("routes"), list) and data["routes"]:
        route = data["routes"][0]
        summary = route["summary"]
        geometry = route.get("geometry", [])
        return summary, _extract_route_points(geometry)

    raise KeyError("No route data found")


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

    attempts = [
        {
            "label": "geojson-post-auth-header",
            "method": "POST",
            "url": URL_GEOJSON,
            "kwargs": {"json": body, "headers": headers, "timeout": 8},
        },
        {
            "label": "json-post-auth-header",
            "method": "POST",
            "url": URL_JSON,
            "kwargs": {"json": body, "headers": headers, "timeout": 8},
        },
        {
            "label": "json-get-api-key-query",
            "method": "GET",
            "url": URL_JSON,
            "kwargs": {
                "params": {
                    "api_key": API_KEY,
                    "start": f"{source_coords[0]},{source_coords[1]}",
                    "end": f"{destination_coords[0]},{destination_coords[1]}",
                },
                "timeout": 8,
            },
        },
    ]

    errors = []

    for attempt in attempts:
        try:
            response = requests.request(
                method=attempt["method"],
                url=attempt["url"],
                **attempt["kwargs"],
            )
            response.raise_for_status()

            data = response.json()
            summary, route_path = _parse_distance_response(data)

            distance_km = round(float(summary["distance"]) / 1000, 2)
            duration_min = round(float(summary["duration"]) / 60, 2)

            result = {
                "distance_km": distance_km,
                "duration_min": duration_min,
                "route_path": route_path,
                "status": "success",
                "error": None,
            }
            log_info(
                "Distance service success: "
                f"distance_km={result['distance_km']} duration_min={result['duration_min']} "
                f"via={attempt['label']}"
            )
            return result

        except requests.exceptions.RequestException as e:
            errors.append(f"{attempt['label']}: {str(e)}")
            continue

        except (KeyError, IndexError, TypeError, ValueError) as e:
            errors.append(f"{attempt['label']}: Invalid response format: {str(e)}")
            continue
        except Exception as e:
            errors.append(f"{attempt['label']}: {str(e)}")
            continue

    message = "Request failed: " + " | ".join(errors)
    log_error(f"Distance service request error: {message}")
    return _fallback_distance(message)


if __name__ == "__main__":
    result = get_distance([88.36, 22.57], [77.10, 28.70])
    print("RESULT:", result)
