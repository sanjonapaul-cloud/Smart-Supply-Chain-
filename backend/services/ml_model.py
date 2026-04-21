from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "route_risk" / "model.pkl"

_cached_model = None
_cached_features: List[str] | None = None


def load_model() -> Tuple[object, List[str]]:
    global _cached_model
    global _cached_features

    if _cached_model is not None and _cached_features is not None:
        return _cached_model, _cached_features

    with open(MODEL_PATH, "rb") as model_file:
        model_data = pickle.load(model_file)

    _cached_model = model_data["model"]
    _cached_features = list(model_data["feature_columns"])
    return _cached_model, _cached_features


def _feature_vector(features: Dict[str, float], feature_columns: List[str]) -> np.ndarray:
    values = [float(features.get(column, 0.0)) for column in feature_columns]
    return np.array(values, dtype=float).reshape(1, -1)


def predict_risk(features: Dict[str, float]) -> str:
    model, feature_columns = load_model()
    vector = _feature_vector(features, feature_columns)
    frame = pd.DataFrame(vector, columns=feature_columns)
    prediction = model.predict(frame)[0]
    return str(prediction)


if __name__ == "__main__":
    example_features = {
        "distance_km": 120.0,
        "duration_min": 160.0,
        "current_speed": 32.0,
        "free_flow_speed": 80.0,
        "temperature_celsius": 29.0,
        "humidity": 88.0,
        "wind_speed_mps": 8.5,
        "congestion_ratio": 0.4,
    }

    try:
        print("Example prediction:", predict_risk(example_features))
    except Exception as exc:
        print("Model prediction failed:", str(exc))
