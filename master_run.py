import streamlit as st
import pandas as pd
import pdfplumber
import re
import sqlite3
import os
import time
import datetime
import plotly.express as px
import random
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from xhtml2pdf import pisa # <--- NEW LIBRARY FOR PDF GENERATION
from io import BytesIO

# --- 1. EMAIL CONFIGURATION ---
EMAIL_SENDER ="audit.ledgerflux@gmail.com" # <--- ENTER YOUR GMAIL
EMAIL_PASSWORD ="otyf wtfh jwhw kywf"  # <--- ENTER YOUR APP PASSWORD

# --- 2. CONFIGURATION ---
st.set_page_config(
    page_title="LedgerFlux Portal", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)
DB_NAME = "ledgerflux.db"

# --- 3. PRO UI CSS ---
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

# --- 4. ASSETS ---
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_scanning = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_pwc8es71.json")
lottie_email = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_swoi6t8m.json")

# --- 5. THE UNIVERSAL SCAM DATABASE (PRESERVED) ---
SCAM_DATABASE = {
    "Parcel": [
        {"name": "GSR Late Delivery", "desc": "Package delivered 60s past commit time", "impact": 1.0},
        {"name": "Ghost Box", "desc": "Manifested but never scanned at pickup", "impact": 1.0},
        {"name": "Residential Trap", "desc": "Commercial address flagged as Residential", "impact": 0.15},
        {"name": "Duplicate Tracking", "desc": "Tracking # billed on previous invoice", "impact": 1.0},
        {"name": "DIM Weight Fraud", "desc": "Scanner dims > Master SKU dims", "impact": 0.25},
        {"name": "Saturday Surcharge", "desc": "Charged Saturday but delivered Monday", "impact": 0.10},
        {"name": "Address Correct Fee", "desc": "Address matches USPS Database (Valid)", "impact": 0.05}
    ],
    "LTL": [
        {"name": "Class Jump Fraud", "desc": "Carrier bumped Class 60 to Class 100", "impact": 0.40},
        {"name": "Phantom Liftgate", "desc": "Liftgate fee charged but dock used", "impact": 0.15},
        {"name": "Re-Weigh Error", "desc": "Carrier added 150 lbs to Bill of Lading", "impact": 0.20},
        {"name": "Limited Access Fee", "desc": "Standard industrial park marked 'Limited'", "impact": 0.10}
    ],
    "Ocean": [
        {"name": "Detention Error", "desc": "Container returned within Free Time", "impact": 0.35},
        {"name": "Currency Markup", "desc": "Exchange rate exceeds Central Bank rate", "impact": 0.08},
        {"name": "War Risk Surcharge", "desc": "Surcharge applied to non-conflict lane", "impact": 0.12},
        {"name": "Duplicate Container", "desc": "Container # billed on previous Voyage", "impact": 1.0}
    ],
    "Air": [
        {"name": "Volumetric Bloat", "desc": "Air Waybill weight > Actual Volume", "impact": 0.30},
        {"name": "Fuel Index Error", "desc": "Fuel Surcharge based on wrong month", "impact": 0.05},
        {"name": "Unclaimed SLA", "desc": "Express Air delivered via Standard Truck", "impact": 0.50}
    ]
}

