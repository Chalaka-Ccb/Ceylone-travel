# File: app/api/v1/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase_client import supabase_client
from app.core.auth import get_authenticated_user
from app.models.schemas import ClerkUser, UserProfileResponse, UserProfileUpdate
import sys

router = APIRouter()


# Dependency to get the DB client (same as in trips.py)
def get_db():
    return supabase_client


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
        current_user: ClerkUser = Depends(get_authenticated_user),
        db: Client = Depends(get_db)
):
    """
    GET /api/v1/users/me
    Fetches the authenticated user's profile from the 'users' table.
    """
    print(f"--- Fetching profile for user: {current_user.id} ---")
    try:
        response = db.table('users').select(
            "id, first_name, last_name, email, address, post_code, country, mobile_phone, passport_number"
        ).eq('id', current_user.id).single().execute()

        if not response.data:
            # This shouldn't happen if the user has generated a trip,
            # but it's good to have a fallback.
            print(f"--- No profile found for {current_user.id}, returning minimal data ---")
            return UserProfileResponse(
                id=current_user.id,
                email=current_user.email
            )

        return response.data

    except Exception as e:
        print(f"---!!! Error fetching user profile: {e} !!!---", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {e}")


@router.put("/me", response_model=UserProfileResponse)
def update_current_user_profile(
        profile_update: UserProfileUpdate,
        current_user: ClerkUser = Depends(get_authenticated_user),
        db: Client = Depends(get_db)
):
    """
    PUT /api/v1/users/me
    Updates the authenticated user's profile in the 'users' table.
    """
    # exclude_unset=True is important: it only includes fields
    # that were actually sent in the request body.
    # This matches your frontend's 'updatePayload' logic perfectly.
    update_data = profile_update.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No changes to update.")

    print(f"--- Updating profile for user: {current_user.id} ---")
    print(f"--- Update data: {update_data} ---")

    try:
        response = db.table('users').update(
            update_data
        ).eq('id', current_user.id).select(
            "id, first_name, last_name, email, address, post_code, country, mobile_phone, passport_number"
        ).execute()

        if not response.data:
            print(f"---!!! Error: Failed to update or find user {current_user.id} ---", file=sys.stderr)
            raise HTTPException(status_code=404, detail="User profile not found to update.")

        print("--- Update successful ---")
        return response.data[0]  # Return the updated profile data

    except Exception as e:
        print(f"---!!! Error updating user profile: {e} !!!---", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=f"Error updating profile: {e}")