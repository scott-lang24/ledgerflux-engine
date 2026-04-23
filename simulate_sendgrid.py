import requests

# This points to your local FastAPI webhook catcher
WEBHOOK_URL = "http://localhost:8000/inbound-parse"

# We need a dummy PDF to test the engine
test_pdf_path = "sample_invoice.pdf" # Ensure you have a dummy PDF named this in the same folder

with open(test_pdf_path, "rb") as f:
    # This dictionary perfectly mimics SendGrid's webhook structure
    payload_data = {
        "to": "audit@ledgerflux.com",
        "From": "shabbir@testcompany.com", # SendGrid capitalizes 'From'
        "subject": "Fwd: Q3 Freight Invoices FedEx"
    }
    
    files = {
        "attachment1": (test_pdf_path, f, "application/pdf")
    }

    print("[*] Firing simulated SendGrid payload at local Webhook...")
    response = requests.post(WEBHOOK_URL, data=payload_data, files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")