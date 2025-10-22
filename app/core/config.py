import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# +++ ADD THIS DEBUG LINE +++
print(f"--- DEBUG: ORS_API_KEY loaded as: {os.getenv('ORS_API_KEY')} ---")
# +++++++++++++++++++++++++++

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    ORS_API_KEY: str = os.getenv("ORS_API_KEY")
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY") # Keep this, just in case
    CLERK_ISSUER_URL: str = os.getenv("CLERK_ISSUER_URL") # <-- ADD THIS

    # Bandaranaike International Airport (Katunayake)
    STARTING_POINT_COORDS: tuple[float, float] = (79.8841, 7.1807)
    DAILY_BUDGET_PER_PERSON: int = 150

settings = Settings()