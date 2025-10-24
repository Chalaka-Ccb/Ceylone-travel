# from fastapi import FastAPI
# from app.api.v1.api import api_router
#
# app = FastAPI(
#     title="Sri Lanka Travel Planner API",
#     description="Backend service for the smart travel planning application.",
#     version="1.0.0"
# )
#
# # Include the v1 router
# app.include_router(api_router, prefix="/api/v1")
#
# @app.get("/", tags=["Health"])
# def read_root():
#     """
#     Root endpoint to check if the API is running.
#     """
#     return {"status": "ok", "message": "Welcome to the Travel Planner API!"}
#


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router

app = FastAPI(
    title="Sri Lanka Travel Planner API",
    description="Backend service for the smart travel planning application.",
    version="1.0.0"
)

# ------------------------------------------------------------
# ✅ Enable CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# ✅ Include API routes
# ------------------------------------------------------------
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def read_root():
    """Root endpoint to check if the API is running."""
    return {"status": "ok", "message": "Welcome to the Travel Planner API!"}

# Run with:
# uvicorn app.main:app --reload