import React from 'react';
// This imports the component you just created
import UploadArea from './components/UploadArea'; 

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      
      <div className="w-full max-w-4xl space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
            LedgerFlux Command Center
          </h1>
          <p className="mt-2 text-lg text-slate-600">
            Enterprise Forensic Freight Audit Pipeline
          </p>
        </div>

        {/* This is the ignition switch: rendering your upload component on the screen */}
        <UploadArea />
        
      </div>
    </div>
  );
}

export default App;