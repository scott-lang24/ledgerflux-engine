const express = require('express');
const cors = require('cors');
const multer = require('multer');
const AdmZip = require('adm-zip');
const fs = require('fs');
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
app.post('/api/upload/batch', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No ZIP file provided." });
        }

        // 1. Unpack the ZIP
        console.log(`[SYS] Receiving Batch ZIP: ${req.file.originalname}`);
        const zip = new AdmZip(req.file.path);
        const zipEntries = zip.getEntries();
        
        // 2. Filter for PDFs only
        const pdfFiles = zipEntries.filter(entry => entry.entryName.toLowerCase().endsWith('.pdf'));
        console.log(`[LOG] Extracted ${pdfFiles.length} invoices for processing.`);

        // 3. (Mock) Grab the Client ID from the request header 
        // In production, this comes from their JWT login token
        const clientId = req.headers['x-client-id'] || "PENDING-CLIENT-UUID";

        // 4. Clean up the raw ZIP file to save server space
        fs.unlinkSync(req.file.path);

        // 5. Return the payload to the frontend so it can trigger the Python Engine
        return res.status(200).json({
            message: "Batch received and unpacked successfully.",
            invoice_count: pdfFiles.length,
            status: "QUEUED_FOR_AUDIT"
        });

    } catch (error) {
        console.error("[ERROR] Batch Processing Failed:", error);
        return res.status(500).json({ error: "Failed to process ZIP archive." });
    }
});
// --- ROOT ENDPOINT ---
app.get('/', (req, res) => {
    res.status(200).send("LedgerFlux Enterprise API V1 is Online.");
});
// --- HEALTH CHECK ENDPOINT ---
app.get('/health', async (req, res) => {
    try {
        // Ping Supabase to ensure connection is alive
        await prisma.$queryRaw`SELECT 1`;
        res.status(200).json({ status: "LedgerFlux API & Database Online ⚡" });
    } catch (e) {
        res.status(500).json({ status: "Database Connection Failed" });
    }
});

// --- IGNITION ---
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`\n======================================`);
    console.log(`⚡ LEDGERFLUX ENTERPRISE API RUNNING`);
    console.log(`🚀 Port: ${PORT}`);
    console.log(`======================================\n`);
});