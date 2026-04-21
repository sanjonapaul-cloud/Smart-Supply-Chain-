print("File is running")
import requests

API_KEY = "API_KEY"
URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def get_distance(source_coords, destination_coords):

    if (
        not isinstance(source_coords, list)
        or not isinstance(destination_coords, list)
        or len(source_coords) != 2
        or len(destination_coords) != 2
    ):
        raise ValueError("Invalid coordinates format. Use [longitude, latitude].")

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
        response = requests.post(URL, json=body, headers=headers)

        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        data = response.json()

        summary = data["routes"][0]["summary"]
        distance_km = round(summary["distance"] / 1000, 2)
        duration_min = round(summary["duration"] / 60, 2)

        return {
            "distance": distance_km,
            "duration": duration_min
        }

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")

    except (KeyError, IndexError):
        raise Exception("Invalid response format from API")


# ✅ THIS MUST BE OUTSIDE THE FUNCTION
if __name__ == "__main__":
    print("MAIN BLOCK WORKING")

    try:
        result = get_distance([88.36, 22.57], [77.10, 28.70])
        print("RESULT:", result)
    except Exception as e:
        print("ERROR:", e)