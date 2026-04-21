print("File is running")

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DISTANCE_API_KEY")

if not API_KEY:
    raise ValueError("DISTANCE_API_KEY not found in environment variables")

URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def get_distance(source_coords, destination_coords):

    if (
        not isinstance(source_coords, list)
        or not isinstance(destination_coords, list)
        or len(source_coords) != 2
        or len(destination_coords) != 2
    ):
        return {"error": "Invalid coordinates format. Use [longitude, latitude]."}

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            source_coords,
            destination_coords
        ]
    }

    try:
        response = requests.post(URL, json=body, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json()

        summary = data["routes"][0]["summary"]
        distance_km = round(summary["distance"] / 1000, 2)
        duration_min = round(summary["duration"] / 60, 2)

        return {
            "distance_km": distance_km,
            "duration_min": duration_min
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

    except (KeyError, IndexError):
        return {"error": "Invalid response format from API"}


if __name__ == "__main__":
    print("MAIN BLOCK WORKING")

    result = get_distance([88.36, 22.57], [77.10, 28.70])
    print("RESULT:", result)