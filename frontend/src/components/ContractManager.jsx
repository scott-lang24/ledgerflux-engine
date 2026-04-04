import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle, Clock, Trash2 } from 'lucide-react';

const ContractManager = () => {
  const [contracts, setContracts] = useState([
    { id: 1, carrier: 'Delhivery', type: 'Surface LTL', expiry: '2026-12-31', status: 'Active' },
    { id: 2, carrier: 'BlueDart', type: 'Air Freight', expiry: '2025-10-15', status: 'Expired' },
  ]);

  const [isUploading, setIsUploading] = useState(false);

  const handleUploadDummy = () => {
    setIsUploading(true);
    setTimeout(() => {
      setContracts([
        { id: 3, carrier: 'Gati', type: 'Surface FTL', expiry: '2027-01-01', status: 'Active' },
        ...contracts
      ]);
      setIsUploading(false);
    }, 1500);
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Carrier Contract Matrix</h1>
        <p className="text-slate-500">Upload rate cards and Master Service Agreements (MSAs) to serve as the baseline for the audit engine.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload Section */}
        <div className="lg:col-span-1">
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <h2 className="text-xl font-bold text-slate-800 mb-4">Ingest Rate Card</h2>
            
            <div className="border-2 border-dashed border-blue-200 rounded-lg p-8 text-center bg-blue-50 hover:bg-blue-100 transition-colors mb-4">
              <UploadCloud className="mx-auto h-12 w-12 text-blue-500 mb-4" />
              <p className="text-sm font-medium text-slate-700 mb-1">Upload PDF or Excel</p>
              <p className="text-xs text-slate-500 mb-4">Engine will auto-extract DIM rules & zone rates.</p>
              <button 
                onClick={handleUploadDummy}
                disabled={isUploading}
                className="bg-blue-600 text-white text-sm px-4 py-2 rounded shadow hover:bg-blue-700 disabled:bg-blue-400"
              >
                {isUploading ? 'Extracting Data...' : 'Select Document'}
              </button>
            </div>
            
            <div className="bg-slate-50 p-4 rounded text-sm text-slate-600 border">
              <strong>Supported Formats:</strong>
              <ul className="list-disc ml-5 mt-2 space-y-1">
                <li>Standard PDF Contracts</li>
                <li>.XLSX Zone Matrices</li>
                <li>Signed MSAs</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Active Contracts List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <h2 className="text-xl font-bold text-slate-800">Active Rate Baseline</h2>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase">
                  <tr>
                    <th className="px-6 py-4 font-medium">Carrier / Type</th>
                    <th className="px-6 py-4 font-medium">Expiry Date</th>
                    <th className="px-6 py-4 font-medium">Status</th>
                    <th className="px-6 py-4 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {contracts.map((contract) => (
                    <tr key={contract.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <FileText className="h-5 w-5 text-slate-400 mr-3" />
                          <div>
                            <p className="font-semibold text-slate-800">{contract.carrier}</p>
                            <p className="text-xs text-slate-500">{contract.type}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">{contract.expiry}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          contract.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {contract.status === 'Active' ? <CheckCircle className="w-3 h-3 mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                          {contract.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button className="text-slate-400 hover:text-red-500 transition-colors">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default ContractManager;