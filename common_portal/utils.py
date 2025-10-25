import requests
from django.conf import settings

def calculate_distance_and_time(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Returns both distance (km) and estimated time (minutes) between two coordinates using Google Distance Matrix API.
    """
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{pickup_lat},{pickup_lng}",
        "destinations": f"{dropoff_lat},{dropoff_lng}",
        "units": "metric",
        "mode": "driving",  # realistic driving distance and time
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data["status"] == "OK" and data["rows"]:
            element = data["rows"][0]["elements"][0]
            if element["status"] == "OK":
                distance_km = round(element["distance"]["value"] / 1000, 2)  # meters -> km
                duration_minutes = round(element["duration"]["value"] / 60)  # seconds -> minutes
                return distance_km, duration_minutes
    except Exception as e:
        print(f"Google API error: {e}")

    return None, None




# import math

# def calculate_distance(lat1, lon1, lat2, lon2):
#     """
#     Calculate the great-circle distance between two points on the Earth (in km).
#     Uses the Haversine formula.
#     """
#     R = 6371  # Radius of Earth in kilometers

#     lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
#     dlat = lat2 - lat1
#     dlon = lon2 - lon1

#     a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

#     return round(R * c, 2)
