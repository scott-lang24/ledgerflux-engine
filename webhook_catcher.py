import os
import shutil
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
import uvicorn
import requests

app = FastAPI()

def execute_forensic_audit(file_path: str, sender_email: str):
    """
    The Core Engine. We extract, analyze, and dispatch.
    """
    print(f"\n[*] Initiating Deep Scan on {file_path} for {sender_email}...")
    
    # MOCK ENGINE LOGIC (Until we plug your real OCR/SCAM_DATABASE here)
    audit_result = {
        "discrepancy_found": True,
        "leakage_amount": "$430.00",
        "reason": "Dimensional Weight Bloat (Carrier billed 150 lbs, actual DIM is 112 lbs)",
        "carrier": "FedEx",
        "invoice_ref": file_path.split("/")[-1]
    }

    print("[*] Scan complete. Leakage found. Triggering Node.js Dispatcher...")
    
    # Ping the Node.js API to send the email
    node_api_url = "http://127.0.0.1:3000/api/dispatch-certificate" 
    payload = {"to_email": sender_email, "audit_data": audit_result}
    
    try:
        response = requests.post(node_api_url, json=payload)
        if response.status_code == 200:
            print(f"[+] SUCCESS: HTML Dispute Certificate fired to {sender_email}")
        else:
            print(f"[-] Node API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[-] Node API Connection Failed: Is Terminal 1 (Node) running on port 3000? Error: {e}")

    # Burn the evidence to keep the server clean
    if os.path.exists(file_path):
        os.remove(file_path)
        print("[*] Temp payload deleted.")


@app.post("/inbound-parse")
async def receive_inbound_email(
    background_tasks: BackgroundTasks,
    to: str = Form(None),
    From: str = Form(None),
    attachment1: UploadFile = File(...) 
):
    print("\n[>>>] INCOMING SECURE PAYLOAD [<<<]")
    sender_email = From if From else "shabbir@ledgerflux.com" # Default to your email for testing
    print(f"[*] Sender detected: {sender_email}")
    
    temp_dir = "temp_inbound"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, attachment1.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(attachment1.file, buffer)

    # Hand off to the engine so the webhook returns immediately
    background_tasks.add_task(execute_forensic_audit, temp_path, sender_email)

    return {"status": "success", "message": "Payload secured. Engine engaging."}

if __name__ == "__main__":
    print("[*] Webhook Catcher Online. Awaiting transmission...")
    uvicorn.run(app, host="127.0.0.1", port=8000)