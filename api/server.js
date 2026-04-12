const nodemailer = require('nodemailer');
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const AdmZip = require('adm-zip');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { PrismaClient } = require('@prisma/client');

console.log("\n[BOOT] Powering up LedgerFlux Enterprise Engine...");
const prisma = new PrismaClient();
const app = express();

// --- 1. ENTERPRISE MIDDLEWARE ---
app.use(cors());
app.use(express.json({ limit: '100mb' })); // Increased to 100mb for massive HTML attachments
app.use(express.urlencoded({ limit: '100mb', extended: true }));

const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
    console.log("[BOOT] Secure uploads directory created.");
}
const upload = multer({ dest: uploadDir });

// --- 2. DATABASE SEEDER ---
async function initializeDB() {
    try {
        await prisma.client.upsert({
            where: { id: "OMNIACTIVE-UUID-001" },
            update: {},
            create: { id: "OMNIACTIVE-UUID-001", company_name: "OmniActive Health" }
        });
        console.log("[BOOT] System Client 'OMNIACTIVE-UUID-001' verified in Supabase.");
    } catch (e) {
        console.error("[BOOT ERROR] Database connection failed. Check your .env file.", e.message);
    }
}
initializeDB();

// --- 3. THE DOORS (ROUTES) ---
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
    } catch (err) { 
        console.error("[API ERROR] Failed to fetch summary:", err);
        res.status(500).json({ error: err.message }); 
    }
});

// --- 4. BATCH PROCESSOR (WITH GARBAGE COLLECTION) ---
app.post('/api/upload/batch', upload.single('file'), async (req, res) => {
    let extractDir = null;
    try {
        if (!req.file) return res.status(400).json({ error: "No ZIP file provided in the payload." });

        console.log(`\n[SYS] Payload received. Size: ${(req.file.size / 1024 / 1024).toFixed(2)} MB`);
        
        const zip = new AdmZip(req.file.path);
        extractDir = path.join(uploadDir, `batch_${Date.now()}`);
        zip.extractAllTo(extractDir, true);
        
        // Delete the raw ZIP immediately
        if (fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);

        const files = fs.readdirSync(extractDir).filter(f => f.toLowerCase().endsWith('.pdf'));
        console.log(`[SYS] Unpacked ${files.length} PDFs. Engaging Python Workers...`);

        const processedResults = [];
        let total_billed = 0;
        let total_savings = 0;

        for (const file of files) {
            const filePath = path.join(extractDir, file);
            
            await new Promise((resolve) => {
                exec(`python3 core/analyzer.py "${filePath}"`, async (err, stdout, stderr) => {
                    if (err) { 
                        console.error(`[PY WORKER ERROR] Failed on ${file}: ${err.message}`); 
                        return resolve(); 
                    }
                    
                    try {
                        // TITANIUM PARSING: Extract ONLY the JSON, ignore Python warnings
                        const jsonMatch = stdout.match(/\{[\s\S]*\}/);
                        if (!jsonMatch) throw new Error("No valid JSON found in Python output.");
                        
                        const result = JSON.parse(jsonMatch[0]);
                        
                        // DB INSERT
                        await prisma.audit.create({
                            data: {
                                clientId: "OMNIACTIVE-UUID-001", 
                                invoice_number: result.invoice_id,
                                carrier_name: result.carrier,
                                status: result.status,
                                total_billed: result.total_billed,
                                total_savings: result.total_savings
                            }
                        });
                        console.log(`[DB SUCCESS] Invoice ${result.invoice_id} secured.`);
                        
                        processedResults.push({
                            "Invoice ID": result.invoice_id, 
                            "Carrier": result.carrier,
                            "Status": result.status, 
                            "Billed": result.total_billed, 
                            "Recoverable": result.total_savings
                        });
                        total_billed += result.total_billed;
                        total_savings += result.total_savings;

                    } catch (parseDbErr) {
                        console.error("[CRITICAL] Processing failed for file:", file, "| Error:", parseDbErr.message);
                    }
                    resolve();
                });
            });
        }
        
        // AUTO-GARBAGE COLLECTION: Delete the extracted PDFs to save disk space
        if (fs.existsSync(extractDir)) {
            fs.rmSync(extractDir, { recursive: true, force: true });
            console.log(`[SYS] Garbage Collection: Wiped temporary folder ${extractDir}`);
        }

        // Return Data to UI
        res.status(200).json({
            message: "Batch processed successfully.",
            results: processedResults,
            total_billed: total_billed,
            total_savings: total_savings
        });

    } catch (err) {
        console.error("[FATAL SERVER ERROR]", err);
        // Ensure cleanup happens even if the server crashes mid-process
        if (extractDir && fs.existsSync(extractDir)) {
            fs.rmSync(extractDir, { recursive: true, force: true });
        }
        if (!res.headersSent) res.status(500).json({ error: "Internal Server Error during Batch Processing." });
    }
});

// --- 5. AUTOMATED DISPUTE RELAY (PHASE 3) ---
app.post('/api/mail/send', async (req, res) => {
    try {
        const { to, subject, text, html_content, filename } = req.body;
        
        if (!to || !subject) {
            return res.status(400).json({ error: "Missing required email fields (to, subject)." });
        }

        console.log(`\n[MAILER] Engaging SMTP Relay to: ${to}`);

        // Set up the SMTP Transporter (Ethereal Testing)
        const transporter = nodemailer.createTransport({
            host: 'smtp.ethereal.email',
            port: 587,
            auth: {
                user: 'melyssa.cruickshank60@ethereal.email',
                pass: 'zN915M6fCwk5T1Fbdw'
            }
        });

        const mailOptions = {
            from: '"LedgerFlux Enterprise" <disputes@ledgerflux.com>',
            to: to,
            subject: subject,
            text: text,
            html: `
                <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                    <h2 style="color: #6C5DD3;">LedgerFlux Automated Dispute Request</h2>
                    <p>${text}</p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #888;">This is an automated legal dispute generated by the LedgerFlux System. Please review the attached HTML Certificate.</p>
                </div>
            `,
            attachments: [
                {
                    filename: filename || "Audit_Certificate.html",
                    content: html_content || "<p>No data provided.</p>",
                    contentType: 'text/html'
                }
            ]
        };

        const info = await transporter.sendMail(mailOptions);
        console.log(`[MAIL SUCCESS] Packet delivered. ID: ${info.messageId}`);
        
        const previewUrl = nodemailer.getTestMessageUrl(info);
        console.log(`[PREVIEW LINK] Open this URL to view the sent email: ${previewUrl}\n`);

        res.status(200).json({ message: "Dispute Sent", preview: previewUrl });
    } catch (err) {
        console.error("[MAIL ERROR] SMTP Relay Failed:", err);
        res.status(500).json({ error: "Failed to dispatch email." });
    }
});

// --- 6. IGNITION ---
const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => { 
    console.log(`====================================================`);
    console.log(`⚡ LEDGERFLUX API ROUTER ONLINE : PORT ${PORT}`);
    console.log(`====================================================\n`);
}); 