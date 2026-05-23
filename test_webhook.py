import requests
import json

# The payload mimics an email/invoice being forwarded by a client's system
payload = {
    "tenant_id": "capital_foods_001",
    "invoice_data": {
        "carrier": "FEDEX",
        "billed_amount": 450.00,
        "billed_weight": 25.0,
        "zone": 5
    }
}

print("[*] Firing simulated webhook from Capital Foods ERP...")

# Hitting your local Node.js/Python webhook catcher
try:
    response = requests.post(
        "http://127.0.0.1:3000/api/audit/webhook", # Assuming your server is on port 3000
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"[+] Server Response: {response.status_code}")
    print(f"[+] Payload Result: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"[-] Webhook failed to connect: {e}")