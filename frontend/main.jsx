import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

// This is the ignition switch that injects your React app into the HTML file
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);