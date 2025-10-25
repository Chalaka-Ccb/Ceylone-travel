# # File: app/api/v1/endpoints/trips.py
#
# from fastapi import APIRouter, Depends, HTTPException
# from app.models.schemas import TripGenerationRequest, TripResponse, ReservationRequest, UserResponse, ClerkUser
# from app.core.auth import get_authenticated_user
# from app.db.supabase_client import supabase_client
# from app.services import plan_service
# from supabase import Client
# import sys
#
# router = APIRouter()
#
#
# # Dependency
# def get_db():
#     return supabase_client
#
#
# # --- MODIFIED /generate-plan ---
# @router.post("/generate-plan", response_model=TripResponse)
# def generate_plan(
#         request: TripGenerationRequest,
#         current_user: ClerkUser = Depends(get_authenticated_user),
#         db: Client = Depends(get_db)
# ):
#     """
#     Generates a new personalized travel plan based on user inputs.
#     Requires authentication.
#     """
#     # --- (FIX 1: Separate the user upsert) ---
#     try:
#         user_data_to_upsert = {'id': current_user.id}
#
#         # Only add email to the upsert if it actually exists
#         if current_user.email:
#             user_data_to_upsert['email'] = current_user.email
#
#         print(f"--- Upserting user profile: {user_data_to_upsert} ---")
#         sys.stdout.flush()
#
#         db.table('users').upsert(user_data_to_upsert, on_conflict='id').execute()
#
#         print(f"--- User profile upsert successful for {current_user.id} ---")
#         sys.stdout.flush()
#
#     except Exception as e:
#         print(f"---!!! FATAL: Error upserting user profile !!!---", file=sys.stderr)
#         print(f"Error: {e}", file=sys.stderr)
#         sys.stderr.flush()
#         # This is the error your frontend will now see
#         raise HTTPException(status_code=500, detail=f"Failed to create user profile in DB: {e}")
#
#     # --- (FIX 2: Separate the plan generation) ---
#     # This code will only run if the user upsert above was successful
#     try:
#         print(f"Generating plan for user: {current_user.id}")
#         trip_plan = plan_service.generate_trip_plan(request, user_id=current_user.id)
#         return trip_plan
#
#     except HTTPException as e:
#         # Re-raise known errors from the service (e.g., "Budget too low")
#         raise e
#     except Exception as e:
#         # Catch any errors from plan_service.py
#         print(f"Unexpected error in /generate-plan endpoint: {e}", file=sys.stderr)
#         sys.stderr.flush()
#         # This will catch the "[NEW ERROR 1]" or "[NEW ERROR 2]"
#         # and pass them to the frontend
#         raise HTTPException(status_code=500, detail=f"Error during plan generation: {e}")
#
#
# # --- MODIFIED /reserve-trip ---
# @router.post("/reserve-trip", response_model=UserResponse)
# def reserve_trip(
#         request: ReservationRequest,
#         current_user: ClerkUser = Depends(get_authenticated_user),
#         db: Client = Depends(get_db)
# ):
#     """
#     Saves reservation details for a user and links it to their trip.
#     Requires authentication.
#     """
#     try:
#         user_response = db.table('users').upsert({
#             'id': current_user.id,
#             'email': request.email,
#             'first_name': request.first_name,
#             'last_name': request.last_name,
#         }, on_conflict='id').execute()
#
#         if not user_response.data:
#             raise Exception("Failed to upsert user profile data.")
#
#         new_user_profile = user_response.data[0]
#
#         # --- (FIXED TYPO HERE) ---
#         # Changed 'new_user__profile' to 'new_user_profile'
#         trip_update_response = db.table('trips').update({
#             'user_id': new_user_profile['id']
#         }).eq('id', request.trip_id).execute()
#
#         if not trip_update_response.data:
#             print(f"Warning: Could not link trip {request.trip_id} to user {new_user_profile['id']}.")
#
#         return UserResponse(
#             id=new_user_profile.get('id'),
#             email=new_user_profile.get('email'),
#             first_name=new_user_profile.get('first_name'),
#             last_name=new_user_profile.get('last_name')
#         )
#
#     except Exception as e:
#         print(f"Error in /reserve-trip: {e}", file=sys.stderr)
#         sys.stderr.flush()
#         raise HTTPException(status_code=500, detail="Could not process reservation.")

# File: app/api/v1/endpoints/trips.py

from fastapi import APIRouter, Depends, HTTPException
# --- IMPORT ClerkUser and auth dependency ---
from app.models.schemas import TripGenerationRequest, TripResponse, ReservationRequest, ReservationUserResponse, \
    ClerkUser  # <-- (FIX 1)
from app.core.auth import get_authenticated_user
# ---
from app.db.supabase_client import supabase_client
from app.services import plan_service
from supabase import Client
import sys

router = APIRouter()


# Dependency
def get_db():
    return supabase_client


# --- MODIFIED /generate-plan ---
@router.post("/generate-plan", response_model=TripResponse)
def generate_plan(
        request: TripGenerationRequest,
        current_user: ClerkUser = Depends(get_authenticated_user),
        db: Client = Depends(get_db)
):
    """
    Generates a new personalized travel plan based on user inputs.
    Requires authentication.
    """
    try:
        user_data_to_upsert = {'id': current_user.id}

        if current_user.email:
            user_data_to_upsert['email'] = current_user.email

        print(f"--- Upserting user profile: {user_data_to_upsert} ---")
        sys.stdout.flush()

        db.table('users').upsert(user_data_to_upsert, on_conflict='id').execute()

        print(f"--- User profile upsert successful for {current_user.id} ---")
        sys.stdout.flush()

    except Exception as e:
        print(f"---!!! FATAL: Error upserting user profile !!!---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=f"Failed to create user profile in DB: {e}")

    try:
        print(f"Generating plan for user: {current_user.id}")
        trip_plan = plan_service.generate_trip_plan(request, user_id=current_user.id)
        return trip_plan

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error in /generate-plan endpoint: {e}", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=f"Error during plan generation: {e}")


# --- (FIX 2) MODIFIED /reserve-trip ---
@router.post("/reserve-trip", response_model=ReservationUserResponse)  # <-- Renamed UserResponse
def reserve_trip(
        request: ReservationRequest,
        current_user: ClerkUser = Depends(get_authenticated_user),
        db: Client = Depends(get_db)
):
    """
    Saves reservation details for a user and links it to their trip.
    Requires authentication.
    """
    try:
        user_response = db.table('users').upsert({
            'id': current_user.id,
            'email': request.email,
            'first_name': request.first_name,
            'last_name': request.last_name,
        }, on_conflict='id').execute()

        if not user_response.data:
            raise Exception("Failed to upsert user profile data.")

        new_user_profile = user_response.data[0]

        trip_update_response = db.table('trips').update({
            'user_id': new_user_profile['id']
        }).eq('id', request.trip_id).execute()

        if not trip_update_response.data:
            print(f"Warning: Could not link trip {request.trip_id} to user {new_user_profile['id']}.")

        # --- (FIX 3) Return the correct model type ---
        return ReservationUserResponse(  # <-- Renamed UserResponse
            id=new_user_profile.get('id'),
            email=new_user_profile.get('email'),
            first_name=new_user_profile.get('first_name'),
            last_name=new_user_profile.get('last_name')
        )

    except Exception as e:
        print(f"Error in /reserve-trip: {e}", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail="Could not process reservation.")