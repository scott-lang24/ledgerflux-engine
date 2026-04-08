import pdfplumber
import random
import re

def clean_number(text):
    """Strips currency symbols and commas to return a clean float."""
    if not text: return 0.0
    clean_text = re.sub(r'[^\d.]', '', str(text))
    try:
        return float(clean_text)
    except ValueError:
        return 0.0

# THE MASTER TRANSLATION SCHEMA
# This tells the engine what column headers to hunt for based on the carrier.
CARRIER_SCHEMAS = {
    "Delhivery": {
        "awb": ["awb", "tracking"],
        "wt": ["wt", "weight"],
        "zone": ["zone"],
        "billed": ["total", "billed", "amount"]
    },
    "BlueDart": {
        "awb": ["waybill", "ref"],
        "wt": ["weight", "kgs"],
        "zone": ["destination", "hub"],
        "billed": ["amount", "charge"]
    },
    "Safexpress": {
        "awb": ["lr", "consignment"],
        "wt": ["actual", "charged"],
        "zone": ["location", "branch"],
        "billed": ["freight", "net"]
    }
}

def extract_invoice_data(pdf_file, carrier_name):
    extracted_data = []
    # Generate a smart invoice ID based on the carrier name
    invoice_id = f"INV-{carrier_name[:3].upper()}-{random.randint(1000, 9999)}"
    
    # Load the specific dictionary for the selected carrier
    schema = CARRIER_SCHEMAS.get(carrier_name, CARRIER_SCHEMAS["Delhivery"])
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    header_idx = -1
                    
                    # 1. Hunt for the Header Row using the Carrier Schema
                    for i, row in enumerate(table):
                        row_text = " ".join([str(cell).lower() for cell in row if cell])
                        # If we find at least one AWB keyword and one Billed keyword, we found the header
                        if any(k in row_text for k in schema["awb"]) and any(k in row_text for k in schema["billed"]):
                            header_idx = i
                            break
                    
                    # 2. Map the Columns dynamically
                    if header_idx != -1:
                        headers = table[header_idx]
                        awb_idx, wt_idx, zone_idx, billed_idx = -1, -1, -1, -1
                        
                        for i, col_name in enumerate(headers):
                            if not col_name: continue
                            col_lower = str(col_name).lower()
                            
                            if any(k in col_lower for k in schema["awb"]): awb_idx = i
                            elif any(k in col_lower for k in schema["wt"]): wt_idx = i
                            elif any(k in col_lower for k in schema["zone"]): zone_idx = i
                            elif any(k in col_lower for k in schema["billed"]): billed_idx = i
                        
                        # 3. Rip the Data
                        if awb_idx != -1 and billed_idx != -1:
                            for row in table[header_idx + 1:]:
                                if not row or not any(row): continue
                                
                                awb_val = str(row[awb_idx]).strip() if awb_idx < len(row) and row[awb_idx] else ""
                                if not awb_val or len(awb_val) < 4: continue # Skip junk rows
                                
                                weight_val = clean_number(row[wt_idx]) if wt_idx != -1 else 1.0
                                zone_val = str(row[zone_idx]).strip() if zone_idx != -1 else "Zone A"
                                billed_val = clean_number(row[billed_idx]) if billed_idx != -1 else 0.0
                                
                                extracted_data.append({
                                    "awb": awb_val,
                                    "weight": weight_val,
                                    "zone": zone_val,
                                    "billed": billed_val
                                })

    except Exception as e:
        print(f"[SYS ERROR] PDF Extraction failed: {e}")
        
    return invoice_id, extracted_data