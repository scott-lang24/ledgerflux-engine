import requests
import os

# 1. LOCAL CONFIG
WEBHOOK_URL = "http://localhost:8000/inbound-parse"
FILENAME = "sample_invoice.pdf"

def find_the_target():
    # Diagnostic: Where are we?
    current_dir = os.getcwd()
    print(f"[*] Current Command Center: {current_dir}")
    
    # Check current folder
    if os.path.exists(FILENAME):
        return FILENAME
    
    # Check if we are outside the LedgerFlux folder
    alt_path = os.path.join(current_dir, "LedgerFlux", FILENAME)
    if os.path.exists(alt_path):
        return alt_path

    # Check for common subfolders
    for root, dirs, files in os.walk(current_dir):
        if FILENAME in files:
            return os.path.join(root, FILENAME)
            
    return None

def fire_payload():
    target_path = find_the_target()
    
    if not target_path:
        print(f"[!] CRITICAL FAILURE: {FILENAME} is missing from the mainframe.")
        print("[*] Creating a dummy file to bypass...")
        target_path = FILENAME
        with open(target_path, "wb") as f:
            f.write(b"%PDF-1.1\n%Stark-Dummy-Invoice")

    print(f"[+] Target Locked: {target_path}")

    payload_fields = {
        "to": "audit@ledgerflux.com",
        "From": "stark@starkindustries.com",
        "subject": "Q3 Forensic Audit"
    }

    with open(target_path, "rb") as f:
        # We MUST ensure the key is 'attachment1' to match the Webhook Greedy Logic
        files = {
            "attachment1": (FILENAME, f, "application/pdf")
        }

        print(f"[*] Firing Payload...")
        try:
            r = requests.post(WEBHOOK_URL, data=payload_fields, files=files)
            print(f"[+] Webhook Response: {r.json()}")
        except Exception as e:
            print(f"[-] Handshake Failed: {e}")

if __name__ == "__main__":
    fire_payload()