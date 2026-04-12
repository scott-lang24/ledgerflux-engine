import requests
import sys
import os

# The address of your LedgerFlux Enterprise API
API_URL = "http://localhost:3000/api/webhook/ingest"

# The Secret Key (If this is wrong, Node.js will slam the door)
API_KEY = "lf_live_enterprise_991"

def push_invoice(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"❌ Error: Cannot find file '{pdf_path}'")
        return

    print(f"📦 Carrier Bot: Pushing {pdf_path} to LedgerFlux Webhook...")
    
    headers = {
        "x-api-key": API_KEY  # Passing the security badge
    }
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            
            # Firing the payload directly at Node.js (Bypassing Streamlit)
            response = requests.post(API_URL, headers=headers, files=files)
            
        if response.status_code == 200:
            print("\n✅ SUCCESS: LedgerFlux accepted the payload.")
            data = response.json()
            print(f"📊 Auto-Audit Result: Invoice {data['data']['invoice_id']} | Status: {data['data']['status']} | Savings: ₹{data['data']['total_savings']}")
        else:
            print(f"\n❌ ACCESS DENIED: {response.status_code} - {response.json().get('error', 'Unknown Error')}")
            
    except requests.exceptions.ConnectionError:
        print("\n🚨 Connection Error: Is your Node.js server running on Port 3000?")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python carrier_bot.py <path_to_pdf>")
    else:
        push_invoice(sys.argv[1])