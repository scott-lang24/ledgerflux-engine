import os
import shutil
import base64
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
import uvicorn
import requests
from fpdf import FPDF

# Import our new Billion-Dollar Brain
from core.contract_engine import engine

app = FastAPI()

# --- PRE-FLIGHT: LOAD CONTRACTS INTO MEMORY ---
print("[*] Initializing Dynamic Contract Engine...")
# We load OmniActive's dummy contract into the engine's RAM
engine.ingest_rate_card("OMNIACTIVE-UUID-001", "contracts/omniactive_rates.csv")


def generate_pdf_base64(audit_data):
    """Forges the Dispute Certificate as a PDF in memory and returns a Base64 string."""
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(217, 83, 79)
    pdf.cell(200, 10, txt="LEDGERFLUX FORENSIC AUDIT CERTIFICATE", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt=f"Invoice Reference: {audit_data['invoice_ref']}", ln=True)
    pdf.cell(200, 10, txt=f"Carrier: {audit_data['carrier']}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Leakage Detected: {audit_data['leakage_amount']}", ln=True)
    
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Audit Finding: {audit_data['reason']}")
    pdf.ln(20)
    
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 10, txt="This document is a certified system-generated dispute artifact. Forward directly to your carrier representative to execute credit recovery.")
    
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return base64.b64encode(pdf_bytes).decode('utf-8')


def execute_forensic_audit(file_path: str, sender_email: str):
    print(f"\n[*] Initiating Deep Scan on {file_path} for {sender_email}...")
    
    # ---------------------------------------------------------
    # THE UPGRADE: LIVE MATHEMATICAL AUDIT
    # ---------------------------------------------------------
    # Imagine our OCR just ripped this data off the FedEx PDF:
    mock_ocr_data = {
        "carrier": "FEDEX",
        "billed_amount": 135.00,  # FedEx billed them $135!
        "billed_weight": 15.0,    # It's a 15kg package
        "zone": 4                 # Going to Zone 4
    }

    print(f"[*] OCR Extraction: {mock_ocr_data['carrier']} billed ${mock_ocr_data['billed_amount']} for {mock_ocr_data['billed_weight']}kg to Zone {mock_ocr_data['zone']}.")
    print(f"[*] Verifying against OmniActive Contract...")

    # Run the live audit!
    audit_result = engine.execute_audit("OMNIACTIVE-UUID-001", mock_ocr_data)

    if audit_result["status"] != "DISCREPANCY_FOUND":
        print("[+] Audit Clean. No leakage detected. Skipping dispatch.")
        return

    print(f"[!] LEAKAGE FOUND: {audit_result['leakage_amount']}. {audit_result['reason']}")
    
    # Map the output for the PDF Generator
    final_dispatch_data = {
        "discrepancy_found": True,
        "leakage_amount": audit_result['leakage_amount'],
        "reason": audit_result['reason'],
        "carrier": mock_ocr_data['carrier'],
        "invoice_ref": file_path.split("/")[-1]
    }

    print("[*] Forging PDF Certificate Artifact...")
    pdf_b64 = generate_pdf_base64(final_dispatch_data)

    print("[*] PDF forged. Handing off to Node.js Dispatcher...")
    
    node_api_url = "http://127.0.0.1:3000/api/dispatch-certificate" 
    payload = {
        "to_email": sender_email, 
        "audit_data": final_dispatch_data,
        "pdf_attachment": pdf_b64
    }
    
    try:
        response = requests.post(node_api_url, json=payload)
        if response.status_code == 200:
            print(f"[+] SUCCESS: Email + Contract PDF Certificate fired to {sender_email}")
        else:
            print(f"[-] Node API Error: {response.status_code}")
    except Exception as e:
        print(f"[-] Node API Connection Failed: {e}")

    if os.path.exists(file_path):
        os.remove(file_path)


@app.post("/inbound-parse")
async def receive_inbound_email(
    background_tasks: BackgroundTasks,
    to: str = Form(None),
    From: str = Form(None),
    attachment1: UploadFile = File(...) 
):
    print("\n[>>>] INCOMING SECURE PAYLOAD [<<<]")
    sender_email = From if From else "shabbir@ledgerflux.com"
    
    temp_dir = "temp_inbound"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, attachment1.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(attachment1.file, buffer)

    background_tasks.add_task(execute_forensic_audit, temp_path, sender_email)
    return {"status": "success"}


if __name__ == "__main__":
    print("[*] Webhook Catcher Online. Awaiting transmission...")
    uvicorn.run(app, host="127.0.0.1", port=8000)