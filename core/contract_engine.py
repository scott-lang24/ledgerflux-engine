# A mock rate card. In a real app, this comes from a database per client.
RATE_CARD = {
    "Delhivery": {
        "Zone A": 45.0, # ₹ per kg
        "Zone B": 60.0,
        "Fuel Surcharge": 0.10 # 10%
    }
}

def run_audit(extracted_rows, carrier):
    results = []
    total_billed = 0.0
    total_savings = 0.0
    
    rates = RATE_CARD.get(carrier, RATE_CARD["Delhivery"])
    
    for row in extracted_rows:
        awb = row["awb"]
        weight = float(row["weight"])
        zone = row["zone"]
        billed_amount = float(row["billed"])
        
        # Calculate what it SHOULD cost
        base_rate = rates.get(zone, 50.0)
        expected_base = weight * base_rate
        expected_total = expected_base + (expected_base * rates["Fuel Surcharge"])
        
        total_billed += billed_amount
        
        if billed_amount > expected_total:
            overcharge = billed_amount - expected_total
            total_savings += overcharge
            results.append({
                "AWB": awb,
                "Billed": billed_amount,
                "Expected": expected_total,
                "Status": "DISPUTE",
                "Note": f"Rate mismatch for {zone}. Overcharged by ₹{overcharge:.2f}"
            })
        else:
            results.append({
                "AWB": awb,
                "Billed": billed_amount,
                "Expected": expected_total,
                "Status": "Match",
                "Note": "Cleared"
            })
            
    status = "Discrepancy" if total_savings > 0 else "Clear"
    return status, total_billed, total_savings, results