from flask import Blueprint, request, jsonify
import pickle
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

from utils.logger import log_info, log_error
from utils.storage import save_prediction, get_history

predict_bp = Blueprint("predict", __name__)

# Load model, scaler, and metadata
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "model.pkl"

try:
    with open(MODEL_PATH, "rb") as model_file:
        model_data = pickle.load(model_file)
        model = model_data['model']
        scaler = model_data['scaler']
        feature_columns = model_data['feature_columns']
        label_encoders = model_data['label_encoders']
    log_info(f"✓ Model loaded successfully with {len(feature_columns)} features")
except FileNotFoundError as e:
    raise RuntimeError(f"Model file not found at {MODEL_PATH}") from e
except Exception as e:
    raise RuntimeError(f"Error loading model: {str(e)}") from e


def _legacy_to_model_payload(data):
    """Map legacy 3-field frontend payload to full model feature payload."""
    distance = float(data.get("distance", 0))
    delay = float(data.get("delay", 0))
    weather = int(data.get("weather", 0))

    # Heuristic mapping to keep old UI compatible with the new 18-feature model.
    lead_time = max(1, int(round(delay / 2 + distance / 120)))
    shipping_times = max(1, int(round(delay / 6 + distance / 400)))
    defect_rates = min(5.0, max(0.1, 1.2 + (1.8 if weather == 1 else 0.0) + delay / 20))

    return {
        "Price": 50.0,
        "Availability": 70,
        "Number_of_products_sold": 400,
        "Revenue_generated": 12000.0,
        "Stock_levels": 55,
        "Lead_times": lead_time,
        "Shipping_times": shipping_times,
        "Shipping_carriers": "Carrier B",
        "Shipping_costs": 120.0 + distance * 0.2,
        "Location": "Mumbai",
        "Lead_time": lead_time,
        "Production_volumes": 500,
        "Manufacturing_lead_time": max(1, int(round(lead_time * 0.7))),
        "Manufacturing_costs": 40.0 + distance * 0.05,
        "Inspection_results": "Pending" if weather == 1 else "Pass",
        "Defect_rates": float(defect_rates),
        "Transportation_modes": "Road" if distance < 700 else "Rail",
        "Costs": 180.0 + distance * 0.25,
    }


@predict_bp.route("/predict", methods=["POST"])
def predict():
    """
    Predict Supply Chain Risk based on input features.
    
    Expected JSON input (example):
    {
        "lead_time": 25,
        "shipping_times": 8,
        "defect_rates": 2.5,
        "price": 50.0,
        "availability": 75,
        "number_of_products_sold": 500,
        "revenue_generated": 25000,
        "stock_levels": 100,
        "shipping_carriers": "Carrier A",
        "shipping_costs": 150.0,
        "location": "Mumbai",
        "production_volumes": 1000,
        "manufacturing_lead_time": 20,
        "manufacturing_costs": 500.0,
        "inspection_results": "Pass",
        "transportation_modes": "Road",
        "costs": 200.0
    }
    """
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "Invalid or missing JSON payload"
            }), 400

        # Backward compatibility for legacy frontend payload:
        # { distance, delay, weather }
        if all(k in data for k in ["distance", "delay", "weather"]):
            data = _legacy_to_model_payload(data)

        # Normalize feature names: convert any case to match expected column names
        # This allows users to send lowercase keys like 'lead_time' and it maps to 'Lead_time'
        normalized_data = {}
        for key, value in data.items():
            # Try to find a matching feature column (case-insensitive match)
            matched = False
            for feature_col in feature_columns:
                if key.lower().replace('_', '').replace(' ', '') == feature_col.lower().replace('_', '').replace(' ', ''):
                    normalized_data[feature_col] = value
                    matched = True
                    break
            if not matched:
                # If no match found, keep the original key (might be extra fields to ignore)
                normalized_data[key] = value

        # Create a DataFrame with the normalized input data
        try:
            input_df = pd.DataFrame([normalized_data])
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error creating DataFrame: {str(e)}"
            }), 400

        # Encode categorical features using the saved label encoders
        for col in label_encoders.keys():
            if col in input_df.columns:
                try:
                    input_df[col] = label_encoders[col].transform(input_df[col].astype(str))
                except ValueError as e:
                    return jsonify({
                        "status": "error",
                        "message": f"Invalid value for '{col}': {str(e)}"
                    }), 400

        # Ensure all required features are present and in correct order
        missing_features = set(feature_columns) - set(input_df.columns)
        if missing_features:
            return jsonify({
                "status": "error",
                "message": f"Missing required features: {list(missing_features)}"
            }), 400

        # Select only the required features in the correct order
        X_input = input_df[feature_columns]

        # Scale the features
        X_scaled = scaler.transform(X_input)

        # Make prediction
        prediction = model.predict(X_scaled)[0]
        prediction_proba = model.predict_proba(X_scaled)[0]

        result = "High Risk 🚨" if prediction == 1 else "Safe ✅"

        prediction_data = {
            "timestamp": str(datetime.datetime.now()),
            "input": data,
            "result": result,
            "confidence": float(max(prediction_proba) * 100)
        }

        # Save to history
        save_prediction(prediction_data)

        # Log success
        log_info(f"✓ Prediction: {result} (Confidence: {max(prediction_proba)*100:.1f}%) | Input: Lead_time={data.get('lead_time')}, Shipping_times={data.get('shipping_times')}, Defect_rates={data.get('defect_rates')}")

        return jsonify({
            "status": "success",
            "prediction": result,
            "confidence": float(max(prediction_proba) * 100),
            "risk_probability": {
                "safe": float(prediction_proba[0] * 100),
                "high_risk": float(prediction_proba[1] * 100)
            }
        }), 200

    except Exception as e:
        log_error(f"Prediction error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@predict_bp.route("/history", methods=["GET"])
def history():
    """Get prediction history"""
    try:
        data = get_history()
        return jsonify({
            "status": "success",
            "data": data
        }), 200

    except Exception as e:
        log_error(f"History retrieval error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@predict_bp.route("/health", methods=["GET"])
def health():
    """Check if the model is loaded and ready"""
    return jsonify({
        "status": "ok",
        "model_loaded": True,
        "features_count": len(feature_columns),
        "feature_columns": feature_columns
    }), 200