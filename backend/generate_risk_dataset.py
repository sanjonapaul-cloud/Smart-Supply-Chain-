from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATASET_PATH = Path(__file__).resolve().parent / "data" / "route_risk_dataset.csv"


def _sample_weather_condition(rng: np.random.Generator) -> str:
    return rng.choice(["Clear", "Clouds", "Rain", "Thunderstorm"], p=[0.42, 0.26, 0.24, 0.08])


def _label_risk(congestion_ratio: float, condition: str, wind_speed: float) -> str:
    if congestion_ratio < 0.5 or condition in {"Rain", "Thunderstorm"} or wind_speed > 11:
        return "High"
    if congestion_ratio < 0.75:
        return "Moderate"
    return "Low"


def generate_dataset(rows: int = 1000, random_seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    records = []

    for _ in range(rows):
        distance_km = float(np.round(rng.uniform(5, 2500), 2))

        free_flow_speed = float(np.round(rng.uniform(35, 110), 2))
        congestion_ratio = float(np.round(rng.uniform(0.25, 1.0), 3))
        current_speed = float(np.round(max(5.0, free_flow_speed * congestion_ratio), 2))

        duration_min = float(np.round((distance_km / max(current_speed, 8.0)) * 60, 2))

        condition = _sample_weather_condition(rng)
        if condition == "Clear":
            temperature_celsius = float(np.round(rng.uniform(18, 38), 2))
            humidity = float(np.round(rng.uniform(30, 65), 2))
            wind_speed_mps = float(np.round(rng.uniform(1, 8), 2))
        elif condition == "Clouds":
            temperature_celsius = float(np.round(rng.uniform(14, 34), 2))
            humidity = float(np.round(rng.uniform(45, 80), 2))
            wind_speed_mps = float(np.round(rng.uniform(2, 9), 2))
        elif condition == "Rain":
            temperature_celsius = float(np.round(rng.uniform(10, 30), 2))
            humidity = float(np.round(rng.uniform(70, 96), 2))
            wind_speed_mps = float(np.round(rng.uniform(4, 13), 2))
        else:  # Thunderstorm
            temperature_celsius = float(np.round(rng.uniform(8, 28), 2))
            humidity = float(np.round(rng.uniform(75, 99), 2))
            wind_speed_mps = float(np.round(rng.uniform(7, 18), 2))

        risk_level = _label_risk(congestion_ratio, condition, wind_speed_mps)

        records.append(
            {
                "distance_km": distance_km,
                "duration_min": duration_min,
                "current_speed": current_speed,
                "free_flow_speed": free_flow_speed,
                "temperature_celsius": temperature_celsius,
                "humidity": humidity,
                "wind_speed_mps": wind_speed_mps,
                "congestion_ratio": congestion_ratio,
                "risk_level": risk_level,
            }
        )

    return pd.DataFrame.from_records(records)


def save_dataset(rows: int = 1000) -> Path:
    dataset = generate_dataset(rows=rows)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(DATASET_PATH, index=False)
    print(f"Saved dataset with {len(dataset)} rows -> {DATASET_PATH}")
    return DATASET_PATH


if __name__ == "__main__":
    save_dataset(rows=1000)
