import streamlit as st
import pandas as pd
import zipfile
import sqlite3
import os
import time
import datetime
import plotly.express as px
import requests
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from io import BytesIO

# --- IMPORT OUR NEW MODULAR ENGINES (The V8 Under the Hood) ---
from core.db_manager import init_db, log_audit, get_db_connection
from core.ocr_engine import extract_invoice_data
from core.contract_engine import run_audit
from core.dispute_builder import generate_dispute_draft
from core.report_engine import generate_html_report, send_real_email

# --- 1. CONFIGURATION & DB INIT ---
st.set_page_config(
    page_title="LedgerFlux Portal", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()

# --- ADDITION: OVERRIDE COMPANY NAME TO DEMO CLIENT ---
conn = get_db_connection()
conn.execute("UPDATE users SET company_name='Demo Client' WHERE username='user1'")
conn.commit()
conn.close()
# ------------------------------------------------------

# --- 2. PRO UI CSS (Your Original Masterpiece) ---
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
    conn = get_db_connection()
    try: df = pd.read_sql_query("SELECT * FROM audits ORDER BY timestamp DESC", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

# --- 4. MAIN APP & LOGIN FLOW ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

def login():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("## ⚡ LedgerFlux")
        st.caption("Secure Portal Access")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log In"):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['logged_in'] = True
                    # Re-fetch company name just in case the update above fired
                    st.session_state['user_info'] = {'user': user[0], 'company': "Demo Client"}
                    st.rerun()
                else: st.error("Invalid Credentials")

if not st.session_state['logged_in']:
    login()
    st.info("Demo Access: `user1` | `demo123`")
else:
    user = st.session_state['user_info']
    company = user['company']
    
    # --- SIDEBAR (Restored) ---
    with st.sidebar:
        st.markdown("## ⚡ LedgerFlux") 
        st.caption("v6.1 Modular Enterprise Cloud")
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
        total_rec = data['recovered_amt'].sum() if not data.empty and 'recovered_amt' in data else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Audits", len(data))
        c2.metric("Identified Leakage", f"₹ {total_rec:,.0f}")
        c3.metric("Pending Disputes", len(data[data['status']=='Discrepancy']) if not data.empty else 0)
        c4.metric("EBITDA Impact", f"+ {(total_rec / 500000) * 100:.1f}%" if total_rec > 0 else "0.0%")
        
        st.subheader("Audit Log")
        if not data.empty:
            df_show = data[['timestamp', 'status', 'recovered_amt']].copy()
            def color_row(val):
                if 'Discrepancy' in str(val): return 'color: #FF5252; font-weight: bold;'
                return 'color: #00E676; font-weight: bold;'
            st.table(df_show.style.map(color_row, subset=['status']).format({'recovered_amt': '₹ {:,.2f}'}))

    # --- REQUEST NEW CHECK TAB (The Hybrid UI + Engine) ---
    elif selected == "Request New Check":
        st.title("New Audit Request")
        
        st.subheader("Audit Parameters")
        
        # --- ADDITION: THE DUAL-PARAMETER SELECTOR ---
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
        # ---------------------------------------------
        
        uploaded_file = st.file_uploader("Upload Invoice(s) (PDF or .ZIP batch)", type=['pdf', 'zip'])
        
        if st.button("RUN DEEP AUDIT") and uploaded_file:
            if lottie_scanning: st_lottie(lottie_scanning, height=200, key="scan")
            
            terminal = st.empty()
            
            # --- BATCH ZIP LOGIC ---
            if uploaded_file.name.endswith('.zip'):
                terminal.code("[SYS] ZIP Archive detected. Unpacking batch...", language="bash")
                time.sleep(1)
                
                results = []
                with zipfile.ZipFile(uploaded_file, 'r') as z:
                    pdf_files = [f for f in z.namelist() if f.endswith('.pdf')]
                    terminal.code(f"[LOG] Found {len(pdf_files)} invoices. Routing to {carrier} ({trade_lane}) Schema...", language="bash")
                    
                    for pdf_name in pdf_files:
                        with z.open(pdf_name) as pdf_file:
                            pdf_bytes = BytesIO(pdf_file.read())
                            
                            # Call the new modular engines
                            inv_id, extracted_rows = extract_invoice_data(pdf_bytes, carrier)
                            status, billed, savings, details = run_audit(extracted_rows, carrier)
                            log_audit(inv_id, status, billed, savings)
                            
                            results.append({"id": inv_id, "mode": carrier, "status": status, "total": billed, "savings": savings})
                
                terminal.empty()
                st.success(f"Batch Analysis Complete: Processed {len(results)} Invoices")
                
                total_billed = sum(r['total'] for r in results)
                total_savings = sum(r['savings'] for r in results)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Invoices Audited", len(results))
                c2.metric("Total Invoiced", f"₹ {total_billed:,.2f}")
                c3.metric("Total Recoverable", f"₹ {total_savings:,.2f}")
                
                st.subheader("Batch Breakdown")
                batch_df = pd.DataFrame([{
                    "Invoice ID": r['id'], "Carrier": r['mode'], "Status": r['status'], 
                    "Billed": f"₹ {r['total']:,.2f}", "Recoverable": f"₹ {r['savings']:,.2f}"
                } for r in results])
                
                def color_status(val):
                    return 'color: #FF5252; font-weight: bold;' if val == 'Discrepancy' else 'color: #00E676; font-weight: bold;'
                st.dataframe(batch_df.style.map(color_status, subset=['Status']), use_container_width=True)
                
            # --- SINGLE PDF LOGIC ---
            else:
                terminal.code(f"[SYS] Phase 1: Initiating {carrier} OCR Vision Engine...", language="bash")
                inv_id, extracted_rows = extract_invoice_data(uploaded_file, carrier)
                time.sleep(1)
                terminal.code(f"[SYS] Phase 2: Cross-referencing {trade_lane} rate cards...", language="bash")
                
                status, billed, savings, details = run_audit(extracted_rows, carrier)
                log_audit(inv_id, status, billed, savings)
                
                time.sleep(1)
                terminal.empty() 
                
                # Save to session state so UI can render it
                st.session_state['result'] = {
                    "id": inv_id, "carrier": carrier, "status": status, 
                    "billed": billed, "savings": savings, "details": details
                }

        # Display single result actions
        if 'result' in st.session_state and st.session_state['result'] and not (uploaded_file and uploaded_file.name.endswith('.zip')):
            res = st.session_state['result']
            st.success(f"Analysis Complete: {res['carrier']} Invoice {res['id']}")
            
            # Overview Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Billed", f"₹ {res['billed']:,.2f}")
            c2.metric("Identified Overcharge", f"₹ {res['savings']:,.2f}")
            c3.metric("Status", res['status'])
            
            # Line Item Table
            st.subheader("Line Item Breakdown")
            df_det = pd.DataFrame(res['details'])
            def highlight_error(row):
                if row.get('Status') != 'Match': return ['background-color: #381E1E'] * len(row)
                return [''] * len(row)
            st.table(df_det.style.apply(highlight_error, axis=1).format({"Billed": "₹ {:.2f}", "Expected": "₹ {:.2f}"}))
            
            # Dispute Builder
            if res['status'] == "Discrepancy":
                st.subheader("Auto-Generated Legal Dispute")
                draft = generate_dispute_draft(res['id'], res['carrier'], res['details'])
                st.text_area("Copy and send to carrier billing:", value=draft, height=200)

            # HTML & Email Routing
            st.markdown("---")
            html_report = generate_html_report(res['id'], res['carrier'], res['status'], res['billed'], res['savings'], df_det)
            
            c4, c5 = st.columns(2)
            with c4:
                st.download_button("⬇️ Download Official HTML Certificate", data=html_report, file_name=f"Audit_{res['id']}.html", mime="text/html")
            with c5:
                email = st.text_input("Email Report To:")
                if st.button("Send via Secure Mail") and email:
                    if lottie_email: st_lottie(lottie_email, height=100, key="mail_anim")
                    ok, msg = send_real_email(
                        email, f"Audit Certificate: {res['id']}", 
                        "Please find the attached formal audit certificate.", 
                        html_content=html_report, filename=f"Audit_{res['id']}.html"
                    )
                    if ok: st.success("Report Sent Successfully!")
                    else: st.error(msg)

    # --- ANALYTICS TAB (Restored) ---
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
                fig_bar = px.bar(data, x='timestamp', y='recovered_amt', color_discrete_sequence=['#6C5DD3'])
                fig_bar.update_layout(plot_bgcolor="#121212", paper_bgcolor="rgba(0,0,0,0)", font_color="#E0E0E0", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'))
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No data available yet. Run an audit to generate analytics.")

    # --- SETTINGS TAB (Restored) ---
    elif selected == "Settings":
        st.title("Settings")
        st.text_input("User ID", value="user1", disabled=True)
        st.toggle("Enable Dark Mode", value=True, disabled=True)