import os

from flask import Flask
from flask_cors import CORS
from routes.predict import predict_bp

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Backend is running 🚀"

# register route
app.register_blueprint(predict_bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)