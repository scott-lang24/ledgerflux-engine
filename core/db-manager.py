import sqlite3
import datetime

DB_NAME = "ledgerflux.db"

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username text, password text, company_name text)''')
    c.execute('''CREATE TABLE IF NOT EXISTS audits 
                 (timestamp text, invoice_id text, status text, billed real, recovered_amt real)''')
    
    # Create default user if none exists
    c.execute("SELECT * FROM users WHERE username='user1'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('user1', 'demo123', 'OmniActive Health')")
        conn.commit()
    conn.close()

def log_audit(invoice_id, status, billed, savings):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audits VALUES (?,?,?,?,?)", 
              (timestamp, invoice_id, status, billed, savings))
    conn.commit()
    conn.close()