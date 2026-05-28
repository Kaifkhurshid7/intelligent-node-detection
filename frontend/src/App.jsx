/**
 * App — Root Application Component
 *
 * Sana-inspired light theme with polished glass aesthetic.
 * High-contrast typography, clean white canvas, minimal elevation.
 */

import React, { useState } from "react";
import {
  Activity,
  ShieldCheck,
  ServerCrash,
  RefreshCcw,
  Layout,
  FileSearch,
  Scan,
  Brain,
  GitBranch,
  FileText,
  Layers,
  Workflow,
  Zap,
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
      {/* Navigation */}
      <header className="main-nav">
        <div className="nav-content">
          <div className="brand">
            <Activity size={22} aria-hidden="true" />
            <div>
              <h1>NodeDetect</h1>
              <p className="brand-tagline">Diagram Intelligence</p>
            </div>
          </div>

          <div className={`status-pill ${apiStatus}`} aria-live="polite">
            <span className="status-indicator">
              {apiStatus === API_STATUS.CONNECTED && <ShieldCheck size={14} />}
              {apiStatus === API_STATUS.CHECKING && <RefreshCcw size={14} className="spin" />}
              {apiStatus === API_STATUS.DISCONNECTED && <ServerCrash size={14} />}
            </span>
            <span className="status-text">
              {apiStatus === API_STATUS.CONNECTED && "System Online"}
              {apiStatus === API_STATUS.CHECKING && "Connecting..."}
              {apiStatus === API_STATUS.DISCONNECTED && "Offline"}
            </span>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="hero-section">
        <h2 className="hero-title">Intelligent Node Detection</h2>
        <p className="hero-subtitle">
          Transform any diagram into a structured graph with semantic
          classification, edge detection, and workflow narrative generation.
        </p>
      </section>

      {/* Main Workspace */}
      <main className="workspace">
        <div className="grid-layout">
          {/* Left: Upload Panel */}
          <aside className="tool-panel">
            <div className="panel-header">
              <div className="header-with-icon">
                <FileSearch size={18} aria-hidden="true" />
                <h3>Upload Diagram</h3>
              </div>
              <p>Drop a flowchart, architecture diagram, or hand-drawn sketch</p>
            </div>
            <Upload key={resetCounter} onUploadSuccess={handleUploadSuccess} />
          </aside>

          {/* Right: Results Panel */}
          <section className="viewport-panel">
            {analysisResult ? (
              <div className="result-container">
                <div className="viewport-header">
                  <div className="header-with-icon">
                    <Layout size={18} aria-hidden="true" />
                    <h3>Analysis Results</h3>
                  </div>
                  <button onClick={handleReset} className="ghost-btn">
                    <RefreshCcw size={14} aria-hidden="true" /> New Analysis
                  </button>
                </div>
                <GraphView data={analysisResult} />
              </div>
            ) : (
              <div className="empty-state">
                <Layout size={44} strokeWidth={1} aria-hidden="true" />
                <h3>Ready for Analysis</h3>
                <p>Upload a diagram image to extract its graph structure</p>
              </div>
            )}
          </section>
        </div>

        {/* Features Section */}
        <section className="features-section">
          <div className="features-header">
            <h2>How It Works</h2>
            <p>A 7-stage computer vision pipeline powered by OpenCV and NetworkX</p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-card-icon"><Scan size={20} /></div>
              <h4>Shape Detection</h4>
              <p>Contour analysis identifies rectangles, circles, diamonds, and polygons</p>
            </div>
            <div className="feature-card">
              <div className="feature-card-icon"><FileText size={20} /></div>
              <h4>OCR Extraction</h4>
              <p>Tesseract reads text labels and assigns them to their containing shapes</p>
            </div>
            <div className="feature-card">
              <div className="feature-card-icon"><Brain size={20} /></div>
              <h4>Semantic Classification</h4>
              <p>NLP + shape heuristics classify nodes as start, end, process, or decision</p>
            </div>
            <div className="feature-card">
              <div className="feature-card-icon"><GitBranch size={20} /></div>
              <h4>Edge Detection</h4>
              <p>Hough transform finds arrows and maps connections between nodes</p>
            </div>
            <div className="feature-card">
              <div className="feature-card-icon"><Layers size={20} /></div>
              <h4>Noise Reduction</h4>
              <p>Proximity merging and confidence filtering eliminate false detections</p>
            </div>
            <div className="feature-card">
              <div className="feature-card-icon"><Workflow size={20} /></div>
              <h4>Narrative Generation</h4>
              <p>BFS traversal produces human-readable step-by-step workflow descriptions</p>
            </div>
          </div>
        </section>

        {/* Pipeline Steps */}
        <section className="pipeline-section">
          <h2>Processing Pipeline</h2>
          <div className="pipeline-steps">
            <div className="pipeline-step">
              <span className="pipeline-step-number">1</span>
              <div className="pipeline-step-content">
                <h4>Preprocessing</h4>
                <p>Resize → Grayscale → Gaussian blur → Adaptive threshold → Morphological closing</p>
              </div>
            </div>
            <div className="pipeline-step">
              <span className="pipeline-step-number">2</span>
              <div className="pipeline-step-content">
                <h4>Node Detection</h4>
                <p>Find contours, classify shapes by circularity and vertex count</p>
              </div>
            </div>
            <div className="pipeline-step">
              <span className="pipeline-step-number">3</span>
              <div className="pipeline-step-content">
                <h4>Text Extraction</h4>
                <p>OCR with 2x upscaling and Otsu binarization for small diagram labels</p>
              </div>
            </div>
            <div className="pipeline-step">
              <span className="pipeline-step-number">4</span>
              <div className="pipeline-step-content">
                <h4>Merging & Grouping</h4>
                <p>Proximity-based clustering consolidates fragmented contours into logical nodes</p>
              </div>
            </div>
            <div className="pipeline-step">
              <span className="pipeline-step-number">5</span>
              <div className="pipeline-step-content">
                <h4>Classification</h4>
                <p>Shape + text + NLP assigns semantic meaning (start, process, decision, end)</p>
              </div>
            </div>
            <div className="pipeline-step">
              <span className="pipeline-step-number">6</span>
              <div className="pipeline-step-content">
                <h4>Edge Mapping</h4>
                <p>Hough lines clustered and mapped to nearest node boundaries</p>
              </div>
            </div>
            <div className="pipeline-step">
              <span className="pipeline-step-number">7</span>
              <div className="pipeline-step-content">
                <h4>Graph Construction</h4>
                <p>NetworkX DiGraph with sanity validation and BFS narrative generation</p>
              </div>
            </div>
          </div>
        </section>

        {/* Tech Stack */}
        <div className="tech-badges">
          <span className="tech-badge">FastAPI</span>
          <span className="tech-badge">OpenCV</span>
          <span className="tech-badge">Tesseract OCR</span>
          <span className="tech-badge">NetworkX</span>
          <span className="tech-badge">spaCy</span>
          <span className="tech-badge">React 18</span>
          <span className="tech-badge">Vite</span>
          <span className="tech-badge">Docker</span>
        </div>
      </main>

      {/* Footer */}
      <footer className="main-footer">
        <p>
          © {new Date().getFullYear()} Intelligent Node Detection •{" "}
          <span className="version">v1.0</span> • Built by Kaif
        </p>
      </footer>
    </div>
  );
}

export default App;
