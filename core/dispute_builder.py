def generate_dispute_draft(invoice_id, carrier, details):
    """Generates a legally sound dispute email based on specific line item failures."""
    
    # Filter only the items that were flagged as a DISPUTE
    disputed_items = [d for d in details if d.get('Status') == 'DISPUTE']
    
    if not disputed_items:
        return "Audit cleared. No discrepancies found to dispute."
    
    # Calculate the total amount we are fighting for
    total_disputed = sum([float(item.get('Billed', 0)) for item in disputed_items])
    
    draft = f"Subject: URGENT: SLA/Billing Discrepancy Notice - Invoice {invoice_id}\n\n"
    draft += f"To {carrier} Billing Department,\n\n"
    draft += f"We are writing to formally dispute charges totaling ₹{total_disputed:,.2f} on Invoice {invoice_id}. "
    draft += "Our automated LedgerFlux audit has identified the following violations based on our contracted rate cards and SLA agreements:\n\n"
    
    for item in disputed_items:
        draft += f"• Discrepancy: {item.get('Item')}\n"
        draft += f"  - Amount Billed: ₹{float(item.get('Billed', 0)):,.2f}\n"
        draft += f"  - Expected Amount: ₹{float(item.get('Expected', 0)):,.2f}\n"
        draft += f"  - System Note: {item.get('Note')}\n\n"
        
    draft += "Please review the attached Master Audit Certificate for full line-item details. "
    draft += "We expect a revised invoice or a credit note issued for the disputed amount within 5 business days.\n\n"
    draft += "Regards,\nLedgerFlux Automated Dispute System"
    
    return draft