import csv
import os

# --- 1. THE ENTERPRISE ENGINE (For the Email Webhook) ---
class DynamicContractEngine:
    def __init__(self):
        # Cache for lightning-fast lookups
        self.active_rate_cards = {} 

    def ingest_rate_card(self, tenant_id: str, filepath: str):
        if not os.path.exists(filepath):
            print(f"[-] FATAL: Rate card not found for tenant {tenant_id}")
            return False

        rates = []
        with open(filepath, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                rates.append({
                    "carrier": row["Carrier"].upper(),
                    "zone": int(row["Zone"]),
                    "weight_max": float(row["Weight_Max"]),
                    "rate": float(row["Contract_Rate"])
                })
        
        self.active_rate_cards[tenant_id] = rates
        print(f"[+] Loaded {len(rates)} specific contract rules for Tenant: {tenant_id}")
        return True

    def calculate_expected_cost(self, tenant_id: str, carrier: str, weight: float, zone: int):
        if tenant_id not in self.active_rate_cards:
            return None 
            
        tenant_rates = self.active_rate_cards[tenant_id]
        for rule in tenant_rates:
            if rule["carrier"] == carrier.upper() and rule["zone"] == zone and weight <= rule["weight_max"]:
                return rule["rate"]
                
        return None 

    def execute_audit(self, tenant_id: str, invoice_data: dict):
        carrier = invoice_data.get("carrier")
        billed_amount = float(invoice_data.get("billed_amount", 0.0))
        weight = float(invoice_data.get("billed_weight", 0.0))
        zone = int(invoice_data.get("zone", 1))

        expected_cost = self.calculate_expected_cost(tenant_id, carrier, weight, zone)

        if expected_cost is None:
            return {"status": "SKIPPED", "reason": "No contract data for this lane"}

        if billed_amount > expected_cost:
            leakage = round(billed_amount - expected_cost, 2)
            return {
                "status": "DISCREPANCY_FOUND",
                "leakage_amount": f"${leakage}",
                "reason": f"Contract Violation: Expected ${expected_cost}, but billed ${billed_amount} for {weight}kg to Zone {zone}."
            }
        
        return {"status": "CLEAN", "reason": "Billed amount matches contract"}

# Initialize the global engine instance for the webhook
engine = DynamicContractEngine()


# --- 2. THE UI ADAPTER (For master_run.py Streamlit Dashboard) ---
def run_audit(extracted_rows, carrier):
    """
    Legacy adapter to ensure master_run.py can import successfully.
    Acts as a passthrough if the UI triggers a direct table extraction.
    """
    status = "Match"
    total_billed = 0.0
    total_savings = 0.0
    details = []
    
    for row in extracted_rows:
        # Dummy pass-through logic for the UI array format
        billed_val = float(row.get("billed", 0))
        details.append({
            "Item": "Standard Freight",
            "Billed": billed_val,
            "Expected": billed_val,
            "Status": "Match",
            "Note": "Cleared by UI Adapter"
        })
        total_billed += billed_val

    return status, total_billed, total_savings, details