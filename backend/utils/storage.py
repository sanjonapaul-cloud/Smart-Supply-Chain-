import json
import os

FILE = "data/history.json"

def save_prediction(entry):
    try:
        if not os.path.exists(FILE):
            with open(FILE, "w") as f:
                json.dump([], f)

        with open(FILE, "r") as f:
            history = json.load(f)

        history.append(entry)

        with open(FILE, "w") as f:
            json.dump(history, f, indent=4)

    except Exception as e:
        print("Error saving history:", e)


def get_history():
    try:
        if not os.path.exists(FILE):
            return []

        with open(FILE, "r") as f:
            return json.load(f)

    except:
        return []