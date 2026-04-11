const express = require('express');
const cors = require('cors');
const multer = require('multer');
const AdmZip = require('adm-zip');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { PrismaClient } = require('@prisma/client');

console.log("[BOOT] Starting LedgerFlux Enterprise Engine...");
const prisma = new PrismaClient();
const app = express();

app.use(cors());
app.use(express.json());
app.get('/', (req, res) => res.send("LedgerFlux Enterprise API Online"));

const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);
const upload = multer({ dest: uploadDir });

// --- 1. SEED THE DATABASE (THE FIX) ---
async function initializeDB() {
    try {
        await prisma.client.upsert({
            where: { id: "OMNIACTIVE-UUID-001" },
            update: {},
            create: { id: "OMNIACTIVE-UUID-001", company_name: "OmniActive Health" }
        });
        console.log("[BOOT] Client relationship verified in Supabase.");
    } catch (e) {
        console.error("[BOOT] Warning: Could not verify client.", e.message);
    }
}
initializeDB();

// --- 2. THE DOORS ---
app.get('/health', async (req, res) => {
    try {
        await prisma.$queryRaw`SELECT 1`;
        res.json({ status: "Database Connected ⚡" });
    } catch (e) {
        res.status(500).json({ status: "Database Offline" });
    }
});

app.get('/api/audits/summary', async (req, res) => {
    try {
        const audits = await prisma.audit.findMany({ orderBy: { timestamp: 'desc' }, take: 50 });
        res.json(audits);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// --- 3. BATCH PROCESSOR (SYNCED FOR UI) ---
app.post('/api/upload/batch', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ error: "No ZIP provided" });

        const zip = new AdmZip(req.file.path);
        const extractDir = path.join(uploadDir, `batch_${Date.now()}`);
        zip.extractAllTo(extractDir, true);
        fs.unlinkSync(req.file.path);

        const files = fs.readdirSync(extractDir).filter(f => f.toLowerCase().endsWith('.pdf'));
        console.log(`[SYS] Processing ${files.length} invoices...`);

        const processedResults = [];
        let total_billed = 0;
        let total_savings = 0;

        for (const file of files) {
            const filePath = path.join(extractDir, file);
            
            await new Promise((resolve) => {
                exec(`python3 core/analyzer.py "${filePath}"`, async (err, stdout) => {
                    if (err) { console.error(`[PY] ${err.message}`); return resolve(); }
                    try {
                        const result = JSON.parse(stdout.trim());
                        
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
                        console.log(`[DB SUCCESS] ${result.invoice_id} secured.`);
                        
                        processedResults.push({
                            "Invoice ID": result.invoice_id, "Carrier": result.carrier,
                            "Status": result.status, "Billed": result.total_billed, "Recoverable": result.total_savings
                        });
                        total_billed += result.total_billed;
                        total_savings += result.total_savings;

                    } catch (dbErr) {
                        console.error("[CRITICAL DB ERROR] Failed to save:", dbErr.message);
                    }
                    resolve();
                });
            });
        }
        
        // Return everything to Streamlit so it can draw the UI
        res.json({
            message: "Batch processed successfully.",
            results: processedResults,
            total_billed: total_billed,
            total_savings: total_savings
        });

    } catch (err) {
        console.error("[FATAL]", err);
        res.status(500).send("Server Error");
    }
});

const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => { console.log(`⚡ LEDGERFLUX API: Port ${PORT}`); });