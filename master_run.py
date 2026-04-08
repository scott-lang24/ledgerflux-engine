import streamlit as st
import pandas as pd
import zipfile
import requests
from io import BytesIO
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie

# --- IMPORT OUR MODULAR ENGINES ---
from core.db_manager import init_db, log_audit, get_db_connection
from core.ocr_engine import extract_invoice_data
from core.contract_engine import run_audit
from core.dispute_builder import generate_dispute_draft
from core.report_engine import generate_html_report, send_real_email

# Initialize DB
init_db()

st.set_page_config(page_title="LedgerFlux Portal", page_icon="⚡", layout="wide")

# Lottie Animation Loader
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_email = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_swoi6t8m.json")

pro_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; color: #E0E0E0; }
    .stApp { background-color: #050505; } 
    div[data-testid="stMetric"] { background: #121212; border: 1px solid #2A2A2A; border-radius: 16px; padding: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .stButton > button { background: linear-gradient(90deg, #6C5DD3 0%, #8B78E6 100%); color: white; border-radius: 8px; border: none; height: 50px; font-weight: 700; width: 100%; }
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = True

with st.sidebar:
    st.markdown("## ⚡ LedgerFlux") 
    st.caption("v6.1 Modular Engine (Enterprise)")
    selected = option_menu(None, ["Dashboard", "Run Audit"], icons=["grid", "lightning"], default_index=1)

if selected == "Run Audit":
    st.title("Run Carrier Audit")
    carrier = st.selectbox("Target Carrier Contract:", ["Delhivery", "BlueDart", "Safexpress"])
    
    uploaded_file = st.file_uploader("Upload Invoice (PDF or ZIP)", type=['pdf', 'zip'])
    
    if st.button("EXECUTE FORENSIC AUDIT") and uploaded_file:
        terminal = st.empty()
        
        if uploaded_file.name.endswith('.pdf'):
            terminal.code("[SYS] Phase 1: Initiating OCR Vision Engine...", language="bash")
            
            # 1. OCR Engine
            inv_id, extracted_rows = extract_invoice_data(uploaded_file, carrier)
            terminal.code("[SYS] Phase 2: Running Contract Math Engine...", language="bash")
            
            # 2. Contract Engine
            status, total_billed, total_savings, details = run_audit(extracted_rows, carrier)
            details_df = pd.DataFrame(details)
            
            # 3. DB Manager
            log_audit(inv_id, status, total_billed, total_savings)
            terminal.empty()
            
            # --- UI RENDERING ---
            st.success(f"Audit Complete: Invoice {inv_id}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Billed", f"₹ {total_billed:,.2f}")
            c2.metric("Identified Overcharge", f"₹ {total_savings:,.2f}", delta=f"₹{total_savings:,.2f}")
            c3.metric("Status", status)
            
            st.subheader("Line Item Breakdown")
            
            def highlight_error(row):
                if row['Status'] != 'Match': return ['background-color: #381E1E'] * len(row)
                return [''] * len(row)
                
            st.dataframe(details_df.style.apply(highlight_error, axis=1).format({"Billed": "₹ {:.2f}", "Expected": "₹ {:.2f}"}), use_container_width=True)
            
            # 4. Dispute Builder
            if status == "Discrepancy":
                st.subheader("Auto-Generated Legal Dispute")
                draft = generate_dispute_draft(inv_id, carrier, details)
                st.text_area("Copy and send to carrier billing:", value=draft, height=250)
            
            # 5. HTML Generation & Email Routing (THE MISSING FEATURES)
            st.markdown("---")
            st.subheader("Export & Distribution")
            
            html_report = generate_html_report(inv_id, carrier, status, total_billed, total_savings, details_df)
            
            c4, c5 = st.columns(2)
            with c4:
                st.download_button("⬇️ Download Official HTML Certificate", data=html_report, file_name=f"Audit_{inv_id}.html", mime="text/html")
            
            with c5:
                email = st.text_input("Send to Client / Exec Team:")
                if st.button("Secure Send") and email:
                    if lottie_email: st_lottie(lottie_email, height=100, key="mail_anim")
                    ok, msg = send_real_email(
                        email, 
                        f"LedgerFlux Audit Certificate: {inv_id}", 
                        "Please find the attached formal audit certificate.", 
                        html_content=html_report, 
                        filename=f"Audit_{inv_id}.html"
                    )
                    if ok: st.success("Report Sent Successfully!")
                    else: st.error(msg)

elif selected == "Dashboard":
    st.title("Financial Intelligence")
    conn = get_db_connection()
    try: 
        df = pd.read_sql_query("SELECT * FROM audits ORDER BY timestamp DESC", conn)
        st.dataframe(df, use_container_width=True)
    except: 
        st.write("No audits run yet.")
    conn.close()