# File: app/api/v1/endpoints/trips.py

from fastapi import APIRouter, Depends, HTTPException
# --- IMPORT ClerkUser and auth dependency ---
from app.models.schemas import TripGenerationRequest, TripResponse, ReservationRequest, UserResponse, ClerkUser
from app.core.auth import get_authenticated_user
# ---
from app.db.supabase_client import supabase_client
from app.services import plan_service
from supabase import Client

router = APIRouter()


# Dependency (Keep for /reserve-trip if it still needs direct db access)
def get_db():
    return supabase_client


# --- MODIFIED /generate-plan ---
@router.post("/generate-plan", response_model=TripResponse)
def generate_plan(
        request: TripGenerationRequest,
        # --- ADD THIS DEPENDENCY ---
        # This will check the token. If valid, 'current_user' will be a ClerkUser model.
        # If invalid, it will stop here and return a 401 Error.
        current_user: ClerkUser = Depends(get_authenticated_user)
):
    """
    Generates a new personalized travel plan based on user inputs.
    Requires authentication.
    """
    try:
        # --- PASS 'current_user.id' to the service ---
        print(f"Generating plan for user: {current_user.id}")  # Good for logging
        trip_plan = plan_service.generate_trip_plan(request, user_id=current_user.id)
        return trip_plan
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unexpected error in /generate-plan: {e}")  # Keep detailed logging
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


# --- MODIFIED /reserve-trip ---
@router.post("/reserve-trip", response_model=UserResponse)
def reserve_trip(
        request: ReservationRequest,
        # --- ADD AUTH DEPENDENCY ---
        current_user: ClerkUser = Depends(get_authenticated_user),
        db: Client = Depends(get_db)
):
    """
    Saves reservation details for a user and links it to their trip.
    Requires authentication.
    """
    # With Clerk, the user account (current_user.id) is the source of truth.
    # The 'users' table in your Supabase might now be used for storing *profiles*
    # or *reservation details* linked to the Clerk user_id, rather than for auth.

    # We will use the 'current_user.id' as the unique ID.
    # We can 'upsert' (update or insert) profile info based on their Clerk ID.

    try:
        # Use the Clerk ID as the primary key for your user/profile table
        user_response = db.table('users').upsert({
            'id': current_user.id,  # <-- Use Clerk ID
            'email': request.email,  # <-- Use email from form ( or current_user.email)
            'first_name': request.first_name,
            'last_name': request.last_name,
            # ... add other fields from request if your 'users' table stores them
        }, on_conflict='id').execute()  # <-- Upsert on 'id' (the Clerk ID)

        if not user_response.data:
            raise Exception("Failed to upsert user profile data.")

        new_user_profile = user_response.data[0]

        # Now, link the trip to this user ID
        trip_update_response = db.table('trips').update({
            'user_id': new_user_profile['id']  # <-- This is the Clerk ID
        }).eq('id', request.trip_id).execute()

        if not trip_update_response.data:
            # This might happen if the trip_id is wrong, but we'll allow it for now
            print(f"Warning: Could not link trip {request.trip_id} to user {new_user_profile['id']}.")

        # Return the user data that was saved
        return UserResponse(
            id=new_user_profile.get('id'),
            email=new_user_profile.get('email'),
            first_name=new_user_profile.get('first_name'),
            last_name=new_user_profile.get('last_name')
        )

    except Exception as e:
        print(f"Error in /reserve-trip: {e}")
        raise HTTPException(status_code=500, detail="Could not process reservation.")