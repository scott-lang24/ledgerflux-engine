import React, { useState } from 'react';

const UploadArea = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.zip')) {
      setFile(selectedFile);
      setMessage('');
    } else {
      setFile(null);
      setMessage('Error: Please upload a .zip file containing your PDFs.');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setMessage('Uploading and extracting batch...');

    const formData = new FormData();
    formData.append('file', file);
    // Hardcoding client_id=1 for now, we will connect this to real auth later
    formData.append('client_id', 1); 

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload/batch', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessage('Success! ' + data.message);
        // Next step: Redirect user to the /historical-audit dashboard here
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
    <div className="max-w-2xl mx-auto p-8 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg text-center mt-10">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">LedgerFlux Forensic Audit Engine</h2>
      <p className="text-gray-600 mb-8">Upload a ZIP file containing historical carrier invoices (PDFs).</p>
      
      <input 
        type="file" 
        accept=".zip" 
        onChange={handleFileChange} 
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-6"
      />
      
      <button 
        onClick={handleUpload} 
        disabled={!file || uploading}
        className={`px-6 py-3 rounded-md text-white font-bold transition-all ${!file || uploading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-lg'}`}
      >
        {uploading ? 'Processing Engine...' : 'Run Autonomous Audit'}
      </button>

      {message && (
        <div className={`mt-6 p-4 rounded-md ${message.includes('Success') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default UploadArea;