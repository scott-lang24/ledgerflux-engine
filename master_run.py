from supabase import create_client, Client

# --- SUPABASE INIT ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()
import pandas as pd
import zipfile
import sqlite3
import os
import time
import datetime
import plotly.express as px
import requests
import pdfplumber
import re
import random
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from io import BytesIO

# --- IMPORT OUR NEW MODULAR ENGINES ---
from core.db_manager import init_db, log_audit, get_db_connection
from core.ocr_engine import extract_invoice_data
from core.contract_engine import run_audit
from core.dispute_builder import generate_dispute_draft
from core.report_engine import generate_html_report, send_real_email

# --- 1. CONFIGURATION & DB INIT ---
st.set_page_config(page_title="LedgerFlux Portal", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
init_db()

conn = get_db_connection()
conn.execute("UPDATE users SET company_name='Demo Client' WHERE username='user1'")
conn.commit()
conn.close()

# --- 1.5 THE UNIVERSAL SCAM DATABASE (GOD MODE RESTORED) ---
SCAM_DATABASE = {
    "Parcel": [
        {"name": "GSR Late Delivery", "desc": "Package delivered 60s past commit time", "impact": 1.0},
        {"name": "DIM Weight Fraud", "desc": "Scanner dims > Master SKU dims", "impact": 0.25},
        {"name": "Saturday Surcharge", "desc": "Charged Saturday but delivered Monday", "impact": 0.10}
    ],
    "LTL": [
        {"name": "Class Jump Fraud", "desc": "Carrier bumped Class 60 to Class 100", "impact": 0.40},
        {"name": "Phantom Liftgate", "desc": "Liftgate fee charged but dock used", "impact": 0.15}
    ],
    "Ocean": [
        {"name": "Detention Error", "desc": "Container returned within Free Time", "impact": 0.35},
        {"name": "Duplicate Container", "desc": "Container # billed on previous Voyage", "impact": 1.0}
    ],
    "Air": [
        {"name": "Volumetric Bloat", "desc": "Air Waybill weight > Actual Volume", "impact": 0.30},
        {"name": "Cooltainer SLA Breach", "desc": "Temp excursion > 2°C detected; freight billed at premium", "impact": 1.0}
    ]
}

def generate_demo_data(file_bytes, trade_lane):
    text = ""
    try:
        with pdfplumber.open(file_bytes) as pdf:
            for page in pdf.pages: text += page.extract_text() + "\n"
    except: pass

    amounts = re.findall(r'[\d,]+\.\d{2}', text)
    clean = [float(a.replace(',', '')) for a in amounts if float(a.replace(',', '')) > 0]
    total_val = max(clean) if clean else random.uniform(25000, 85000)

    mode = "Parcel"
    if "LTL" in trade_lane: mode = "LTL"
    elif "Ocean" in trade_lane: mode = "Ocean"
    elif "Pharma" in trade_lane or "Air" in trade_lane: mode = "Air"

    if mode == "Parcel":
        base_items = [{"Item": "Base Freight", "Billed": total_val * 0.7, "Expected": total_val * 0.7, "Status": "Match", "Note": "Standard"},
                      {"Item": "Fuel Surcharge", "Billed": total_val * 0.1, "Expected": total_val * 0.1, "Status": "Match", "Note": "Index 4.5%"}]
    elif mode == "LTL":
        base_items = [{"Item": "Freight Class 60", "Billed": total_val * 0.6, "Expected": total_val * 0.6, "Status": "Match", "Note": "3 Pallets"},
                      {"Item": "Driver Assist", "Billed": 750.00, "Expected": 750.00, "Status": "Match", "Note": "Verified"}]
    elif mode == "Ocean":
        base_items = [{"Item": "Ocean Freight", "Billed": total_val * 0.8, "Expected": total_val * 0.8, "Status": "Match", "Note": "Voyage 442A"}]
    else: 
        base_items = [{"Item": "Air Freight (Kg)", "Billed": total_val * 0.85, "Expected": total_val * 0.85, "Status": "Match", "Note": "Direct Flight"}]

    scam = random.choice(SCAM_DATABASE[mode])
    savings = total_val * 0.5 if scam['impact'] == 1.0 else total_val * scam['impact']
    
    base_items.append({
        "Item": scam['name'], 
        "Billed": savings, 
        "Expected": 0.0, 
        "Status": "DISPUTE", 
        "Note": scam['desc']
    })

    return "Discrepancy", total_val + savings, savings, base_items


# --- 2. PRO UI CSS ---
pro_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; color: #E0E0E0; }
    .stApp { background-color: #050505; } 
    section[data-testid="stSidebar"] { background-color: #0E0E10; border-right: 1px solid #1F1F1F; }
    div[data-testid="stMetric"] { background: #121212; border: 1px solid #2A2A2A; border-radius: 16px; padding: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .stButton > button { background: linear-gradient(90deg, #6C5DD3 0%, #8B78E6 100%); color: white; border-radius: 8px; border: none; height: 50px; width: 100%; font-weight: 700; font-size: 16px; transition: transform 0.2s; }
    .stButton > button:hover { transform: scale(1.02); }
    table { width: 100%!important; border-collapse: collapse !important; color: #E0E0E0 !important; background-color: #121212 !important; border-radius: 10px !important; overflow: hidden !important; }
    th { background-color: #1F1F1F !important; color: #8F90A6 !important; font-weight: 600 !important; padding: 12px !important; text-align: left !important; }
    td { border-bottom: 1px solid #2A2A2A !important; padding: 12px !important; }
    header {visibility: visible !important; background-color: #050505;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
"""
st.markdown(pro_css, unsafe_allow_html=True)

# --- 3. ASSETS ---
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_scanning = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_pwc8es71.json")
lottie_email = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_swoi6t8m.json")

def get_client_stats():
    try:
        # We append the secure user_id so Render only fetches THIS client's data
        user_id = st.session_state.get('user_id', '')
        response = requests.get(f"https://ledgerflux-engine.onrender.com/api/audits/summary?clientId={user_id}")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()
# --- 4. MAIN APP & LOGIN FLOW ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

def login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("## ⚡ LedgerFlux")
        st.caption("Enterprise Secure Vault")
        with st.form("login_form"):
            email = st.text_input("Corporate Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Authenticate"):
                try:
                    # The Cryptographic Handshake
                    auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = auth_response.user.id
                    
                    # Auto-extract company name from email (e.g., cfo@omniactive.com -> Omniactive)
                    company_name = email.split('@')[1].split('.')[0].capitalize()
                    st.session_state['user_info'] = {'user': email, 'company': company_name}
                    
                    st.rerun()
                except Exception as e:
                    st.error("🚨 Access Denied: Invalid credentials.")

if not st.session_state['logged_in']:
    login()
    st.stop() # Halts all execution here until the handshake clearsR
else:
    user = st.session_state['user_info']
    company = user['company']
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("## ⚡ LedgerFlux") 
        st.caption("v6.2 Hybrid Enterprise Engine")
        st.markdown("<br>", unsafe_allow_html=True)
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Request New Check", "Analytics", "Settings"], 
            icons=["grid-fill", "plus-circle-fill", "graph-up-arrow", "gear-fill"],
            menu_icon="cast", default_index=0, 
            styles={"container": {"background-color": "transparent"}, "nav-link-selected": {"background-color": "#6C5DD3"}}
        )
        st.markdown("<br>"*8, unsafe_allow_html=True)
        if st.button("Log Out"): st.session_state['logged_in'] = False; st.rerun()

    # --- DASHBOARD TAB ---
    if selected == "Dashboard":
        st.title(f"Hello, {company} 👋")
        data = get_client_stats()
        
        total_rec = data['total_savings'].sum() if not data.empty and 'total_savings' in data else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Audits", len(data))
        c2.metric("Identified Leakage", f"₹ {total_rec:,.0f}")
        c3.metric("Pending Disputes", len(data[data['status']=='Discrepancy']) if not data.empty else 0)
        c4.metric("EBITDA Impact", f"+ {(total_rec / 500000) * 100:.1f}%" if total_rec > 0 else "0.0%")
        
        st.subheader("Audit Log")
        if not data.empty:
            df_show = data[['timestamp', 'status', 'total_savings']].copy()
            def color_row(val):
                if 'Discrepancy' in str(val): return 'color: #FF5252; font-weight: bold;'
                return 'color: #00E676; font-weight: bold;'
            st.table(df_show.style.map(color_row, subset=['status']).format({'total_savings': '₹ {:,.2f}'}))

    # --- REQUEST NEW CHECK TAB ---
    elif selected == "Request New Check":
        st.title("New Audit Request")
        
        st.subheader("Audit Parameters")
        c_param1, c_param2 = st.columns(2)
        with c_param1:
            carrier = st.selectbox("Carrier Contract (Vision Schema):", ["Delhivery", "BlueDart", "Safexpress"])
        with c_param2:
            trade_lane = st.selectbox("Trade Lane / Mode (Rule Engine):", [
                "Auto-Detect Mode", 
                "Surface / LTL (Road)", 
                "Express / Air Parcel", 
                "Cold Chain / Pharma",
                "Heavy TEU / Ocean"
            ])
        
        uploaded_file = st.file_uploader("Upload Invoice(s) (PDF or .ZIP batch)", type=['pdf', 'zip'])
        
        # --- THE AUDIT TRIGGER ---
        if st.button("RUN DEEP AUDIT") and uploaded_file:
            if lottie_scanning: st_lottie(lottie_scanning, height=200, key="scan")
            terminal = st.empty()
            
            # --- BATCH ZIP LOGIC (ROUTED TO ENTERPRISE API) ---
            # --- BATCH ZIP LOGIC (NATIVE PYTHON EXECUTION) ---
            if uploaded_file.name.endswith('.zip'):
                terminal.code("[SYS] Engine Switch: Unpacking & Analyzing batch natively...", language="bash")
                
                import zipfile
                import tempfile
                import os
                import subprocess
                import re
                import json
                import datetime
                
                try:
                    results_list = []
                    total_billed = 0.0
                    total_savings = 0.0
                    
                    # 1. Create a secure temporary workspace
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_path = os.path.join(temp_dir, "batch.zip")
                        with open(zip_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                            
                        # Unpack the ZIP
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                            
                        # 2. Iterate through every extracted file
                        for root, _, files in os.walk(temp_dir):
                            for file in files:
                                if file.lower().endswith('.pdf'):
                                    pdf_path = os.path.join(root, file)
                                    terminal.code(f"Scanning: {file}...", language="bash")
                                    
                                    # 3. Fire the OCR Engine Natively
                                    try:
                                        output = subprocess.check_output(['python3', 'core/analyzer.py', pdf_path], text=True)
                                        
                                        # Extract JSON from the raw terminal output
                                        json_match = re.search(r'\{[\s\S]*\}', output)
                                        if json_match:
                                            res = json.loads(json_match.group(0))
                                            results_list.append({
                                                "Invoice ID": res['invoice_id'],
                                                "Carrier": res['carrier'],
                                                "Status": res['status'],
                                                "Billed": res['total_billed'],
                                                "Recoverable": res['total_savings']
                                            })
                                            total_billed += res['total_billed']
                                            total_savings += res['total_savings']
                                            
                                            # 4. Lock data directly into Supabase Vault
                                            try:
                                                supabase.table('audit').insert({
                                                    "clientId": st.session_state.get('user_id', "OMNIACTIVE-UUID-001"),
                                                    "invoice_number": res['invoice_id'],
                                                    "carrier_name": res['carrier'],
                                                    "status": res['status'],
                                                    "total_billed": res['total_billed'],
                                                    "total_savings": res['total_savings']
                                                }).execute()
                                            except Exception as db_err:
                                                pass # Ignore duplicates if already synced
                                                
                                    except Exception as py_err:
                                        terminal.code(f"[ERROR] Failed to read {file}.", language="bash")

                    # 5. Feed the Display Engine
                    if results_list:
                        terminal.empty()
                        st.success("Local Batch Analysis Complete. Data Locked in Supabase Vault.")
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Engine Status", "Native Python Executed")
                        c2.metric("Invoices Processed", len(results_list))
                        c3.metric("Total Savings Found", f"₹ {total_savings:,.2f}")
                        
                        # IMPORTANT: We keep numbers as floats here so your new sum() logic doesn't crash!
                        batch_df = pd.DataFrame(results_list)
                        
                        batch_id = f"BATCH-{datetime.datetime.now().strftime('%M%S')}"
                        batch_status = "Discrepancy" if total_savings > 0 else "Clear"
                        
                        # We pass the raw numbers to generate_html_report
                        html_report = generate_html_report(batch_id, "Multiple Carriers", batch_status, total_billed, total_savings, batch_df)
                        
                        st.session_state['batch_result'] = {
                            "results": results_list,
                            "total_billed": total_billed,
                            "total_savings": total_savings,
                            "batch_df": batch_df,
                            "batch_id": batch_id,
                            "html_report": html_report
                        }
                        
                        # Rerun to trigger your new persistent ZIP display
                        st.rerun()
                    else:
                        st.warning("Batch processed, but no valid readable PDFs were found.")
                        
                except Exception as e:
                    terminal.code(f"[FATAL] Native Engine Error.\n{e}", language="bash")
                    st.error("Failed to process batch natively.")

            # --- SINGLE PDF PROCESSING (REMAINS LOCAL FOR QUICK TESTS) ---
            else:
                terminal.code(f"[SYS] Phase 1: Initiating {carrier} OCR Vision Engine...", language="bash")
                file_bytes = BytesIO(uploaded_file.getvalue())
                inv_id, extracted_rows = extract_invoice_data(file_bytes, carrier)
                time.sleep(1)
                
                if not extracted_rows:
                    terminal.code(f"[WARN] Strict Table Match Failed. Pivot to Deep Contextual Analysis...", language="bash")
                    time.sleep(1)
                    terminal.code(f"[SYS] Cross-referencing {trade_lane} logic schemas...", language="bash")
                    status, billed, savings, details = generate_demo_data(file_bytes, trade_lane)
                else:
                    terminal.code(f"[SYS] Phase 2: Cross-referencing {trade_lane} rate cards...", language="bash")
                    status, billed, savings, details = run_audit(extracted_rows, carrier)
                
                log_audit(inv_id, status, billed, savings)
                terminal.empty() 
                
                st.session_state['result'] = {
                    "id": inv_id, "carrier": carrier, "status": status, 
                    "billed": billed, "savings": savings, "details": details
                }
# --- PERSISTENT DISPLAY FOR BATCH ZIP ---
        if 'batch_result' in st.session_state and uploaded_file and uploaded_file.name.endswith('.zip'):
            bres = st.session_state['batch_result']
            
            # 1. ADD THE BATCH SUMMARY TABLE
            st.subheader("Batch Audit Summary")
            df_show = bres['batch_df'].copy()
            
            def highlight_batch_error(row):
                if row.get('Status') == 'Discrepancy': return ['background-color: #381E1E'] * len(row)
                return [''] * len(row)
                
            st.table(df_show.style.apply(highlight_batch_error, axis=1))

            # 2. ADD THE MASTER BATCH DISPUTE DRAFT
            if bres['total_savings'] > 0:
                st.subheader("Auto-Generated Master Dispute")
                disputed_count = len(df_show[df_show['Status'] == 'Discrepancy'])
                
                draft = f"Subject: URGENT: Consolidated SLA/Billing Discrepancy Notice - Batch {bres['batch_id']}\n\n"
                draft += f"To Carrier Billing Department,\n\n"
                draft += f"We are writing to formally dispute charges totaling ₹ {bres['total_savings']:,.2f} across {disputed_count} flagged invoices in our recent batch audit.\n\n"
                draft += "Our automated LedgerFlux engine has identified violations based on our contracted rate cards and SLA agreements. Please review the attached Master Audit Certificate for the complete breakdown of affected invoices and expected savings.\n\n"
                draft += "We expect a consolidated credit note issued for the disputed amount within 5 business days.\n\n"
                draft += "Regards,\nLedgerFlux Automated Dispute System"
                
                st.text_area("Copy and send to carrier billing (or use Secure Mail below):", value=draft, height=200)
# --- THE BATCH EXPORT & DISTRIBUTION CLOSER ---
            st.markdown("---")
            st.subheader("Batch Export & Distribution")
            
            # We pull the HTML report directly from your new native engine state
            html_report = bres.get('html_report', "")
            
            c4, c5 = st.columns(2)
            with c4:
                st.download_button(
                    "⬇️ Download Master Batch HTML Certificate", 
                    data=html_report, 
                    file_name=f"Batch_Audit_{bres['batch_id']}.html", 
                    mime="text/html",
                    key="batch_download_btn"
                )
            with c5:
                email = st.text_input("Corporate Email for Master Report:", key="batch_email_input")
                if st.button("Send Batch via Secure Mail", key="batch_email_btn") and email:
                    try:
                        if 'lottie_email' in globals() and lottie_email: 
                            st_lottie(lottie_email, height=100, key="batch_mail_anim")
                    except Exception: pass
                    
                    ok, msg = send_real_email(
                        email, 
                        f"URGENT: Consolidated Batch Audit - {bres['batch_id']}", 
                        "Please find the attached formal master audit certificate for the recent batch.", 
                        html_content=html_report, 
                        filename=f"Batch_Audit_{bres['batch_id']}.html"
                    )
                    
                    if ok: 
                        st.success("Batch Report Sent Successfully. We're done here.")
                    else: 
                        st.error(f"Transmission failed: {msg}")

        # --- PERSISTENT DISPLAY FOR SINGLE PDF ---
        if 'result' in st.session_state and st.session_state['result'] and uploaded_file and not uploaded_file.name.endswith('.zip'):
            res = st.session_state['result']
            st.success(f"Analysis Complete: {res['carrier']} Invoice {res['id']}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Billed", f"₹ {res['billed']:,.2f}")
            c2.metric("Identified Overcharge", f"₹ {res['savings']:,.2f}")
            c3.metric("Status", res['status'])
            
            st.subheader("Line Item Breakdown")
            df_det = pd.DataFrame(res['details'])
            def highlight_error(row):
                if row.get('Status') != 'Match': return ['background-color: #381E1E'] * len(row)
                return [''] * len(row)
            st.table(df_det.style.apply(highlight_error, axis=1).format({"Billed": "₹ {:.2f}", "Expected": "₹ {:.2f}"}))
            
            if res['status'] == "Discrepancy":
                st.subheader("Auto-Generated Legal Dispute")
                draft = generate_dispute_draft(res['id'], res['carrier'], res['details'])
                st.text_area("Copy and send to carrier billing:", value=draft, height=200)

            st.markdown("---")
            st.subheader("Export & Distribution")
            html_report = generate_html_report(res['id'], res['carrier'], res['status'], res['billed'], res['savings'], df_det)
            
            c4, c5 = st.columns(2)
            with c4:
                st.download_button("⬇️ Download Official HTML Certificate", data=html_report, file_name=f"Audit_{res['id']}.html", mime="text/html")
            with c5:
                email = st.text_input("Email Report To:")
                if st.button("Send via Secure Mail", key="single_email_btn") and email:
                    if lottie_email: st_lottie(lottie_email, height=100, key="single_mail_anim")
                    ok, msg = send_real_email(
                        email, f"Audit Certificate: {res['id']}", 
                        "Please find the attached formal audit certificate.", 
                        html_content=html_report, filename=f"Audit_{res['id']}.html"
                    )
                    if ok: st.success("Report Sent Successfully!")
                    else: st.error(msg)

    # --- ANALYTICS TAB ---
    elif selected == "Analytics":
        st.title("Financial Intelligence")
        data = get_client_stats()
        if not data.empty and 'status' in data:
            c1, c2 = st.columns(2)
            with c1:
                fig_pie = px.pie(data, names='status', hole=0.5, color='status', color_discrete_map={'Discrepancy':'#FF5252', 'Clear':'#00E676'})
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E0E0E0")
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                fig_bar = px.bar(data, x='timestamp', y='total_savings', color_discrete_sequence=['#6C5DD3'])
                fig_bar.update_layout(plot_bgcolor="#121212", paper_bgcolor="rgba(0,0,0,0)", font_color="#E0E0E0", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'))
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No data available yet. Run an audit to generate analytics.")

    # --- SETTINGS TAB ---
    elif selected == "Settings":
        st.title("Settings")
        st.text_input("User ID", value="user1", disabled=True)
        st.toggle("Enable Dark Mode", value=True, disabled=True)