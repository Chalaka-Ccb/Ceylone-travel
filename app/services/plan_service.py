# File: app/services/plan_service.py

import httpx
from supabase import Client
from app.models.schemas import TripGenerationRequest, TripResponse, LocationResponse, TripDayResponse
from app.core.config import settings
from app.services import ors_service
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
import sys
import traceback

# Import the client instance directly
from app.db.supabase_client import supabase_client as db_client


# Helper function (no changes)
def parse_point_string(point_str: str) -> Dict[str, float]:
    try:
        lon, lat = point_str.strip("POINT()").split()
        return {"longitude": float(lon), "latitude": float(lat)}
    except Exception:
        print(f"Error parsing point string: {point_str}")
        return {"longitude": 0.0, "latitude": 0.0}


def generate_trip_plan(request: TripGenerationRequest, user_id: Optional[str] = None) -> TripResponse:
    # ... (Steps 1, 2, 3 - Budget Check, Fetch Locations, Prioritize - NO CHANGES) ...
    # 1. Budget Check
    min_budget = settings.DAILY_BUDGET_PER_PERSON * request.num_people * request.num_days
    if request.budget < min_budget:
        raise HTTPException(
            status_code=400,
            detail=f"Budget is too low. Minimum required budget for {request.num_people} people for {request.num_days} days is ${min_budget}."
        )

    # 2. Fetch locations
    try:
        locations_response = db_client.rpc(
            'get_locations_by_tags',
            {'tag_names': request.interests}
        ).execute()

        if not locations_response.data:
            raise HTTPException(status_code=404, detail="No locations found matching your interests.")

        all_locations = locations_response.data
    except Exception as e:
        print(f"Supabase error fetching locations: {e}", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail="Error fetching locations from database.")

    # 3. Prioritize locations
    interest_set = set(request.interests)
    perfect_matches = []
    partial_matches = []
    for loc in all_locations:
        loc_tags = set(loc['tags'])
        if 'lon' in loc and 'lat' in loc and loc['lon'] is not None and loc['lat'] is not None:
            if interest_set.issubset(loc_tags):
                perfect_matches.append(loc)
            else:
                partial_matches.append(loc)
        else:
            print(f"Warning: Location {loc.get('name', 'Unknown')} missing coordinates, skipping.")
    sorted_locations = perfect_matches + partial_matches
    if not sorted_locations:
        raise HTTPException(status_code=44, detail="No valid locations with coordinates found for your interests.")

    # 4. Build the Itinerary
    itinerary_days = []
    available_locations = sorted_locations.copy()

    # Start at the airport
    current_coords = settings.STARTING_POINT_COORDS

    # 5. Prepare data for the external hotel service
    hotel_service_data = {
        "num_people": request.num_people,
        "daily_locations": {}
    }

    # 6. Main Day Generation Loop
    for day_num in range(1, request.num_days + 1):
        day_plan_locations = []
        day_route_segments = []  # <-- NEW: List to hold route geometries for the day

        # Assign up to 6 locations per day
        for _ in range(6):
            if not available_locations:
                break
            try:
                coord_list = [current_coords] + [
                    (float(loc['lon']), float(loc['lat'])) for loc in available_locations
                ]
            except (ValueError, KeyError, TypeError) as coord_err:
                print(f"Error preparing coordinates for ORS: {coord_err}. Skipping day planning step.")
                break

            matrix = ors_service.get_distance_matrix(coord_list)

            if not matrix or 'durations' not in matrix or not matrix['durations'] or not matrix['durations'][0]:
                print(f"ORS Matrix API failed or returned unexpected structure: {matrix}. Breaking plan generation.")
                available_locations = []
                break
            travel_times = matrix['durations'][0][1:]
            if len(travel_times) != len(available_locations):
                print(
                    f"Mismatch between travel times ({len(travel_times)}) and available locations ({len(available_locations)}). Skipping step.")
                break
            if not travel_times:
                print("No travel times returned by ORS. Stopping day planning.")
                break
            closest_index = min(range(len(travel_times)),
                                key=lambda i: travel_times[i] if travel_times[i] is not None else float('inf'))
            if travel_times[closest_index] is None:
                print(
                    f"Could not find a route to any remaining locations from {current_coords}. Stopping day planning.")
                break

            chosen_location = available_locations.pop(closest_index)

            # --- NEW: Get the route geometry for this step ---
            start_coords_for_route = current_coords
            end_coords_for_route = (float(chosen_location['lon']), float(chosen_location['lat']))

            # This calls 'get_directions_route' for "driving-car"
            route_geom = ors_service.get_directions_route(start_coords_for_route, end_coords_for_route)

            if route_geom:
                day_route_segments.append(route_geom)
            else:
                day_route_segments.append(None)  # Add None if route fails
            # --- END NEW ---

            day_plan_locations.append(chosen_location)
            current_coords = end_coords_for_route  # Update current_coords for the *next* iteration

        # Add the day's plan
        if day_plan_locations:
            last_location_of_the_day = day_plan_locations[-1]
            hotel_service_data["daily_locations"][f"day{day_num}"] = {
                "lat": float(last_location_of_the_day['lat']),
                "long": float(last_location_of_the_day['lon'])
            }
            itinerary_days.append(
                TripDayResponse(
                    day_number=day_num,
                    locations=[
                        LocationResponse(
                            id=loc['id'],
                            name=loc['name'],
                            description=loc['description'],
                            image_url=loc['image_url'],
                            coordinates={"longitude": float(loc['lon']), "latitude": float(loc['lat'])}
                        ) for loc in day_plan_locations
                    ],
                    route_geometries=day_route_segments  # <-- NEW: Add the route list
                )
            )
        if not available_locations:
            break

    # 7. Call Hotel Service (No changes)
    if hotel_service_data["daily_locations"]:
        hotel_service_endpoint = f"{settings.HOTEL_SERVICE_URL}/nearest-hotels"
        print(f"--- Calling Hotel Service at {hotel_service_endpoint} ---")
        print(hotel_service_data)
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(hotel_service_endpoint, json=hotel_service_data)
                response.raise_for_status()
                hotel_results = response.json()
                print(f"Hotel service response: {hotel_results}")
        except httpx.HTTPStatusError as e:
            print(f"Hotel service returned an error: {e}", file=sys.stderr)
        except httpx.RequestError as e:
            print(f"Error calling hotel service (e.g., connection refused): {e}", file=sys.stderr)
        except Exception as e:
            print(f"An unexpected error occurred during hotel service call: {e}", file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()

    if not itinerary_days:
        raise HTTPException(status_code=404,
                            detail="Could not generate any valid itinerary days with the selected locations and routing.")

    # 8. Save the new trip to the database
    new_trip_id = None
    new_trip = None

    # Part 1: Save the main 'trips' record
    try:
        print("--- Attempting to save main trip record... ---")
        trip_data_to_insert = {
            "num_people": request.num_people,
            "num_days": request.num_days,
            "total_budget": request.budget
        }

        if user_id:
            trip_data_to_insert['user_id'] = user_id

        print(f"--- Trip data to insert: {trip_data_to_insert} ---")
        sys.stdout.flush()

        trip_insert_response = db_client.table('trips').insert(trip_data_to_insert).execute()

        if not trip_insert_response.data:
            print("--- ERROR: Main 'trips' insert response returned no data. ---", file=sys.stderr)
            sys.stderr.flush()
            raise Exception("Failed to insert main trip record or no data returned.")

        new_trip = trip_insert_response.data[0]
        new_trip_id = new_trip['id']
        print(f"--- New trip created with ID: {new_trip_id} ---")
        sys.stdout.flush()

    except Exception as e:
        print("---!!! FATAL ERROR SAVING MAIN 'trips' RECORD !!!---", file=sys.stderr)
        print(f"Supabase error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail="[NEW ERROR 1] Failed to save the main trip. Check backend log.")

    # Part 2: Save the 'trip_days' records
    try:
        trip_days_data = []
        for day in itinerary_days:
            for i, loc in enumerate(day.locations):
                if loc.id:
                    trip_days_data.append({
                        "trip_id": new_trip_id,
                        "day_number": day.day_number,
                        "step_order": i + 1,
                        "location_id": loc.id
                    })
                else:
                    print(f"Warning: Location {loc.name} has invalid ID on Day {day.day_number}, skipping.")

        if trip_days_data:
            print(f"--- Saving {len(trip_days_data)} trip day entries... ---")
            days_insert_response = db_client.table('trip_days').insert(trip_days_data).execute()
            if not days_insert_response.data and len(trip_days_data) > 0:
                print("Warning: Trip days insert command executed but returned no data.")
        else:
            print("Warning: No valid trip day locations to save.")

        print("--- Trip save complete. ---")
        sys.stdout.flush()

    except Exception as e:
        print("---!!! FATAL ERROR SAVING 'trip_days' RECORDS !!!---", file=sys.stderr)
        print(f"Supabase error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail="[NEW ERROR 2] Failed to save itinerary days. Check backend log.")

    if not new_trip_id or not new_trip:
        print("Error: Trip ID or Trip data is missing after supposedly successful save.", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail="Internal error after saving trip.")

    # 9. Return the full trip plan
    return TripResponse(
        id=new_trip_id,
        num_people=new_trip['num_people'],
        num_days=new_trip['num_days'],
        total_budget=new_trip['total_budget'],
        itinerary=itinerary_days,
        user_id=new_trip.get('user_id')

    )