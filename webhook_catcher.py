import os
import shutil
from fastapi import FastAPI, File, UploadFile, Form
import uvicorn

app = FastAPI()

@app.post("/inbound-parse")
async def receive_inbound_email(
    to: str = Form(None),
    From: str = Form(None),
    attachment1: UploadFile = File(...) # The ... makes it strictly required
):
    print("\n[>>>] INCOMING SECURE PAYLOAD [<<<]")
    print(f"[*] Sender detected: {From}")
    
    if not attachment1:
        print("[-] FATAL ERROR: attachment1 is completely missing from the stream.")
        return {"status": "failed", "reason": "No file stream received"}

    print(f"[+] File Detected in stream: {attachment1.filename}")
    
    # Secure the file
    temp_dir = "temp_inbound"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, attachment1.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(attachment1.file, buffer)

    print(f"[+] Payload secured at {temp_path}. Handshake Complete.")
    
    # We are isolating the handshake. We will plug the Node.js emailer back in AFTER this works.
    return {"status": "success", "message": "Handshake 100% verified."}

if __name__ == "__main__":
    # Ensure it's running
    print("[*] Webhook Catcher Online. Awaiting transmission...")
    uvicorn.run(app, host="127.0.0.1", port=8000)