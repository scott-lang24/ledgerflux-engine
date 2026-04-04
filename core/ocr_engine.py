import pdfplumber
import random
import re

def clean_number(text):
    """Strips currency symbols and commas to return a clean float."""
    if not text: return 0.0
    # Remove anything that isn't a digit or a decimal point
    clean_text = re.sub(r'[^\d.]', '', str(text))
    try:
        return float(clean_text)
    except ValueError:
        return 0.0

def extract_invoice_data(pdf_file, carrier_name="Delhivery"):
    extracted_data = []
    invoice_id = f"INV-{random.randint(10000, 99999)}"
    
    try:
        # Open the PDF using the real file you uploaded
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Tell the engine to look for grid lines and tables
                tables = page.extract_tables()
                
                for table in tables:
                    header_idx = -1
                    
                    # 1. Hunt for the Header Row
                    for i, row in enumerate(table):
                        row_text = " ".join([str(cell).lower() for cell in row if cell])
                        if "awb" in row_text and "wt" in row_text:
                            header_idx = i
                            break
                    
                    # 2. Map the Columns
                    if header_idx != -1:
                        headers = table[header_idx]
                        awb_idx, wt_idx, zone_idx, billed_idx = -1, -1, -1, -1
                        
                        for i, col_name in enumerate(headers):
                            if not col_name: continue
                            col_lower = str(col_name).lower()
                            if "awb" in col_lower: awb_idx = i
                            elif "wt" in col_lower or "weight" in col_lower: wt_idx = i
                            elif "zone" in col_lower: zone_idx = i
                            elif "total" in col_lower or "billed" in col_lower: billed_idx = i
                        
                        # 3. Rip the Data
                        if awb_idx != -1 and billed_idx != -1:
                            for row in table[header_idx + 1:]:
                                if not row or not any(row): continue
                                
                                awb_val = str(row[awb_idx]).strip() if awb_idx < len(row) and row[awb_idx] else ""
                                if not awb_val or len(awb_val) < 4: continue # Skip if it's not a real AWB
                                
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
        print(f"Error reading PDF: {e}")
        
    return invoice_id, extracted_data