# database/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database.config import Base

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    subdomain = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contracts = relationship("CarrierContract", back_populates="client")

class CarrierContract(Base):
    __tablename__ = "carrier_contracts"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    carrier_name = Column(String, index=True)
    service_type = Column(String) # LTL, Ocean, Air
    rate_valid_from = Column(DateTime)
    rate_valid_to = Column(DateTime)
    
    client = relationship("Client", back_populates="contracts")
    rate_items = relationship("RateLineItem", back_populates="contract")

class RateLineItem(Base):
    __tablename__ = "rate_line_items"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("carrier_contracts.id"), nullable=False)
    charge_type = Column(String) # Base, Fuel, Liftgate, D&D
    min_amount = Column(Float)
    max_amount = Column(Float)
    calculation_type = Column(String) # percentage, fixed
    
    contract = relationship("CarrierContract", back_populates="rate_items")

# ---------------------------------------------------------

# api/upload.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
import zipfile
import shutil
import os
from tempfile import NamedTemporaryFile

router = APIRouter()

def process_pdf_batch(extracted_dir: str, client_id: int):
    # This is where your Celery/Bull queue logic will go
    # For now, it iterates through the extracted PDFs
    for filename in os.listdir(extracted_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(extracted_dir, filename)
            # queue_task.delay(file_path, client_id)
            print(f"Queued for processing: {filename} for Client {client_id}")
    
    # Cleanup after queueing
    shutil.rmtree(extracted_dir)

@router.post("/api/upload/batch")
async def upload_batch_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_id: int = 1 # In reality, get this from JWT/Auth context
):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed for batch processing.")

    # Save uploaded zip to a temporary file
    with NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_zip_path = tmp.name

    # Create a unique directory for extraction
    extracted_dir = f"/tmp/ledgerflux_batch_{client_id}_{os.urandom(4).hex()}"
    os.makedirs(extracted_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
            # Basic security check to prevent zip slip
            for member in zip_ref.namelist():
                if member.endswith('.pdf'):
                    zip_ref.extract(member, extracted_dir)
    except zipfile.BadZipFile:
        os.remove(tmp_zip_path)
        raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file.")
    finally:
        os.remove(tmp_zip_path) # Clean up the zip file

    # Hand off the extracted directory to background worker
    background_tasks.add_task(process_pdf_batch, extracted_dir, client_id)

    return {"status": "success", "message": "Batch ZIP received. PDFs queued for forensic audit."}
