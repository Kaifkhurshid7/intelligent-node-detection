/**
 * Upload Component
 *
 * Provides drag-and-drop and click-to-browse file upload with
 * image preview, loading state, and error feedback.
 */

import React, { useState } from "react";
import { Upload as UploadIcon } from "lucide-react";
import api from "../services/api";

export default function Upload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  /** Process a selected file: validate and generate preview. */
  const processFile = (selectedFile) => {
    setFile(selectedFile);
    setError("");
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(selectedFile);
  };

  /** Handle file input change event. */
  const handleFileSelect = (e) => {
    const selected = e.target.files[0];
    if (selected) processFile(selected);
  };

  /** Submit the file to the analysis API. */
  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await api.analyzeDiagram(file);
      if (result.success) {
        onUploadSuccess(result.data);
      } else {
        setError(result.message || "Analysis failed");
      }
    } catch (err) {
      setError(err.message || "An error occurred during analysis");
    } finally {
      setLoading(false);
    }
  };

  /** Clear the current file selection. */
  const clearSelection = () => {
    setFile(null);
    setPreview("");
    setError("");
  };

  // Drag-and-drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add("drag-active");
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove("drag-active");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove("drag-active");
    const dropped = e.dataTransfer.files;
    if (dropped.length > 0) processFile(dropped[0]);
  };

  return (
    <div className="upload-wrapper">
      <div
        className={`upload-zone ${preview ? "has-preview" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {preview ? (
          <div className="preview-stage">
            <img src={preview} alt="Diagram preview" className="image-snapshot" />
            <div className="file-info-overlay">
              <span className="filename-tag">{file?.name}</span>
              <button onClick={clearSelection} className="change-file-btn">
                Remove
              </button>
            </div>
          </div>
        ) : (
          <div className="upload-prompt">
            <div className="icon-circle">
              <UploadIcon size={24} />
            </div>
            <p className="primary-text">Drag & drop diagram</p>
            <p className="secondary-text">PNG, JPG, or BMP up to 10MB</p>
            <label className="browse-trigger">
              Browse Files
              <input
                type="file"
                onChange={handleFileSelect}
                accept="image/*"
                className="hidden-input"
              />
            </label>
          </div>
        )}
      </div>

      {error && <div className="error-toast" role="alert">{error}</div>}

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className="submit-btn"
        aria-busy={loading}
      >
        {loading ? (
          <>
            <span className="spinner" aria-hidden="true"></span> Analyzing...
          </>
        ) : (
          "Analyze Diagram"
        )}
      </button>
    </div>
  );
}
