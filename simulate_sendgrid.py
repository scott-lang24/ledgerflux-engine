import requests
import os

# 1. Target URL (Your Python Catcher Terminal)
WEBHOOK_URL = "http://localhost:8000/inbound-parse"

# 2. Define the Payload (This was missing or out of order in your script)
payload_data = {
    "to": "audit@ledgerflux.com",
    "From": "shabbir@testcompany.com",
    "subject": "Fwd: Q3 Freight Invoices FedEx"
}

# 3. Path to your test PDF
test_pdf_path = "sample_invoice.pdf"

# Check if the file actually exists to avoid a FileNotFoundError
if not os.path.exists(test_pdf_path):
    print(f"[-] ERROR: {test_pdf_path} not found. Please put a PDF in this folder.")
else:
    # 4. Open the file and fire the request
    with open(test_pdf_path, "rb") as f:
        files = {
            "attachment1": (test_pdf_path, f, "application/pdf")
        }

        print("[*] Firing simulated SendGrid payload at local Webhook...")
        try:
            response = requests.post(WEBHOOK_URL, data=payload_data, files=files)
            print(f"[+] Status Code: {response.status_code}")
            print(f"[+] Response JSON: {response.json()}")
        except Exception as e:
            print(f"[-] Network Error: {e}")