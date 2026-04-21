from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from generate_risk_dataset import generate_dataset


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "data" / "route_risk_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "route_risk" / "model.pkl"

FEATURE_COLUMNS = [
    "distance_km",
    "duration_min",
    "current_speed",
    "free_flow_speed",
    "temperature_celsius",
    "humidity",
    "wind_speed_mps",
    "congestion_ratio",
]


def load_or_create_dataset(rows: int = 1000) -> pd.DataFrame:
    if DATASET_PATH.exists():
        return pd.read_csv(DATASET_PATH)

    dataset = generate_dataset(rows=rows)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(DATASET_PATH, index=False)
    return dataset


def train_model(rows: int = 1000) -> Path:
    df = load_or_create_dataset(rows=rows)

    x = df[FEATURE_COLUMNS]
    y = df["risk_level"]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = accuracy_score(y_test, predictions)

    print(f"Accuracy: {accuracy:.4f}")
    print("Classification Report:")
    print(classification_report(y_test, predictions))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as model_file:
        pickle.dump(
            {
                "model": model,
                "feature_columns": FEATURE_COLUMNS,
            },
            model_file,
        )

    print(f"Saved trained model -> {MODEL_PATH}")
    return MODEL_PATH


if __name__ == "__main__":
    train_model(rows=1000)
