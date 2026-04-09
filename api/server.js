const express = require('express');
const cors = require('cors');
const multer = require('multer');
const AdmZip = require('adm-zip');
const fs = require('fs');
const { exec } = require('child_process');
const path = require('path');
const { PrismaClient } = require('@prisma/client');

// Initialize the Enterprise Tools
const prisma = new PrismaClient();
const app = express();
app.use(cors());
app.use(express.json());

// Setup secure local storage for incoming enterprise files
const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}
const upload = multer({ dest: uploadDir });

// --- THE BATCH ZIP UPLOAD ENDPOINT ---
// --- THE BATCH ZIP UPLOAD ENDPOINT (UPGRADED WITH PYTHON WORKER) ---
app.post('/api/upload/batch', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ error: "No ZIP file provided." });

        console.log(`\n[SYS] Unpacking Batch: ${req.file.originalname}`);
        const zip = new AdmZip(req.file.path);
        const extractDir = path.join(uploadDir, `batch_${Date.now()}`);
        zip.extractAllTo(extractDir, true);
        fs.unlinkSync(req.file.path); // Delete the raw zip

        const files = fs.readdirSync(extractDir).filter(f => f.toLowerCase().endsWith('.pdf'));
        console.log(`[LOG] Found ${files.length} PDFs. Firing Python Engine...`);

        // Send success to frontend immediately so browser doesn't freeze
        res.status(200).json({
            message: "Batch secured. Processing in background.",
            invoice_count: files.length,
            status: "PROCESSING"
        });

        // --- BACKGROUND WORKER QUEUE ---
        // (This runs silently after telling the frontend everything is okay)
        for (const file of files) {
            const filePath = path.join(extractDir, file);
            
            // Fire the Python Specialist
            exec(`python core/analyzer.py "${filePath}"`, async (error, stdout, stderr) => {
                if (error) {
                    console.error(`[PYTHON ERROR] ${error.message}`);
                    return;
                }
                
                try {
                    // Parse what Python spit out
                    const result = JSON.parse(stdout);
                    console.log(`[AUDIT COMPLETE] ${result.invoice_id} | Savings: ₹${result.total_savings}`);
                    
                    // Note: In Phase 3, we will insert 'result' into Supabase here!
                    
                } catch (parseErr) {
                    console.error("[JSON PARSE ERROR] Python output was not valid JSON:", stdout);
                }
            });
        }

    } catch (error) {
        console.error("[ERROR] Batch Processing Failed:", error);
        if (!res.headersSent) res.status(500).json({ error: "Failed to process ZIP archive." });
    }
});