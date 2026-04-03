# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import upload
from database.config import engine, Base

# Creates all database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LedgerFlux Core API")

# --- ADD THIS CORS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing. We will restrict this in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------

# Plugs your batch upload route into the main server
app.include_router(upload.router)

@app.get("/")
def health_check():
    return {"status": "LedgerFlux Engine is Online"}
