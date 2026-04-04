import React, { useState } from 'react';

const UploadArea = ({ onSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
<<<<<<< HEAD:frontend/src/components/UploadArea.jsx
  const [isDragging, setIsDragging] = useState(false);
=======
  const [isDragging, setIsDragging] = useState(false); // New state for drag visuals
>>>>>>> bd135f07aac58fdd667722cb3988662a628e8915:frontend/components/UploadArea.jsx

  const validateAndSetFile = (selectedFile) => {
    if (selectedFile && selectedFile.name.endsWith('.zip')) {
      setFile(selectedFile);
      setMessage('');
    } else {
      setFile(null);
      setMessage('Error: Please upload a .zip file containing your PDFs.');
    }
  };

  const handleFileChange = (e) => {
    validateAndSetFile(e.target.files[0]);
  };

<<<<<<< HEAD:frontend/src/components/UploadArea.jsx
=======
  // --- NEW DRAG AND DROP HANDLERS ---
>>>>>>> bd135f07aac58fdd667722cb3988662a628e8915:frontend/components/UploadArea.jsx
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };
<<<<<<< HEAD:frontend/src/components/UploadArea.jsx
=======
  // ----------------------------------
>>>>>>> bd135f07aac58fdd667722cb3988662a628e8915:frontend/components/UploadArea.jsx

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setMessage('Uploading and extracting batch...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('client_id', 1); 

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload/batch', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessage('Success! ' + data.message);
        setTimeout(() => {
          if (onSuccess) onSuccess();
        }, 1500); 
      } else {
        setMessage('Upload failed: ' + data.detail);
      }
    } catch (error) {
      setMessage('Server connection error. Is your Python backend running?');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`max-w-2xl mx-auto p-8 border-2 border-dashed rounded-lg text-center mt-10 transition-colors ${
        isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'
      }`}
    >
      <h2 className="text-2xl font-bold text-gray-800 mb-4">LedgerFlux Forensic Audit Engine</h2>
      <p className="text-gray-600 mb-8">Drag and drop a ZIP file here, or click to select.</p>
      
      <input 
        type="file" 
        accept=".zip" 
        onChange={handleFileChange} 
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-6 cursor-pointer"
      />
      
<<<<<<< HEAD:frontend/src/components/UploadArea.jsx
=======
      {/* Visual indicator of what file is loaded */}
>>>>>>> bd135f07aac58fdd667722cb3988662a628e8915:frontend/components/UploadArea.jsx
      {file && (
        <div className="mb-4 text-sm font-medium text-slate-700 bg-white p-2 rounded border shadow-sm inline-block">
          📎 {file.name} ready for audit
        </div>
      )}
      
      <div className="block mt-2">
        <button 
          onClick={handleUpload} 
          disabled={!file || uploading}
          className={`px-6 py-3 rounded-md text-white font-bold transition-all ${!file || uploading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-lg'}`}
        >
          {uploading ? 'Processing Engine...' : 'Run Autonomous Audit'}
        </button>
      </div>

      {message && (
        <div className={`mt-6 p-4 rounded-md ${message.includes('Success') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default UploadArea;
