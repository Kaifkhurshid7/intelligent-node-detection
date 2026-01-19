import React, { useState } from 'react';
import '../index.css';
import api from '../services/api';

/**
 * Upload component with a modern, professional dark-theme aesthetic
 */
export default function Upload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState('');

  const handleFileSelect = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      processFile(selectedFile);
    }
  };

  const processFile = (selectedFile) => {
    setFile(selectedFile);
    setError('');
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await api.analyzeDiagram(file);
      if (result.success) {
        onUploadSuccess(result.data);
        // Removed setFile(null) and setPreview('') to keep image visible
      } else {
        setError(result.message || 'Upload failed');
      }
    } catch (err) {
      setError(err.message || 'An error occurred during analysis');
    } finally {
      setLoading(false);
    }
  };

  const clearSelection = () => {
    setFile(null);
    setPreview('');
    setError('');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-active');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-active');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-active');
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      processFile(droppedFiles[0]);
    }
  };

  return (
    <div className="upload-wrapper">
      <div
        className={`upload-zone ${preview ? 'has-preview' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {preview ? (
          <div className="preview-stage">
            <img src={preview} alt="Preview" className="image-snapshot" />
            <div className="file-info-overlay">
              <span className="filename-tag">{file?.name}</span>
              <button onClick={clearSelection} className="change-file-btn">Remove</button>
            </div>
          </div>
        ) : (
          <div className="upload-prompt">
            <div className="icon-circle">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p className="primary-text">Drag & drop diagram</p>
            <p className="secondary-text">PNG, JPG, or SVG up to 10MB</p>
            <label className="browse-trigger">
              Browse Files
              <input type="file" onChange={handleFileSelect} accept="image/*" className="hidden-input" />
            </label>
          </div>
        )}
      </div>

      {error && <div className="error-toast">{error}</div>}

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className={`submit-btn ${loading ? 'is-loading' : ''}`}
      >
        {loading ? (
          <><span className="spinner"></span> Analyzing...</>
        ) : (
          'Analyze Diagram'
        )}
      </button>
    </div>
  );
}