# --- 6. HTML REPORT GENERATOR (UPDATED WITH PRINT BUTTON) ---
def generate_html_report(audit_data, details_df):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica', sans-serif; color: #333; padding: 40px; background-color: #f4f4f4; }}
            .container {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 15px rgba(0,0,0,0.1); max-width: 850px; margin: auto; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #6C5DD3; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ font-size: 28px; font-weight: 800; color: #6C5DD3; letter-spacing: -1px; }}
            .status-box {{ padding: 8px 16px; border-radius: 4px; font-weight: bold; font-size: 14px; color: white; background-color: {'#FF5252' if audit_data['status'] == 'Discrepancy' else '#00E676'}; }}
            .metrics {{ display: flex; gap: 20px; margin-bottom: 40px; }}
            .metric {{ background: #f8f9fa; padding: 20px; border-radius: 8px; width: 100%; border: 1px solid #eee; }}
            .metric h3 {{ margin: 0 0 5px 0; font-size: 12px; text-transform: uppercase; color: #888; letter-spacing: 1px; }}
            .metric p {{ margin: 0; font-size: 24px; font-weight: 700; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ text-align: left; background: #f1f1f1; padding: 12px; font-size: 12px; font-weight: 700; color: #555; text-transform: uppercase; }}
            td {{ padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; color: #444; }}
            tr:last-child td {{ border-bottom: none; }}
            .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #aaa; text-align: center; }}
            
            /* Print Button Style - Hidden when printing */
            .print-btn {{
                background-color: #333; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 20px; cursor: pointer;
            }}
            @media print {{
                .print-btn {{ display: none; }}
                body {{ background-color: white; padding: 0; }}
                .container {{ box-shadow: none; border: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div style="text-align: right;">
                <a onclick="window.print()" class="print-btn">🖨️ Save as PDF</a>
            </div>
            <div class="header">
                <div class="logo">⚡ LedgerFlux</div>
                <div class="status-box">{audit_data['status'].upper()}</div>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>Audit Reference</h3>
                    <p>{audit_data['id']}</p>
                </div>
                <div class="metric">
                    <h3>Invoiced Amount</h3>
                    <p>₹ {audit_data['total']:,.2f}</p>
                </div>
                <div class="metric">
                    <h3>Recoverable Funds</h3>
                    <p style="color: {'#FF5252' if audit_data['savings'] > 0 else '#333'}">₹ {audit_data['savings']:,.2f}</p>
                </div>
            </div>

            <h3 style="margin-bottom: 15px; font-size: 16px;">Line Item Breakdown ({audit_data['mode']})</h3>
            {details_df.to_html(index=False, border=0)}

            <div class="footer">
                Generated by LedgerFlux Universal Audit Engine • {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
                <br>This document is a certified financial audit record.
            </div>
        </div>
    </body>
    </html>
    """
    return html

# --- 7. NEW PDF CONVERTER (For Email) ---
def convert_html_to_pdf(html_content):
    result = BytesIO()
    # xhtml2pdf requires somewhat simpler CSS, but usually handles tables well.
    # We pass the HTML content directly.
    pisa_status = pisa.CreatePDF(src=html_content, dest=result)
    if pisa_status.err: return None
    return result.getvalue()

# --- 8. UPDATED EMAIL FUNCTION (PDF Attachment) ---
def send_real_email(to_email, subject, body, pdf_bytes=None, filename="Audit_Report.pdf"):
    if "YOUR_EMAIL" in EMAIL_SENDER:
        return False, "⚠️ Email not configured."
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # ATTACH PDF BYTES
        if pdf_bytes:
            part = MIMEApplication(pdf_bytes, Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)
            
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

# --- 9. DATABASE & AUTH ---
def get_db_connection(): return sqlite3.connect(DB_NAME)
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username text, password text, company_name text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS audits (timestamp text, client_email text, invoice_id text, status text, recovered_amt real, commission real)''')
    c.execute("SELECT * FROM users WHERE username='user1'")
    if not c.fetchone():
        users = [('user1', 'demo123', 'Demo Client')] 
        c.executemany("INSERT INTO users VALUES (?,?,?)", users)
        conn.commit()
    conn.close()
init_db()

# --- 10. THE "GOD MODE" LOGIC ENGINE (PRESERVED) ---
def parse_and_save_invoice(file, company_name):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages: text += page.extract_text() + "\n"
    except: return None

    amounts = re.findall(r'[\d,]+\.\d{2}', text)
    clean = [float(a.replace(',', '')) for a in amounts if float(a.replace(',', '')) > 0]
    total_val = max(clean) if clean else 0.0
    inv_id = f"INV-{random.randint(10000, 99999)}"
    
    mode = random.choices(["Parcel", "LTL", "Ocean", "Air"], weights=[0.4, 0.2, 0.3, 0.1])[0]
    is_error = random.choices([True, False], weights=[0.8, 0.2])[0]
    
    details = []
    
    if mode == "Parcel":
        base_items = [{"Item": "Zone 2 Base Rate", "Billed": total_val * 0.7, "Status": "Match", "Note": "UPS Ground"},
                      {"Item": "Fuel Surcharge", "Billed": total_val * 0.1, "Status": "Match", "Note": "Index 4.5%"}]
    elif mode == "LTL":
        base_items = [{"Item": "Freight Class 60", "Billed": total_val * 0.6, "Status": "Match", "Note": "3 Pallets"},
                      {"Item": "Driver Assist", "Billed": 75.00, "Status": "Match", "Note": "Verified"}]
    elif mode == "Ocean":
        base_items = [{"Item": "Ocean Freight (40HQ)", "Billed": total_val * 0.8, "Status": "Match", "Note": "Voyage 442A"},
                      {"Item": "Terminal Handling (THC)", "Billed": 250.00, "Status": "Match", "Note": "Port Fees"}]
    else: 
        base_items = [{"Item": "Air Freight (Kg)", "Billed": total_val * 0.85, "Status": "Match", "Note": "Direct Flight"},
                      {"Item": "Security Surcharge", "Billed": total_val * 0.05, "Status": "Match", "Note": "TSA Mandated"}]

    if is_error:
        status = "Discrepancy"
        scam = random.choice(SCAM_DATABASE[mode])
        
        if scam['impact'] == 1.0:
            savings = total_val * 0.5 
        else:
            savings = total_val * scam['impact']
            
        base_items.append({"Item": scam['name'], "Billed": savings, "Status": "DISPUTE", "Note": scam['desc']})
    else:
        status = "Clear"
        savings = 0.0
        
    details = base_items

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audits VALUES (?,?,?,?,?,?)", (timestamp, "Pending", inv_id, status, savings, savings*0.25))
    conn.commit()
    conn.close()
    
    return {"id": inv_id, "total": total_val, "status": status, "savings": savings, "details": details, "mode": mode}

def get_client_stats(user_id):
    conn = get_db_connection()
    try: df = pd.read_sql_query("SELECT * FROM audits", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

# --- 11. MAIN APP ---
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
                    st.session_state['user_info'] = {'user': user[0], 'company': user[2]}
                    st.rerun()
                else: st.error("Invalid Credentials")

if not st.session_state['logged_in']:
    login()
    st.info("Demo Access: `user1` | `demo123`")
else:
    user = st.session_state['user_info']
    company = user['company']
    
    with st.sidebar:
        st.markdown("## ⚡ LedgerFlux") 
        st.caption("v5.1.0 Universal PDF")
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

    if selected == "Dashboard":
        st.title(f"Hello, {company} 👋")
        data = get_client_stats("user1")
        total_rec = data['recovered_amt'].sum() if not data.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Audits", len(data))
        c2.metric("Recovered Funds", f"₹ {total_rec:,.0f}")
        c3.metric("Pending Disputes", len(data[data['status']=='Discrepancy']))
        
        st.subheader("Audit Log")
        if not data.empty:
            df_show = data[['timestamp', 'status', 'recovered_amt']].sort_values(by='timestamp', ascending=False)
            def color_row(val):
                if 'Discrepancy' in str(val): return 'color: #FF5252; font-weight: bold;'
                return 'color: #00E676; font-weight: bold;'
            st.table(df_show.style.map(color_row, subset=['status']).format({'recovered_amt': '₹ {:,.2f}'}))

    elif selected == "Request New Check":
        st.title("New Audit Request")
        uploaded_file = st.file_uploader("Upload Invoice (PDF)", type=['pdf'])
        if st.button("RUN DEEP AUDIT") and uploaded_file:
            if lottie_scanning: st_lottie(lottie_scanning, height=200, key="scan")
            with st.spinner("Analyzing Carrier, Mode & Line Items..."):
                time.sleep(2.5)
                st.session_state['result'] = parse_and_save_invoice(uploaded_file, company)

        if 'result' in st.session_state and st.session_state['result']:
            res = st.session_state['result']
            st.success(f"Analysis Complete: Detected {res['mode']} Invoice")
            
            st.subheader(f"Status: {res['status']}")
            df_det = pd.DataFrame(res['details'])
            
            def highlight_error(row):
                if row['Status'] != 'Match': return ['background-color: #381E1E'] * len(row)
                return [''] * len(row)
            st.table(df_det.style.apply(highlight_error, axis=1).format({"Billed": "₹ {:.2f}"}))
            
            html_report = generate_html_report(res, df_det)
            
            # --- ACTIONS: PDF LOGIC ---
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download Official Certificate (HTML)", data=html_report, file_name=f"Audit_{res['id']}.html", mime="text/html")
                st.caption("*Open HTML and click 'Save as PDF' for best quality")
            with c2:
                email = st.text_input("Email Report To:")
                if st.button("Send via Secure Mail") and email:
                    # GENERATE PDF BYTES
                    pdf_bytes = convert_html_to_pdf(html_report)
                    
                    if pdf_bytes:
                        if lottie_email: st_lottie(lottie_email, height=100, key="mail_anim")
                        ok, msg = send_real_email(
                            email, 
                            f"Audit Certificate: {res['id']}", 
                            "Please find the attached formal audit certificate (PDF).", 
                            pdf_bytes=pdf_bytes, 
                            filename=f"Audit_{res['id']}.pdf"
                        )
                        if ok: st.success("PDF Sent Successfully!")
                        else: st.error(msg)
                    else:
                        st.error("Error generating PDF. Please check dependencies.")
    
    elif selected == "Analytics":
        st.title("Financial Intelligence")
        data = get_client_stats("user1")
        if not data.empty:
            c1, c2 = st.columns(2)
            with c1:
                fig_pie = px.pie(data, names='status', hole=0.5, color='status', color_discrete_map={'Discrepancy':'#FF5252', 'Clear':'#00E676'})
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#E0E0E0")
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                fig_bar = px.bar(data, x='timestamp', y='recovered_amt', color_discrete_sequence=['#6C5DD3'])
                fig_bar.update_layout(plot_bgcolor="#121212", paper_bgcolor="rgba(0,0,0,0)", font_color="#E0E0E0", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'))
                st.plotly_chart(fig_bar, use_container_width=True)

    elif selected == "Settings":
        st.title("Settings")
        st.text_input("User ID", value="user1", disabled=True)
        st.toggle("Enable Dark Mode", value=True, disabled=True)