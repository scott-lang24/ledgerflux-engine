import requests

# Using 127.0.0.1 bypasses any weird 'localhost' DNS resolution issues
URL = "http://127.0.0.1:8000/inbound-parse"
TEST_FILE = "STARK_OVERRIDE_TEST.pdf"

# 1. WE BUILD THE FILE ON THE FLY. Zero chance of "File Not Found".
with open(TEST_FILE, "wb") as f:
    f.write(b"%PDF-1.4\n%This is a guaranteed Stark Industries payload.")
print(f"[*] Asset forged: {TEST_FILE}")

# 2. ASSEMBLE THE PAYLOAD
data = {
    "to": "audit@ledgerflux.com",
    "From": "jdoesbusiness09@gmail.com"
}

# 3. FIRE THE MISSILE
try:
    with open(TEST_FILE, "rb") as f:
        # The key MUST be 'attachment1' to match the FastAPI parameter
        files = {"attachment1": (TEST_FILE, f, "application/pdf")}
        
        print("[*] Initiating override transmission...")
        response = requests.post(URL, data=data, files=files)
        
        print(f"[+] Server Response Code: {response.status_code}")
        print(f"[+] Server JSON: {response.json()}")
except Exception as e:
    print(f"[-] Transmission Failure: {e}")