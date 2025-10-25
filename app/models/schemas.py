# # from pydantic import BaseModel, EmailStr
# # from typing import List, Optional
# #
# # # --- ADD THIS MODEL ---
# # class ClerkUser(BaseModel):
# #     """
# #     Holds the authenticated user data from the Clerk token dependency.
# #     """
# #     id: str
# #     email: Optional[EmailStr] = None
# #     # You can add more fields from the token if needed
# #     # e.g., first_name: Optional[str] = None
# #     # e.g., last_name: Optional[str] = None
# #
# #
# # # --- Trip Generation (Screenshot 1) ---
# #
# # class TripGenerationRequest(BaseModel):
# #     num_people: int
# #     num_days: int
# #     budget: float
# #     interests: List[str] # e.g., ["nature", "history"]
# #     # You can add these later:
# #     # meal_options: bool = False
# #     # accommodation_options: bool = False
# #
# # class LocationResponse(BaseModel):
# #     id: str
# #     name: str
# #     description: Optional[str]
# #     image_url: Optional[str]
# #     coordinates: dict # {"longitude": 79.8, "latitude": 7.1}
# #
# # class TripDayResponse(BaseModel):
# #     day_number: int
# #     locations: List[LocationResponse]
# #
# # class TripResponse(BaseModel):
# #     id: str
# #     num_people: int
# #     num_days: int
# #     total_budget: float
# #     itinerary: List[TripDayResponse]
# #     user_id: Optional[str] = None # <-- ADD THIS to link trip to user
# #
# # # --- Reservation (Screenshot 4) ---
# #
# # class ReservationRequest(BaseModel):
# #     trip_id: str # The ID of the generated trip they are booking
# #     first_name: str
# #     last_name: str
# #     email: EmailStr
# #     address: Optional[str]
# #     post_code: Optional[str]
# #     country: Optional[str]
# #     mobile_phone: Optional[str]
# #     passport_number: str # The non-editable unique ID
# #
# # class UserResponse(BaseModel):
# #     id: str
# #     email: EmailStr
# #     first_name: str
# #     last_name: str
# #
# #     class Config:
# #         from_attributes = True # <-- New name
#
# # File: app/models/schemas.py
#
# from pydantic import BaseModel, EmailStr
# from typing import List, Optional
#
# # --- ADD THIS MODEL ---
# class ClerkUser(BaseModel):
#     """
#     Holds the authenticated user data from the Clerk token dependency.
#     """
#     id: str
#     email: Optional[EmailStr] = None
#     # You can add more fields from the token if needed
#     # e.g., first_name: Optional[str] = None
#     # e.g., last_name: Optional[str] = None
#
#
# # --- Trip Generation (Screenshot 1) ---
#
# class TripGenerationRequest(BaseModel):
#     num_people: int
#     num_days: int
#     budget: float
#     interests: List[str] # e.g., ["nature", "history"]
#     # You can add these later:
#     # meal_options: bool = False
#     # accommodation_options: bool = False
#
# class LocationResponse(BaseModel):
#     id: str
#     name: str
#     description: Optional[str]
#     image_url: Optional[str]
#     coordinates: dict # {"longitude": 79.8, "latitude": 7.1}
#
# class TripDayResponse(BaseModel):
#     day_number: int
#     locations: List[LocationResponse]
#     route_geometries: List[Optional[dict]] # <-- ADD THIS FIELD
#
# class TripResponse(BaseModel):
#     id: str
#     num_people: int
#     num_days: int
#     total_budget: float
#     itinerary: List[TripDayResponse]
#     user_id: Optional[str] = None
#
# # --- Reservation (Screenshot 4) ---
#
# class ReservationRequest(BaseModel):
#     trip_id: str # The ID of the generated trip they are booking
#     first_name: str
#     last_name: str
#     email: EmailStr
#     address: Optional[str]
#     post_code: Optional[str]
#     country: Optional[str]
#     mobile_phone: Optional[str]
#     passport_number: str # The non-editable unique ID
#
# class UserResponse(BaseModel):
#     id: str
#     email: EmailStr
#     first_name: str
#     last_name: str
#
#     class Config:
#         from_attributes = True

# File: app/models/schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional

# --- ClerkUser Model (Existing) ---
class ClerkUser(BaseModel):
    """
    Holds the authenticated user data from the Clerk token dependency.
    """
    id: str
    email: Optional[EmailStr] = None


# --- Trip Generation Models (Existing) ---

class TripGenerationRequest(BaseModel):
    num_people: int
    num_days: int
    budget: float
    interests: List[str]

class LocationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    image_url: Optional[str]
    coordinates: dict # {"longitude": 79.8, "latitude": 7.1}

class TripDayResponse(BaseModel):
    day_number: int
    locations: List[LocationResponse]
    route_geometries: List[Optional[dict]] # <-- This field is from our last change

class TripResponse(BaseModel):
    id: str
    num_people: int
    num_days: int
    total_budget: float
    itinerary: List[TripDayResponse]
    user_id: Optional[str] = None


# --- Reservation Models (Existing) ---

class ReservationRequest(BaseModel):
    trip_id: str
    first_name: str
    last_name: str
    email: EmailStr
    address: Optional[str]
    post_code: Optional[str]
    country: Optional[str]
    mobile_phone: Optional[str]
    passport_number: str

# --- UserResponse (Existing, but we will rename for clarity) ---
# This was for the /reserve-trip endpoint
class ReservationUserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


# --- (NEW) User Profile Models ---
# For your new GET /api/v1/users/me endpoint
class UserProfileResponse(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    address: Optional[str] = None
    post_code: Optional[str] = None
    country: Optional[str] = None
    mobile_phone: Optional[str] = None
    passport_number: Optional[str] = None

    class Config:
        from_attributes = True # To read data from the database object

# For your new PUT /api/v1/users/me endpoint
# This matches the 'editableFields' in your frontend
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    post_code: Optional[str] = None
    country: Optional[str] = None
    mobile_phone: Optional[str] = None
    passport_number: Optional[str] = None