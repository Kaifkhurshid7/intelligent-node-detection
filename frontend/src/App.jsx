import React, { useEffect, useState } from "react";
import {
  Activity,
  ShieldCheck,
  ServerCrash,
  RefreshCcw,
  Layout,
  FileSearch,
  AlertCircle
} from "lucide-react"; // Professional Icon Set
import Upload from "./components/Upload";
import GraphView from "./components/GraphView";
import api from "./services/api";
import "./App.css";

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [apiStatus, setApiStatus] = useState("checking");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const healthy = await api.healthCheck();
        setApiStatus(healthy ? "connected" : "disconnected");
      } catch (err) {
        setApiStatus("disconnected");
      }
    };
    checkApiHealth();
  }, []);

  const handleUploadSuccess = (data) => {
    setAnalysisResult(data);
    setErrorMessage("");
  };

  const handleClearResults = () => {
    setAnalysisResult(null);
  };

  return (
    <div className="app-shell">
      {/* --- Header --- */}
      <header className="main-nav">
        <div className="nav-content">
          <div className="brand">
            <div className="brand-logo-container">
              <Activity size={24} className="logo-icon" />
            </div>
            <div>
              <h1>NodeDetection</h1>
              <p className="brand-tagline">Structured Graph Extraction</p>
            </div>
          </div>

          <div className={`status-pill ${apiStatus}`}>
            <span className="status-indicator">
              {apiStatus === "connected" && <ShieldCheck size={14} />}
              {apiStatus === "checking" && <RefreshCcw size={14} className="spin" />}
              {apiStatus === "disconnected" && <ServerCrash size={14} />}
            </span>
            <span className="status-text">
              {apiStatus === "connected" && "System Online"}
              {apiStatus === "checking" && "Connecting..."}
              {apiStatus === "disconnected" && "Offline"}
            </span>
          </div>
        </div>
      </header>

      {/* --- Main Workspace --- */}
      <main className="workspace">
        {errorMessage && (
          <div className="critical-alert">
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="grid-layout">
          {/* Left: Action Area */}
          <aside className="tool-panel">
            <div className="panel-header">
              <div className="header-with-icon">
                <FileSearch size={20} />
                <h3>Input Diagram</h3>
              </div>
              <p>Upload your image for AI processing</p>
            </div>
            <Upload onUploadSuccess={handleUploadSuccess} />
          </aside>

          {/* Right: Visualization Area */}
          <section className="viewport-panel">
            {analysisResult ? (
              <div className="result-container">
                <div className="viewport-header">
                  <div className="header-with-icon">
                    <Layout size={20} />
                    <h3>Graph Visualization</h3>
                  </div>
                  <button onClick={handleClearResults} className="ghost-btn">
                    <RefreshCcw size={14} />
                    Reset
                  </button>
                </div>
                <div className="canvas-wrapper">
                  <GraphView data={analysisResult} />
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon-container">
                  <Layout size={48} strokeWidth={1} />
                </div>
                <h3>No Data Processed</h3>
                <p>Upload a file on the left to begin analysis</p>
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="main-footer">
        <p>© {new Date().getFullYear()} NodeDetection System • <span className="version">DONE BY KAIF</span></p>
      </footer>
    </div>
  );
}

export default App;