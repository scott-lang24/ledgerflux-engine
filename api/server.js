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
// Background Math
        files.forEach(file => {
            const filePath = path.join(extractDir, file);
            exec(`python3 core/analyzer.py "${filePath}"`, async (err, stdout) => {
                if (err) return console.error(`[PY ERROR] ${err.message}`);
                
                try {
                    const result = JSON.parse(stdout);
                    console.log(`[AUDIT] ${result.invoice_id} | Saved to DB`);

                    // --- THE DB INSERT (PHASE 2 POWER) ---
                    await prisma.audit.create({
                        data: {
                            clientId: "OMNIACTIVE-UUID-001", // Hardcoded for demo
                            invoice_number: result.invoice_id,
                            carrier_name: result.carrier,
                            status: result.status,
                            total_billed: result.total_billed,
                            total_savings: result.total_savings
                        }
                    });

                } catch (parseErr) {
                    console.error("[JSON ERROR]", stdout);
                }
            });
        });