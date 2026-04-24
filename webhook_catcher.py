import os
import shutil
from fastapi import FastAPI, Request, File, UploadFile, Form, BackgroundTasks
import requests
import uvicorn

app = FastAPI(title="LedgerFlux Inbound Gateway")

@app.post("/inbound-parse")
async def receive_inbound_email(
    background_tasks: BackgroundTasks,
    request: Request,
    to: str = Form(...),
    From: str = Form(...),
):
    form_data = await request.form()
    
    # Check for files in both 'attachmentX' format AND standard 'files' format
    attachments = []
    for key, value in form_data.items():
        if isinstance(value, UploadFile):
            attachments.append(value)
    
    sender_email = From
    print(f"[+] INCOMING ALERT: Audit intercepted from {sender_email}")
    print(f"[+] Files detected in stream: {len(attachments)}")

    if not attachments:
        return {"status": "ignored", "reason": "No files found in multipart stream"}

    file_obj = attachments[0]
    
    # Ensure directory exists
    temp_dir = "temp_inbound"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_path = os.path.join(temp_dir, file_obj.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file_obj.file, buffer)

    background_tasks.add_task(execute_forensic_audit, temp_path, sender_email)

    return {"status": "received", "message": f"LedgerFlux Engine engaging on {file_obj.filename}"}

    # We process the first attachment (The Carrier Invoice)
    file_obj = attachments[0]
    
    if not file_obj.filename.lower().endswith(".pdf"):
        return {"status": "ignored", "reason": "Target is not a PDF format"}

    # Secure the payload in a temporary directory
    temp_dir = "temp_inbound"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file_obj.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file_obj.file, buffer)

    # Hand off to the core engine in the background to prevent SendGrid timeout
    background_tasks.add_task(execute_forensic_audit, temp_path, sender_email)

    return {"status": "received", "message": "Payload secured. LedgerFlux engine engaging."}


def execute_forensic_audit(file_path: str, sender_email: str):
    """
    The Brain Connection: Where Webhook meets SCAM_DATABASE
    """
    print(f"[*] Initiating Deep Scan on {file_path} for {sender_email}...")
    
    # TODO: Import your analyzer.py or master_run.py OCR logic here.
    # Example: result = ocr_engine.process_invoice(file_path)
    
    # MOCK RESULT FOR V1 TESTING
    audit_result = {
        "discrepancy_found": True,
        "leakage_amount": "$430.00",
        "reason": "Dimensional Weight Bloat (Carrier billed 150 lbs, actual DIM is 112 lbs)",
        "carrier": "FedEx",
        "invoice_ref": file_path.split("/")[-1]
    }

    # FIRING THE NODE.JS EMAIL CANNON
    print("[*] Scan complete. Triggering Node.js Dispatcher for HTML Certificate...")
    
    # NOTE: Change this to your Render Node.js URL when deploying
    node_api_url = "http://localhost:3000/api/dispatch-certificate" 
    
    payload = {
        "to_email": sender_email,
        "audit_data": audit_result
    }
    
    try:
        response = requests.post(node_api_url, json=payload)
        if response.status_code == 200:
            print("[+] HTML Dispute Certificate fired back to client successfully.")
        else:
            print(f"[-] Node API returned status: {response.status_code}")
    except Exception as e:
        print(f"[-] Node API Connection Failed: {e}")

    # Burn the evidence
    if os.path.exists(file_path):
        os.remove(file_path)
        print("[*] Temp payload deleted.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)