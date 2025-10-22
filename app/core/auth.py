import httpx
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, jwk
from jose.exceptions import JOSEError
from typing import Dict
from app.models.schemas import ClerkUser
from app.core.config import settings  # Import your settings

# --- Configuration ---
# We will cache the Clerk public keys (JWKS) to avoid fetching them on every request
JWKS_CACHE = {}
oauth2_scheme = HTTPBearer()


async def get_clerk_jwks() -> Dict:
    """
    Fetches Clerk's JSON Web Key Set (JWKS) to verify token signatures.
    Caches the keys for performance.
    """
    global JWKS_CACHE
    if JWKS_CACHE:
        return JWKS_CACHE

    if not settings.CLERK_ISSUER_URL:
        raise Exception("CLERK_ISSUER_URL is not set in .env")

    jwks_url = f"{settings.CLERK_ISSUER_URL}/.well-known/jwks.json"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()  # Raise an error for bad responses
            jwks = response.json()
            JWKS_CACHE = {key['kid']: key for key in jwks['keys']}
            return JWKS_CACHE
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch authentication keys.")


def get_key(token: str, jwks: Dict) -> Dict:
    """
    Finds the correct public key (from the JWKS) to verify the token's signature.
    """
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token: 'kid' missing from header")

        key = jwks.get(kid)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token: Key ID not found")

        return key
    except JOSEError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def get_authenticated_user(creds: HTTPAuthorizationCredentials = Security(oauth2_scheme)) -> ClerkUser:
    """
    A FastAPI dependency that validates the Clerk JWT (token)
    from the Authorization: Bearer <token> header.

    This version verifies the token MANUALLY.
    """
    token = creds.credentials

    try:
        # 1. Get the public keys from Clerk
        jwks = await get_clerk_jwks()

        # 2. Find the specific key that signed this token
        key = get_key(token, jwks)

        # 3. Decode and validate the token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER_URL,
            # We don't check audience, but you could add it:
            # audience="your_audience"
        )

        # 4. Token is valid! Get the user ID (subject)
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: User ID ('sub') missing")

        # 5. Get user email from the token payload (optional, but good to have)
        # Note: This might be in a different claim, check your token in Clerk dashboard
        user_email = payload.get('email')

        return ClerkUser(
            id=user_id,
            email=user_email
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTClaimsError as e:
        raise HTTPException(status_code=401, detail=f"Token claims error: {e}")
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )