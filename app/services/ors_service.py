# import httpx
# from app.core.config import settings
# from typing import List, Tuple, Dict, Any
#
# # ORS API base URL
# ORS_BASE_URL = "https://api.openrouteservice.org"
#
#
# def get_coordinates_for_location(location_name: str) -> Tuple[float, float] | None:
#     """
#     Uses ORS Geocoding to find the coordinates for a location name.
#     Returns (longitude, latitude) or None.
#     """
#     client = httpx.Client()
#     try:
#         response = client.get(
#             f"{ORS_BASE_URL}/geocode/search",
#             params={
#                 "api_key": settings.ORS_API_KEY,
#                 "text": location_name,
#                 "boundary.country": "LKA",  # Restrict search to Sri Lanka
#                 "size": 1
#             }
#         )
#         response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
#         data = response.json()
#
#         if data.get("features"):
#             # Coordinates are [longitude, latitude]
#             coords = data["features"][0]["geometry"]["coordinates"]
#             return (coords[0], coords[1])
#         return None
#     except httpx.HTTPStatusError as e:
#         print(f"HTTP error during geocoding: {e}")
#         return None
#     except Exception as e:
#         print(f"Error in get_coordinates_for_location: {e}")
#         return None
#     finally:
#         client.close()
#
#
# def get_distance_matrix(locations: List[Tuple[float, float]]) -> dict | None:
#     """
#     Gets a duration matrix from ORS for a list of coordinates.
#     The coordinates must be in (longitude, latitude) format.
#     """
#     client = httpx.Client()
#     headers = {
#         'Authorization': settings.ORS_API_KEY,
#         'Content-Type': 'application/json'
#     }
#     body = {
#         "locations": locations,
#         "metrics": ["duration"],  # We only need duration for "shortest time" logic
#         "units": "km"
#     }
#
#     try:
#         response = client.post(
#             f"{ORS_BASE_URL}/v2/matrix/driving-car",
#             json=body,
#             headers=headers
#         )
#         response.raise_for_status()  # This will catch 4xx/5xx errors
#         return response.json()
#     except httpx.HTTPStatusError as e:
#         print(f"FATAL ERROR in get_distance_matrix: {e.response.status_code} - {e.response.text}")
#         return None
#     except Exception as e:
#         print(f"Error in get_distance_matrix: {e}")
#         return None
#     finally:
#         client.close()
#
#
# # +++ NEW FUNCTION +++
# def get_directions_route(start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Dict[str, Any] | None:
#     """
#     Gets the vehicle route geometry between two points.
#     Returns a GeoJSON geometry dictionary.
#     """
#     client = httpx.Client()
#     headers = {
#         'Authorization': settings.ORS_API_KEY,
#         'Content-Type': 'application/json'
#     }
#     # Note: ORS expects (longitude, latitude)
#     body = {
#         "coordinates": [
#             [start_coords[0], start_coords[1]],
#             [end_coords[0], end_coords[1]]
#         ]
#     }
#
#     try:
#         # We ask for GeoJSON format directly
#         response = client.post(
#             f"{ORS_BASE_URL}/v2/directions/driving-car/geojson",
#             json=body,
#             headers=headers
#         )
#         response.raise_for_status()
#         data = response.json()
#
#         # Extract the geometry from the GeoJSON response
#         if data.get("features") and len(data["features"]) > 0:
#             return data["features"][0]["geometry"]
#         return None
#     except httpx.HTTPStatusError as e:
#         print(f"Error getting directions route: {e.response.status_code} - {e.response.text}")
#         return None
#     except Exception as e:
#         print(f"Error in get_directions_route: {e}")
#         return None
#     finally:
#         client.close()
# # +++++++++++++++++++++

# File: app/services/ors_service.py
# File: app/services/ors_service.py

import httpx
from app.core.config import settings
from typing import List, Tuple, Dict, Any

# ORS API base URL
ORS_BASE_URL = "https://api.openrouteservice.org"


def get_coordinates_for_location(location_name: str) -> Tuple[float, float] | None:
    """
    Uses ORS Geocoding to find the coordinates for a location name.
    Returns (longitude, latitude) or None.
    """
    client = httpx.Client()
    try:
        response = client.get(
            f"{ORS_BASE_URL}/geocode/search",
            params={
                "api_key": settings.ORS_API_KEY,
                "text": location_name,
                "boundary.country": "LKA",  # Restrict search to Sri Lanka
                "size": 1
            }
        )
        response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
        data = response.json()

        if data.get("features"):
            # Coordinates are [longitude, latitude]
            coords = data["features"][0]["geometry"]["coordinates"]
            return (coords[0], coords[1])
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error during geocoding: {e}")
        return None
    except Exception as e:
        print(f"Error in get_coordinates_for_location: {e}")
        return None
    finally:
        client.close()


def get_distance_matrix(locations: List[Tuple[float, float]]) -> dict | None:
    """
    Gets a duration matrix from ORS for a list of coordinates.
    The coordinates must be in (longitude, latitude) format.
    """
    client = httpx.Client()
    headers = {
        'Authorization': settings.ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    body = {
        "locations": locations,
        "metrics": ["duration"],  # We only need duration for "shortest time" logic
        "units": "km"
    }

    try:
        response = client.post(
            f"{ORS_BASE_URL}/v2/matrix/driving-car",
            json=body,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if "handshake operation timed out" in str(e):
            print(f"FATAL SSL ERROR in get_distance_matrix: {e}. Check network/firewall.")
        else:
            print(f"FATAL HTTP ERROR in get_distance_matrix: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"Error in get_distance_matrix: {e}")
        return None
    finally:
        client.close()


def get_directions_route(start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Dict[str, Any] | None:
    """
    Gets the vehicle route geometry between two points.
    Returns a GeoJSON geometry dictionary.
    """
    client = httpx.Client()
    headers = {
        'Authorization': settings.ORS_API_KEY,
        'Content-Type': 'application/json'
    }

    body = {
        "coordinates": [
            [start_coords[0], start_coords[1]],
            [end_coords[0], end_coords[1]]
        ],
        # --- (THE FIX) ---
        # 'radiuses' is a top-level parameter, not nested.
        # -1 means unlimited search radius to find the nearest routable road.
        "radiuses": [-1, -1]
        # --- END FIX ---
    }

    try:
        # We ask for GeoJSON format directly
        response = client.post(
            f"{ORS_BASE_URL}/v2/directions/driving-car/geojson",
            json=body,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Extract the geometry from the GeoJSON response
        if data.get("features") and len(data["features"]) > 0:
            return data["features"][0]["geometry"]
        return None
    except httpx.HTTPStatusError as e:
        print(f"Error getting directions route: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"Error in get_directions_route: {e}")
        return None
    finally:
        client.close()