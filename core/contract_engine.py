import csv
import os

class DynamicContractEngine:
    def __init__(self):
        # In a production environment, this data lives in Redis or PostgreSQL. 
        # For now, we cache it in memory for lightning-fast lookups.
        self.active_rate_cards = {} 

    def ingest_rate_card(self, tenant_id: str, filepath: str):
        """
        Parses a client's CSV rate card into the engine's memory.
        Expected CSV headers: Carrier,Zone,Weight_Max,Contract_Rate
        """
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
        """
        The Brain: Looks up the exact negotiated cost for a specific shipment.
        """
        if tenant_id not in self.active_rate_cards:
            return None # No rate card on file, default to baseline audit
            
        tenant_rates = self.active_rate_cards[tenant_id]
        
        # Find the exact contract rate for this weight and zone
        for rule in tenant_rates:
            if rule["carrier"] == carrier.upper() and rule["zone"] == zone and weight <= rule["weight_max"]:
                return rule["rate"]
                
        return None # No matching rule found

    def execute_audit(self, tenant_id: str, invoice_data: dict):
        """
        Compares the Billed amount vs the Contracted amount to find Leakage.
        """
        carrier = invoice_data.get("carrier")
        billed_amount = float(invoice_data.get("billed_amount", 0.0))
        weight = float(invoice_data.get("billed_weight", 0.0))
        zone = int(invoice_data.get("zone", 1))

        expected_cost = self.calculate_expected_cost(tenant_id, carrier, weight, zone)

        if expected_cost is None:
            return {"status": "SKIPPED", "reason": "No contract data for this lane"}

        # Calculate the discrepancy
        if billed_amount > expected_cost:
            leakage = round(billed_amount - expected_cost, 2)
            return {
                "status": "DISCREPANCY_FOUND",
                "leakage_amount": f"${leakage}",
                "reason": f"Contract Violation: Expected ${expected_cost}, but billed ${billed_amount} for {weight}kg to Zone {zone}."
            }
        
        return {"status": "CLEAN", "reason": "Billed amount matches contract"}

# Initialize the global engine instance
engine = DynamicContractEngine()