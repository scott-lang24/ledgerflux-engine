import requests
import os

# CONFIGURATION
WEBHOOK_URL = "http://localhost:8000/inbound-parse"
TEST_FILE = "sample_invoice.pdf"

def simulate_stark_payload():
    # 1. PRE-FLIGHT CHECK: Ensure the payload exists
    if not os.path.exists(TEST_FILE):
        print(f"[*] Generating emergency test document: {TEST_FILE}")
        with open(TEST_FILE, "wb") as f:
            f.write(b"%PDF-1.1\n%Stark Industries Freight Data")

    # 2. CONSTRUCT DATA PAYLOAD
    # SendGrid sends metadata as standard form fields
    payload_fields = {
        "to": "audit@ledgerflux.com",
        "From": "stark@starkindustries.com",
        "subject": "Q3 Logistics Audit - Urgent",
        "attachments": "1" 
    }

    # 3. CONSTRUCT FILE STREAM
    # We use a context manager to keep the file open during transmission
    try:
        with open(TEST_FILE, "rb") as f:
            # SendGrid labels files as attachment1, attachment2, etc.
            files = {
                "attachment1": (TEST_FILE, f, "application/pdf")
            }

            print(f"[*] Firing Forensic Payload at {WEBHOOK_URL}...")
            
            # CRITICAL: We send 'data' for fields and 'files' for the PDF
            response = requests.post(
                WEBHOOK_URL, 
                data=payload_fields, 
                files=files
            )

        # 4. POST-FLIGHT ANALYSIS
        if response.status_code == 200:
            print("[+] Handshake Successful.")
            print(f"[+] Engine Response: {response.json()}")
        else:
            print(f"[-] Handshake Failed. Status: {response.status_code}")
            print(f"[-] Error Detail: {response.text}")

    except Exception as e:
        print(f"[!] System Critical Error during simulation: {e}")

if __name__ == "__main__":
    simulate_stark_payload()