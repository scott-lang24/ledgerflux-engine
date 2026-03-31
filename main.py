# main.py
from fastapi import FastAPI
from api import upload
from database.config import engine, Base

# This creates all your database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LedgerFlux Core API")

# This plugs your batch upload route into the main server
app.include_router(upload.router)

@app.get("/")
def health_check():
    return {"status": "LedgerFlux Engine is Online"}
