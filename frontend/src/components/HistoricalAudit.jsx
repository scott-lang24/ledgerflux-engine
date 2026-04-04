import React from 'react';
import { BarChart2 } from 'lucide-react';

const HistoricalAudit = () => {
  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="flex items-center space-x-3 mb-8">
        <BarChart2 className="w-8 h-8 text-blue-600" />
        <h1 className="text-3xl font-bold text-slate-900">Audit Results Dashboard</h1>
      </div>
      
      <div className="bg-white p-10 rounded-lg border border-slate-200 shadow-sm text-center">
        <h2 className="text-xl font-semibold text-slate-700 mb-2">Awaiting Invoice Data</h2>
        <p className="text-slate-500">
          The forensic engine requires a batch of carrier invoices to process. 
          Please navigate to the Upload screen to ingest your ZIP file.
        </p>
      </div>
    </div>
  );
};

export default HistoricalAudit;