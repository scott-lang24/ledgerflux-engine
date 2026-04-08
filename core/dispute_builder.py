import datetime

def generate_dispute_draft(invoice_id, carrier, discrepancies):
    if not discrepancies:
        return "No discrepancies found. No dispute needed."
        
    awb_list = "\n".join([f"- AWB {d['AWB']}: Billed ₹{d['Billed']:.2f}, Expected ₹{d['Expected']:.2f} ({d['Note']})" 
                          for d in discrepancies if d['Status'] == 'DISPUTE'])
    
    draft = f"""
SUBJECT: Formal Billing Dispute - Invoice #{invoice_id}

To {carrier} Billing Team,

Upon forensic review of Invoice #{invoice_id} generated on {datetime.date.today()}, LedgerFlux Enterprise has identified mathematical discrepancies between the billed amounts and our active Master Service Agreement.

Please find the disputed items below:
{awb_list}

We kindly request a credit note for the overcharged amount of ₹{sum([d['Billed'] - d['Expected'] for d in discrepancies if d['Status'] == 'DISPUTE']):.2f} applied to our next billing cycle.

Regards,
OmniActive Health via LedgerFlux Audit Engine
"""
    return draft