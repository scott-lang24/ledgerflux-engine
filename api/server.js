const express = require('express');
const cors = require('cors');
const multer = require('multer');
const AdmZip = require('adm-zip');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { PrismaClient } = require('@prisma/client');
const nodemailer = require('nodemailer');

console.log("\n[BOOT] Powering up LedgerFlux Enterprise Engine...");

// --- 1. INITIALIZATION & CORE SYSTEM ---
const prisma = new PrismaClient();
const app = express();

app.use(cors());
app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ limit: '100mb', extended: true }));

const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
const upload = multer({ dest: uploadDir });

// --- 2. THE SMTP CANNON (Loaded with your real credentials) ---
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: 'auditledgerflux@gmail.com', 
        pass: 'otyf wtfh jwhw kywf'      
    }
});

// --- 3. DATABASE SEEDER ---
async function initializeDB() {
    try {
        await prisma.client.upsert({
            where: { id: "OMNIACTIVE-UUID-001" },
            update: {},
            create: { id: "OMNIACTIVE-UUID-001", company_name: "OmniActive Health" }
        });
        console.log("[BOOT] System Client 'OMNIACTIVE-UUID-001' verified in Supabase.");
    } catch (e) {
        console.error("[BOOT ERROR] Database connection failed.", e.message);
    }
}
initializeDB();

// --- 4. ROUTES & ENDPOINTS ---

app.get('/', (req, res) => res.send("⚡ LedgerFlux API is Online and Routing Traffic."));

app.get('/health', async (req, res) => {
    try {
        await prisma.$queryRaw`SELECT 1`;
        res.status(200).json({ status: "Database Connected ⚡" });
    } catch (e) {
        res.status(500).json({ status: "Database Offline", error: e.message });
    }
});

app.get('/api/audits/summary', async (req, res) => {
    try {
        const audits = await prisma.audit.findMany({ orderBy: { timestamp: 'desc' }, take: 50 });
        res.json(audits);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// --- 5. THE AUTONOMOUS EMAIL DISPATCHER ---
app.post('/api/dispatch-certificate', async (req, res) => {
    const { to_email, audit_data, pdf_attachment } = req.body;

    if (!to_email || !audit_data) {
        return res.status(400).json({ error: "Missing payload data" });
    }

    console.log(`[*] Received dispatch request for: ${to_email}. Attaching PDF artifact.`);

    const htmlCertificate = `
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; max-width: 600px;">
            <h2 style="color: #d9534f; margin-top: 0;">LedgerFlux Forensic Alert</h2>
            <p><strong>Carrier:</strong> ${audit_data.carrier}</p>
            <h3 style="color: #292b2c;">Leakage Detected: <span style="color: #d9534f;">${audit_data.leakage_amount}</span></h3>
            <br/>
            <p><em>We have attached your official PDF Dispute Certificate to this email. Please forward the attachment to your carrier representative.</em></p>
        </div>
    `;

    const mailOptions = {
        from: 'auditledgerflux@gmail.com',
        to: to_email,
        subject: `ACTION REQUIRED: Invoice Discrepancy Found (${audit_data.leakage_amount})`,
        html: htmlCertificate,
        attachments: [
            {
                filename: `LedgerFlux_Dispute_${audit_data.invoice_ref}.pdf`,
                content: pdf_attachment,
                encoding: 'base64'
            }
        ]
    };

    try {
        await transporter.sendMail(mailOptions);
        console.log(`[+] Email with PDF Certificate successfully dispatched to ${to_email}`);
        res.status(200).json({ message: "Success" });
    } catch (error) {
        console.error("[-] Node Mailer Error:", error);
        res.status(500).json({ error: "Failed to dispatch" });
    }
});
// --- 6. IGNITION ---
const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => { 
    console.log(`====================================================`);
    console.log(`⚡ LEDGERFLUX API ROUTER ONLINE : PORT ${PORT}`);
    console.log(`====================================================\n`);
});