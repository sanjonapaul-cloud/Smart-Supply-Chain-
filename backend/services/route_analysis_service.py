"""Route analysis orchestration service.

This module combines distance, traffic, and weather signals into one response
and derives a route risk level.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple


# Allow running this file directly: `python backend/services/route_analysis_service.py`
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))


distance_import_error = None
traffic_import_error = None
weather_import_error = None


try:
    from services.distance_service import get_distance
except Exception as exc:  # pragma: no cover - environment-dependent import
    distance_import_error = str(exc)

    def get_distance(source_coords: List[float], destination_coords: List[float]) -> Dict[str, Any]:
        return {"error": f"distance_service import failed: {distance_import_error}"}


try:
    from services.traffic_service import get_traffic
except Exception as exc:  # pragma: no cover - environment-dependent import
    traffic_import_error = str(exc)

    def get_traffic(lat: float, lon: float) -> Dict[str, Any]:
        return {"error": f"traffic_service import failed: {traffic_import_error}"}


try:
    from services.weather_service import get_weather
except Exception as exc:  # pragma: no cover - environment-dependent import
    weather_import_error = str(exc)

    def get_weather(city_name: str) -> Dict[str, Any]:
        return {"error": f"weather_service import failed: {weather_import_error}"}


def _safe_call(func: Callable[..., Dict[str, Any]], *args: Any) -> Dict[str, Any]:
    """Execute a service function and convert runtime errors into response data."""
    try:
        result = func(*args)
        if isinstance(result, dict):
            return result
        return {"error": "Invalid service response format"}
    except Exception as exc:  # pragma: no cover - defensive safety net
        return {"error": str(exc)}


def _extract_source_lat_lon(source_coords: List[float]) -> Tuple[float | None, float | None]:
    """Extract latitude and longitude for traffic API from [lon, lat] coordinates."""
    if (
        not isinstance(source_coords, list)
        or len(source_coords) != 2
        or not isinstance(source_coords[0], (int, float))
        or not isinstance(source_coords[1], (int, float))
    ):
        return None, None

    lon = float(source_coords[0])
    lat = float(source_coords[1])
    return lat, lon


def calculate_risk(traffic_data: Dict[str, Any], weather_data: Dict[str, Any]) -> str:
    """Calculate route risk using traffic and weather conditions.

    Rules:
    - High congestion -> High risk
    - Rain/Thunderstorm weather -> High risk
    - Moderate congestion -> Moderate risk
    - Otherwise -> Low risk
    """
    if not isinstance(traffic_data, dict) or not isinstance(weather_data, dict):
        return "High"

    if traffic_data.get("error") or weather_data.get("error"):
        # Conservative fallback when upstream data cannot be trusted.
        return "High"

    congestion_level = str(traffic_data.get("congestion_level", "")).strip().lower()
    weather_condition = str(weather_data.get("condition", "")).strip().lower()

    if congestion_level == "high":
        return "High"

    if weather_condition in {"rain", "thunderstorm"}:
        return "High"

    if congestion_level == "moderate":
        return "Moderate"

    return "Low"


def get_route_analysis(
    source_coords: List[float],
    destination_coords: List[float],
    city_name: str,
) -> Dict[str, Any]:
    """Get complete route analysis with distance, traffic, weather, and risk."""
    distance_data = _safe_call(get_distance, source_coords, destination_coords)

    lat, lon = _extract_source_lat_lon(source_coords)
    if lat is None or lon is None:
        traffic_data = {"error": "Invalid source coordinates format. Use [longitude, latitude]."}
    else:
        traffic_data = _safe_call(get_traffic, lat, lon)

    weather_data = _safe_call(get_weather, city_name)

    risk_level = calculate_risk(traffic_data, weather_data)

    return {
        "distance": distance_data,
        "traffic": traffic_data,
        "weather": weather_data,
        "risk_level": risk_level,
    }


if __name__ == "__main__":
    # Example usage: [longitude, latitude]
    source = [88.36, 22.57]        # Kolkata
    destination = [77.10, 28.70]   # Delhi
    city = "Kolkata"

    analysis = get_route_analysis(source, destination, city)
    print(analysis)