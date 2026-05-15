class TenantRouter:
    def __init__(self):
        # In Production, this queries Supabase. We cache it here for speed.
        self.domain_map = {
            "omniactive.com": "OMNIACTIVE-UUID-001",
            "zenohealth.com": "ZENO-UUID-002",
            "starkindustries.com": "STARK-UUID-999" # Added for your testing
        }

    def identify_tenant(self, sender_email: str):
        try:
            domain = sender_email.split('@')[1].lower()
            tenant_id = self.domain_map.get(domain)
            
            if tenant_id:
                print(f"[+] Authentication Success: Domain '{domain}' mapped to Tenant [{tenant_id}]")
                return tenant_id
            else:
                print(f"[-] UNAUTHORIZED: Domain '{domain}' is not registered in LedgerFlux.")
                return None
        except IndexError:
            return None

router = TenantRouter()