import React from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import UploadArea from './components/UploadArea';
// Ensure you have HistoricalAudit.jsx in your components folder too!
import HistoricalAudit from './components/HistoricalAudit';

const UploadScreen = () => {
  const navigate = useNavigate();
  return (
    <div className="w-full max-w-4xl space-y-8 mt-12 mx-auto px-4">
      <div className="text-center">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
          LedgerFlux Command Center
        </h1>
        <p className="mt-2 text-lg text-slate-600">
          Enterprise Forensic Freight Audit Pipeline
        </p>
      </div>
      <UploadArea onSuccess={() => navigate('/dashboard')} />
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50">
        <Routes>
          <Route path="/" element={<UploadScreen />} />
          <Route path="/dashboard" element={<HistoricalAudit />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;