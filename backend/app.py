from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Backend is running 🚀"

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    value = data.get("value", 0)

    if value > 50:
        result = "High Risk 🚨"
    else:
        result = "Safe ✅"

    return jsonify({"prediction": result})

if __name__ == "__main__":
    app.run(debug=True)