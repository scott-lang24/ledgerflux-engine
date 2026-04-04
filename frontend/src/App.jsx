import React from 'react';
import { BrowserRouter, Routes, Route, useNavigate, Link, useLocation } from 'react-router-dom';
import UploadArea from './components/UploadArea';
import HistoricalAudit from './components/HistoricalAudit';
import ContractManager from './components/ContractManager'; // Import the new file!
import { Box, FileText, BarChart2 } from 'lucide-react';

// --- NEW NAVIGATION BAR ---
const Navbar = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-500 hover:text-slate-800';

  return (
    <nav className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between shadow-sm">
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold">LF</div>
        <span className="text-xl font-bold text-slate-900 tracking-tight">LedgerFlux</span>
      </div>
      <div className="flex space-x-8">
        <Link to="/" className={`flex items-center space-x-2 pb-1 font-medium ${isActive('/')}`}>
          <Box className="w-4 h-4" /> <span>Upload</span>
        </Link>
        <Link to="/contracts" className={`flex items-center space-x-2 pb-1 font-medium ${isActive('/contracts')}`}>
          <FileText className="w-4 h-4" /> <span>Contracts</span>
        </Link>
        <Link to="/dashboard" className={`flex items-center space-x-2 pb-1 font-medium ${isActive('/dashboard')}`}>
          <BarChart2 className="w-4 h-4" /> <span>Audit Results</span>
        </Link>
      </div>
      <div>
        <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center text-slate-600 font-bold text-sm">O</div>
      </div>
    </nav>
  );
};

const UploadScreen = () => {
  const navigate = useNavigate();
  return (
    <div className="w-full max-w-4xl space-y-8 mt-12 mx-auto px-4">
      <div className="text-center">
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
          Enterprise Freight Audit
        </h1>
        <p className="mt-2 text-lg text-slate-600">
          Upload 12-24 months of raw carrier invoices.
        </p>
      </div>
      <UploadArea onSuccess={() => navigate('/dashboard')} />
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-grow pt-8">
          <Routes>
            <Route path="/" element={<UploadScreen />} />
            <Route path="/contracts" element={<ContractManager />} />
            <Route path="/dashboard" element={<HistoricalAudit />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;