import random
import time

def extract_invoice_data(pdf_bytes, carrier_name="Delhivery"):
    # TODO: This is where we write the actual pdfplumber table extraction logic
    # ONCE you provide the column headers for the target carrier.
    
    time.sleep(1.5) # Simulate processing time
    
    # We fake extracting 3 rows of data for now
    mock_extracted_data = [
        {"awb": f"774{random.randint(10000,99999)}", "weight": random.uniform(5, 15), "zone": "Zone A", "billed": random.uniform(300, 500)},
        {"awb": f"774{random.randint(10000,99999)}", "weight": random.uniform(10, 25), "zone": "Zone B", "billed": random.uniform(800, 1200)}, # Usually overcharged
        {"awb": f"774{random.randint(10000,99999)}", "weight": random.uniform(2, 8), "zone": "Zone A", "billed": random.uniform(100, 200)}
    ]
    
    # Force a fake overcharge on the second item so the dispute engine triggers
    mock_extracted_data[1]["billed"] += 250.0 
    
    invoice_id = f"INV-{random.randint(10000, 99999)}"
    return invoice_id, mock_extracted_data