/**
 * App - Root Application Component
 *
 * Provides the main layout shell with:
 *   - Header with API status indicator
 *   - Two-column grid: upload panel + visualization panel
 *   - Footer
 */

import React, { useState } from "react";
import {
  Activity,
  ShieldCheck,
  ServerCrash,
  RefreshCcw,
  Layout,
  FileSearch,
  AlertCircle,
} from "lucide-react";
import Upload from "./components/Upload";
import GraphView from "./components/GraphView";
import { useApiStatus } from "./hooks/useApiStatus";
import { API_STATUS } from "./constants";
import "./App.css";

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [resetCounter, setResetCounter] = useState(0);
  const apiStatus = useApiStatus();

  const handleUploadSuccess = (data) => {
    setAnalysisResult(data);
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setResetCounter((prev) => prev + 1);
  };

  return (
    <div className="app-shell">
      {/* Header */}
      <header className="main-nav">
        <div className="nav-content">
          <div className="brand">
            <Activity size={24} aria-hidden="true" />
            <div>
              <h1>NodeDetection</h1>
              <p className="brand-tagline">Diagram → Structured Graph</p>
            </div>
          </div>

          <div className={`status-pill ${apiStatus}`} aria-live="polite">
            <span className="status-indicator">
              {apiStatus === API_STATUS.CONNECTED && <ShieldCheck size={14} />}
              {apiStatus === API_STATUS.CHECKING && <RefreshCcw size={14} className="spin" />}
              {apiStatus === API_STATUS.DISCONNECTED && <ServerCrash size={14} />}
            </span>
            <span className="status-text">
              {apiStatus === API_STATUS.CONNECTED && "Online"}
              {apiStatus === API_STATUS.CHECKING && "Connecting..."}
              {apiStatus === API_STATUS.DISCONNECTED && "Offline"}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="workspace">
        <div className="grid-layout">
          {/* Left Panel: Upload */}
          <aside className="tool-panel">
            <div className="panel-header">
              <div className="header-with-icon">
                <FileSearch size={20} aria-hidden="true" />
                <h3>Input Diagram</h3>
              </div>
              <p>Upload a flowchart or diagram image for analysis</p>
            </div>
            <Upload key={resetCounter} onUploadSuccess={handleUploadSuccess} />
          </aside>

          {/* Right Panel: Visualization */}
          <section className="viewport-panel">
            {analysisResult ? (
              <div className="result-container">
                <div className="viewport-header">
                  <div className="header-with-icon">
                    <Layout size={20} aria-hidden="true" />
                    <h3>Analysis Results</h3>
                  </div>
                  <button onClick={handleReset} className="ghost-btn">
                    <RefreshCcw size={14} aria-hidden="true" /> Reset
                  </button>
                </div>
                <GraphView data={analysisResult} />
              </div>
            ) : (
              <div className="empty-state">
                <Layout size={48} strokeWidth={1} aria-hidden="true" />
                <h3>No Data Processed</h3>
                <p>Upload a diagram to begin analysis</p>
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="main-footer">
        <p>
          © {new Date().getFullYear()} Intelligent Node Detection •{" "}
          <span className="version">v1.0</span>
        </p>
      </footer>
    </div>
  );
}

export default App;
