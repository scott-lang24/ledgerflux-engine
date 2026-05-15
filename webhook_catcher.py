import os
import shutil
import base64
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
import uvicorn
import requests
from fpdf import FPDF

# The Brain, The Eyes, and The Gatekeeper
from core.contract_engine import engine
from core.ocr_engine import ocr_vision
from core.tenant_router import router

app = FastAPI()

print("[*] Booting LedgerFlux Mainframe...")
# Load test contracts
engine.ingest_rate_card("OMNIACTIVE-UUID-001", "contracts/omniactive_rates.csv")
# Let's map your Stark Industries test email to OmniActive's contract so the test works
engine.ingest_rate_card("STARK-UUID-999", "contracts/omniactive_rates.csv") 

def generate_pdf_base64(audit_data):
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
    print(f"\n[*] Pipeline engaged for payload from: {sender_email}")
    
    # 1. GATEKEEPER: Identify Tenant via Email Domain
    tenant_id = router.identify_tenant(sender_email)
    if not tenant_id:
        print("[-] Audit Aborted: Sender is not a registered Enterprise client.")
        if os.path.exists(file_path): os.remove(file_path)
        return

    # 2. VISION: Extract actual data from the PDF
    extracted_data = ocr_vision.extract_invoice_data(file_path)
    
    # 3. BRAIN: Audit against their specific contract
    audit_result = engine.execute_audit(tenant_id, extracted_data)

    if audit_result["status"] != "DISCREPANCY_FOUND":
        print("[+] Audit Clean. No leakage detected. File archived.")
        if os.path.exists(file_path): os.remove(file_path)
        return

    print(f"[!] LEAKAGE FOUND: {audit_result['leakage_amount']}. {audit_result['reason']}")
    
    final_dispatch_data = {
        "discrepancy_found": True,
        "leakage_amount": audit_result['leakage_amount'],
        "reason": audit_result['reason'],
        "carrier": extracted_data['carrier'],
        "invoice_ref": file_path.split("/")[-1]
    }

    pdf_b64 = generate_pdf_base64(final_dispatch_data)
    
    node_api_url = "http://127.0.0.1:3000/api/dispatch-certificate" 
    payload = {"to_email": sender_email, "audit_data": final_dispatch_data, "pdf_attachment": pdf_b64}
    
    try:
        response = requests.post(node_api_url, json=payload)
        if response.status_code == 200:
            print(f"[+] SUCCESS: Artifact dispatched to {sender_email}")
    except Exception as e:
        print(f"[-] Node API Connection Failed: {e}")

    if os.path.exists(file_path):
        os.remove(file_path)


@app.post("/inbound-parse")
async def receive_inbound_email(background_tasks: BackgroundTasks, to: str = Form(None), From: str = Form(None), attachment1: UploadFile = File(...)):
    print("\n[>>>] INBOUND TRANSMISSION INTERCEPTED [<<<]")
    sender_email = From if From else "unknown@domain.com"
    
    temp_dir = "temp_inbound"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, attachment1.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(attachment1.file, buffer)

    background_tasks.add_task(execute_forensic_audit, temp_path, sender_email)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)