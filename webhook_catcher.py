from fastapi import FastAPI, Request, File, UploadFile, Form
from supabase import create_client
import tempfile
import subprocess
import json
import os
import threading
import datetime

# --- 1. INITIALIZE FASTAPI & SUPABASE ---
app = FastAPI(title="LedgerFlux Inbound Email Webhook")

# (In production, load these securely via environment variables like we did in Streamlit)
SUPABASE_URL = os.getenv("SUPABASE_URL","https://dnxmlcrivhlrhjttuepj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRueG1sY3JpdmhscmhqdHR1ZXBqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3MzE2NTMsImV4cCI6MjA5MTMwNzY1M30.tV_kVUjbdxADZGUQnsGWpnQstWw0OR2565xcVQ-k3_8")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. THE GHOST WORKER (Reused from Phase 4) ---
def background_processor(file_bytes, client_id, filename):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, filename)
            with open(pdf_path, "wb") as f:
                f.write(file_bytes)
                
            # Fire the LedgerFlux OCR Engine natively
            output = subprocess.check_output(['python3', 'core/analyzer.py', pdf_path], text=True)
            json_match = re.search(r'\{[\s\S]*\}', output)
            
            if json_match:
                res = json.loads(json_match.group(0))
                
                # Lock data into the Vault silently
                supabase.table('audit').insert({
                    "clientId": client_id,
                    "invoice_number": res['invoice_id'],
                    "carrier_name": res['carrier'],
                    "status": res['status'],
                    "total_billed": res['total_billed'],
                    "total_savings": res['total_savings']
                }).execute()
                print(f"[SUCCESS] Inbound Email Invoice {res['invoice_id']} audited and secured.")
    except Exception as e:
        print(f"[FATAL] Webhook Ghost Worker Crashed: {e}")

# --- 3. THE SENDGRID INBOUND PARSE ENDPOINT ---
@app.get("/")
def health_check():
    return {"status": "🟢 LedgerFlux Webhook Catcher is Online and Listening."}

@app.post("/api/webhooks/inbound_email")
async def handle_inbound_email(
    request: Request,
    to: str = Form(...),          # Who the email was sent to (e.g., omniactive@ledgerflux.com)
    from_email: str = Form(alias="from"), # The carrier's email
    attachments: int = Form(0)    # Number of attachments
):
    """
    SendGrid hits this endpoint the second an email arrives.
    """
    print(f"[SYS] Intercepted email from {from_email} to {to}")
    
    # 1. Routing: Figure out which client this belongs to based on the email address
    client_prefix = to.split('@')[0].upper() # e.g., 'omniactive' -> 'OMNIACTIVE'
    client_uuid = f"{client_prefix}-UUID-001" # In production, look this up in the DB
    
    # 2. Extract the PDF attachments
    form_data = await request.form()
    
    if attachments > 0:
        for i in range(1, attachments + 1):
            file_field = f"attachment{i}"
            if file_field in form_data:
                upload_file = form_data[file_field]
                if upload_file.filename.lower().endswith('.pdf'):
                    file_bytes = await upload_file.read()
                    
                    # 3. Hand off to the ghost worker so the API responds instantly
                    thread = threading.Thread(
                        target=background_processor, 
                        args=(file_bytes, client_uuid, upload_file.filename)
                    )
                    thread.start()
                    
        return {"status": "success", "message": f"Routed {attachments} attachments to Ghost Workers."}
    
    return {"status": "ignored", "message": "No attachments found."}