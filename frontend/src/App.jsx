import React, { useEffect, useState } from "react";
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
            <span className="brand-logo"></span>
            <div>
              <h1>NodeDetection</h1>
              <p className="brand-tagline">Structured Graph Extraction</p>
            </div>
          </div>

          <div className={`status-pill ${apiStatus}`}>
            <span className="status-dot"></span>
            {apiStatus === "connected" && "System Ready"}
            {apiStatus === "checking" && "Connecting..."}
            {apiStatus === "disconnected" && "Offline"}
          </div>
        </div>
      </header>

      {/* --- Main Workspace --- */}
      <main className="workspace">
        {errorMessage && (
          <div className="critical-alert">{errorMessage}</div>
        )}

        <div className="grid-layout">
          {/* Left: Action Area */}
          <aside className="tool-panel">
            <div className="panel-header">
              <h3>Input Diagram</h3>
              <p>Upload your image for AI processing</p>
            </div>
            <Upload onUploadSuccess={handleUploadSuccess} />
          </aside>

          {/* Right: Visualization Area */}
          <section className="viewport-panel">
            {analysisResult ? (
              <div className="result-container">
                <div className="viewport-header">
                  <h3>Graph Visualization</h3>
                  <button onClick={handleClearResults} className="ghost-btn">
                    Reset
                  </button>
                </div>
                <div className="canvas-wrapper">
                  <GraphView data={analysisResult} />
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">📊</div>
                <h3>No Data Processed</h3>
                <p>Upload a file on the left to begin analysis</p>
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="main-footer">
        <p>© {new Date().getFullYear()} NodeDetection System • v1.0.4</p>
      </footer>
    </div>
  );
}

export default App;