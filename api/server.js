const express = require('express');
const cors = require('cors');
const multer = require('multer');
const AdmZip = require('adm-zip');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { PrismaClient } = require('@prisma/client');

// 1. Initializing Tools
console.log("[BOOT] Starting LedgerFlux Engine...");
const prisma = new PrismaClient();
const app = express();

app.use(cors());
app.use(express.json());

// 2. Setup Upload Directory
const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
    console.log("[BOOT] Created uploads directory.");
}
const upload = multer({ dest: uploadDir });

// 3. Root & Health Check (The "Doors")
app.get('/', (req, res) => res.send("LedgerFlux API V1 Online"));

app.get('/health', async (req, res) => {
    try {
        await prisma.$queryRaw`SELECT 1`;
        res.json({ status: "Database Connected ⚡" });
    } catch (e) {
        res.status(500).json({ status: "Database Offline", error: e.message });
    }
});

// 4. The Batch Processor
app.post('/api/upload/batch', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ error: "No ZIP provided" });

        const zip = new AdmZip(req.file.path);
        const extractDir = path.join(uploadDir, `batch_${Date.now()}`);
        zip.extractAllTo(extractDir, true);
        fs.unlinkSync(req.file.path);

        const files = fs.readdirSync(extractDir).filter(f => f.toLowerCase().endsWith('.pdf'));
        
        // Immediate Response to Streamlit so the UI stays snappy
        res.json({ message: "Batch received", invoice_count: files.length, status: "PROCESSING" });

        // Background Math - This is where the Python Specialist works
        files.forEach(file => {
            const filePath = path.join(extractDir, file);
            exec(`python3 core/analyzer.py "${filePath}"`, async (err, stdout) => {
                if (err) return console.error(`[PY ERROR] ${err.message}`);
                
                try {
                    const result = JSON.parse(stdout);
                    console.log(`[AUDIT] ${result.invoice_id} | Saving to DB...`);

                    // Save result to Supabase via Prisma
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

                } catch (parseErr) {
                    console.error("[JSON ERROR] Python output was invalid:", stdout);
                }
            });
        });
    } catch (err) {
        console.error("[FATAL] Batch failed:", err);
        if (!res.headersSent) res.status(500).send("Server Error");
    }
});

// 5. Get Audit Summary (For the Streamlit Dashboard)
app.get('/api/audits/summary', async (req, res) => {
    try {
        const audits = await prisma.audit.findMany({
            orderBy: { timestamp: 'desc' },
            take: 20 
        });
        res.json(audits);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 6. Ignition
const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n======================================`);
    console.log(`⚡ LEDGERFLUX API: http://localhost:${PORT}`);
    console.log(`======================================\n`);
});