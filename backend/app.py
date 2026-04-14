import pickle
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
model = pickle.load(open("models/model.pkl", "rb"))
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Backend is running 🚀"

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    distance = data.get("distance")
    delay = data.get("delay")
    weather = data.get("weather")

    input_data = np.array([[distance, delay, weather]])

    prediction = model.predict(input_data)[0]

    result = "High Risk 🚨" if prediction == 1 else "Safe ✅"

    return jsonify({"prediction": result})

if __name__ == "__main__":
    app.run(debug=True)