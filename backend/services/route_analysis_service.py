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

from utils.logger import log_error, log_info


distance_import_error = None
traffic_import_error = None
weather_import_error = None


try:
    from services.distance_service import get_distance
except Exception as exc:  # pragma: no cover - environment-dependent import
    distance_import_error = str(exc)

    def get_distance(source_coords: List[float], destination_coords: List[float]) -> Dict[str, Any]:
        return {
            "distance_km": 0,
            "duration_min": 0,
            "route_path": [],
            "status": "error",
            "error": f"distance_service import failed: {distance_import_error}",
        }


try:
    from services.traffic_service import get_traffic
except Exception as exc:  # pragma: no cover - environment-dependent import
    traffic_import_error = str(exc)

    def get_traffic(lat: float, lon: float) -> Dict[str, Any]:
        return {
            "current_speed": 0,
            "free_flow_speed": 0,
            "congestion_level": "Unknown",
            "status": "error",
            "error": f"traffic_service import failed: {traffic_import_error}",
        }


try:
    from services.weather_service import get_weather
except Exception as exc:  # pragma: no cover - environment-dependent import
    weather_import_error = str(exc)

    def get_weather(city_name: str) -> Dict[str, Any]:
        return {
            "temperature_celsius": None,
            "condition": "Unavailable",
            "humidity": None,
            "wind_speed_mps": None,
            "status": "error",
            "error": f"weather_service import failed: {weather_import_error}",
        }


try:
    from services.ml_model import predict_risk
except Exception as exc:  # pragma: no cover - environment-dependent import
    ml_import_error = str(exc)

    def predict_risk(features: Dict[str, float]) -> str:
        raise RuntimeError(f"ml_model import failed: {ml_import_error}")


def _safe_call(func: Callable[..., Dict[str, Any]], *args: Any) -> Dict[str, Any]:
    """Execute a service function and convert runtime errors into response data."""
    try:
        result = func(*args)
        if isinstance(result, dict):
            return result
        return {"status": "error", "error": "Invalid service response format"}
    except Exception as exc:  # pragma: no cover - defensive safety net
        return {"status": "error", "error": str(exc)}


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

    congestion_level = str(traffic_data.get("congestion_level", "")).strip().lower()
    weather_condition = str(weather_data.get("condition", "")).strip().lower()

    if congestion_level in {"", "unknown"} and weather_condition in {"", "unavailable"}:
        return "Moderate"

    if congestion_level == "high":
        return "High"

    if weather_condition in {"rain", "thunderstorm"}:
        return "High"

    if congestion_level == "moderate":
        return "Moderate"

    return "Low"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if number != number:  # NaN guard
            return default
        return number
    except (TypeError, ValueError):
        return default


def _build_ml_features(distance_data: Dict[str, Any], traffic_data: Dict[str, Any], weather_data: Dict[str, Any]) -> Dict[str, float]:
    current_speed = _to_float(traffic_data.get("current_speed"), 0.0)
    free_flow_speed = _to_float(traffic_data.get("free_flow_speed"), 0.0)
    congestion_ratio = current_speed / free_flow_speed if free_flow_speed > 0 else 0.0

    return {
        "distance_km": _to_float(distance_data.get("distance_km"), 0.0),
        "duration_min": _to_float(distance_data.get("duration_min"), 0.0),
        "current_speed": current_speed,
        "free_flow_speed": free_flow_speed,
        "temperature_celsius": _to_float(weather_data.get("temperature_celsius"), 0.0),
        "humidity": _to_float(weather_data.get("humidity"), 0.0),
        "wind_speed_mps": _to_float(weather_data.get("wind_speed_mps"), 0.0),
        "congestion_ratio": congestion_ratio,
    }


def _derive_status(*service_payloads: Dict[str, Any]) -> str:
    statuses = [str(payload.get("status", "success")).lower() for payload in service_payloads]

    if any(status == "error" for status in statuses):
        return "error"
    if any(status == "fallback" for status in statuses):
        return "fallback"
    return "success"


def get_route_analysis(
    source_coords: List[float],
    destination_coords: List[float],
    city_name: str,
) -> Dict[str, Any]:
    """Get complete route analysis with distance, traffic, weather, and risk."""
    distance_data = _safe_call(get_distance, source_coords, destination_coords)

    lat, lon = _extract_source_lat_lon(source_coords)
    if lat is None or lon is None:
        traffic_data = {
            "current_speed": 0,
            "free_flow_speed": 0,
            "congestion_level": "Unknown",
            "status": "fallback",
            "error": "Invalid source coordinates format. Use [longitude, latitude].",
        }
    else:
        traffic_data = _safe_call(get_traffic, lat, lon)

    weather_data = _safe_call(get_weather, city_name)

    ml_features = _build_ml_features(distance_data, traffic_data, weather_data)

    model_used = "ml"
    try:
        risk_level = predict_risk(ml_features)
    except Exception as exc:
        model_used = "fallback"
        risk_level = calculate_risk(traffic_data, weather_data)
        errors = [str(exc)]
        log_error(f"ML prediction failed, using fallback risk logic: {str(exc)}")
    else:
        errors = []

    status = _derive_status(distance_data, traffic_data, weather_data)

    for payload in (distance_data, traffic_data, weather_data):
        message = payload.get("error") if isinstance(payload, dict) else None
        if message:
            errors.append(str(message))

    if errors:
        log_error(f"Route analysis completed with issues: {' | '.join(errors)}")
    else:
        log_info(f"Route analysis success: risk_level={risk_level}")

    return {
        "distance": distance_data,
        "traffic": traffic_data,
        "weather": weather_data,
        "route_path": distance_data.get("route_path", []) if isinstance(distance_data, dict) else [],
        "risk_level": risk_level,
        "model": model_used,
        "status": status,
        "features": ml_features,
        "errors": errors,
    }


if __name__ == "__main__":
    # Example usage: [longitude, latitude]
    source = [88.36, 22.57]        # Kolkata
    destination = [77.10, 28.70]   # Delhi
    city = "Kolkata"

    analysis = get_route_analysis(source, destination, city)
    print(analysis)