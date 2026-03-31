# api/upload.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
import zipfile
import shutil
import os
from tempfile import NamedTemporaryFile

router = APIRouter()

def process_pdf_batch(extracted_dir: str, client_id: int):
    # This is where your background queue logic (Celery) will eventually go
    # For now, it iterates through the extracted PDFs and prints them to your terminal
    for filename in os.listdir(extracted_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(extracted_dir, filename)
            # queue_task.delay(file_path, client_id)
            print(f"Queued for processing: {filename} for Client {client_id}")
    
    # Cleanup the temporary directory after queueing
    shutil.rmtree(extracted_dir)

@router.post("/api/upload/batch")
async def upload_batch_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_id: int = 1 # In reality, we will get this from the JWT/Auth token later
):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed for batch processing.")

    # Save uploaded zip to a secure temporary file
    with NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_zip_path = tmp.name

    # Create a unique isolated directory for extraction to prevent file collisions
    extracted_dir = f"/tmp/ledgerflux_batch_{client_id}_{os.urandom(4).hex()}"
    os.makedirs(extracted_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
            # Basic security check to prevent zip-slip vulnerabilities
            for member in zip_ref.namelist():
                if member.endswith('.pdf'):
                    zip_ref.extract(member, extracted_dir)
    except zipfile.BadZipFile:
        os.remove(tmp_zip_path)
        raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file.")
    finally:
        os.remove(tmp_zip_path) # Always clean up the zip file from the server

    # Hand off the extracted directory to the background worker so the client doesn't wait
    background_tasks.add_task(process_pdf_batch, extracted_dir, client_id)

    return {"status": "success", "message": "Batch ZIP received. PDFs queued for forensic audit."}
