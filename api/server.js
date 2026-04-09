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
        
        // Immediate Response to Streamlit
        res.json({ message: "Batch received", invoice_count: files.length, status: "PROCESSING" });

        // Background Math
        files.forEach(file => {
            const filePath = path.join(extractDir, file);
            exec(`python3 core/analyzer.py "${filePath}"`, (err, stdout) => {
                if (err) return console.error(`[PY ERROR] ${err.message}`);
                const result = JSON.parse(stdout);
                console.log(`[AUDIT] ${result.invoice_id} | Saved: ₹${result.total_savings}`);
            });
        });
    } catch (err) {
        console.error("[FATAL] Batch failed:", err);
        if (!res.headersSent) res.status(500).send("Server Error");
    }
});

// 5. The Ignition (THE FIX)
const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`\n======================================`);
    console.log(`⚡ LEDGERFLUX API: http://localhost:${PORT}`);
    console.log(`======================================\n`);
});