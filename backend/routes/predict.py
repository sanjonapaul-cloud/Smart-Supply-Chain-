from flask import Blueprint, request, jsonify
import pickle
import datetime
from pathlib import Path
import pandas as pd  # ✅ use pandas instead of numpy

from utils.logger import log_info, log_error
from utils.storage import save_prediction, get_history

predict_bp = Blueprint("predict", __name__)

# load model using a stable path relative to this file
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "model.pkl"

try:
    with open(MODEL_PATH, "rb") as model_file:
        model = pickle.load(model_file)
except FileNotFoundError as e:
    raise RuntimeError(f"Model file not found at {MODEL_PATH}") from e


@predict_bp.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "Invalid or missing JSON payload"
            }), 400

        # validation
        distance = data.get("distance")
        delay = data.get("delay")
        weather = data.get("weather")

        if distance is None or delay is None or weather is None:
            return jsonify({
                "status": "error",
                "message": "Missing input fields"
            }), 400

        # convert types
        distance = float(distance)
        delay = float(delay)
        weather = int(weather)

        # ✅ FIX: use DataFrame (removes warning)
        input_data = pd.DataFrame([{
            "distance": distance,
            "delay": delay,
            "weather": weather
        }])

        # prediction
        prediction = model.predict(input_data)[0]

        result = "High Risk 🚨" if prediction == 1 else "Safe ✅"

        # save history
        save_prediction({
            "timestamp": str(datetime.datetime.now()),
            "input": data,
            "result": result
        })

        # log success
        log_info(f"Prediction: {result} | Input: {data}")

        return jsonify({
            "status": "success",
            "prediction": result
        })

    except Exception as e:
        # log error
        log_error(str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# 🔥 GET HISTORY ROUTE
@predict_bp.route("/history", methods=["GET"])
def history():
    try:
        data = get_history()

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        log_error(str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500