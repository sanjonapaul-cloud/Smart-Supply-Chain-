from flask import Blueprint, request, jsonify
import numpy as np
import pickle
from utils.logger import log_info, log_error

predict_bp = Blueprint("predict", __name__)

# load model
model = pickle.load(open("models/model.pkl", "rb"))

@predict_bp.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json

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

        # ML input
        input_data = np.array([[distance, delay, weather]])

        # prediction
        prediction = model.predict(input_data)[0]

        result = "High Risk 🚨" if prediction == 1 else "Safe ✅"

        # ✅ LOG SUCCESS (THIS IS STEP 4 YOU ASKED)
        log_info(f"Prediction: {result} | Input: {data}")

        return jsonify({
            "status": "success",
            "prediction": result
        })

    except Exception as e:
        # ✅ LOG ERROR
        log_error(str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500