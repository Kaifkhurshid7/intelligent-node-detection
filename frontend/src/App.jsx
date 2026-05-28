/**
 * App — Root Application Component
 *
 * Minimal, industry-standard layout with clean navigation,
 * responsive grid, and polished content sections.
 */

import { useState } from "react";
import {
  Scan,
  Brain,
  GitBranch,
  FileText,
  Layers,
  Workflow,
  RefreshCcw,
  Github,
} from "lucide-react";
import Upload from "./components/Upload";
import GraphView from "./components/GraphView";
import "./App.css";

function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [resetCounter, setResetCounter] = useState(0);

  const handleUploadSuccess = (data) => {
    setAnalysisResult(data);
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setResetCounter((prev) => prev + 1);
  };

  return (
    <div className="app-shell">
      {/* Navigation — minimal, Stripe/Linear style */}
      <header className="main-nav">
        <div className="nav-content">
          <a href="/" className="nav-brand">
            <span className="nav-logo">⬡</span>
            <span className="nav-title">NodeDetect</span>
          </a>
          <nav className="nav-links">
            <a href="#features" className="nav-link">How it works</a>
            <a href="#pipeline" className="nav-link">Pipeline</a>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="nav-link nav-link-icon"
              aria-label="GitHub"
            >
              <Github size={18} />
            </a>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="hero-section">
        <h1 className="hero-title">Intelligent Node Detection</h1>
        <p className="hero-subtitle">
          Transform any diagram into a structured directed graph with semantic
          classification and workflow narrative generation.
        </p>
      </section>

      {/* Main Workspace */}
      <main className="workspace">
        <div className="grid-layout">
          {/* Left: Upload Panel */}
          <aside className="tool-panel">
            <div className="panel-header">
              <h3>Upload Diagram</h3>
              <p>Flowchart, architecture diagram, or hand-drawn sketch</p>
            </div>
            <Upload key={resetCounter} onUploadSuccess={handleUploadSuccess} />
          </aside>

          {/* Right: Results Panel */}
          <section className="viewport-panel">
            {analysisResult ? (
              <div className="result-container">
                <div className="viewport-header">
                  <h3>Analysis Results</h3>
                  <button onClick={handleReset} className="ghost-btn">
                    <RefreshCcw size={14} aria-hidden="true" /> New
                  </button>
                </div>
                <GraphView data={analysisResult} />
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">⬡</div>
                <h3>Ready for Analysis</h3>
                <p>Upload a diagram to extract its graph structure</p>
              </div>
            )}
          </section>
        </div>

        {/* Features Section */}
        <section className="features-section" id="features">
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
        <section className="pipeline-section" id="pipeline">
          <h2>Processing Pipeline</h2>
          <div className="pipeline-steps">
            {[
              { title: "Preprocessing", desc: "Resize → Grayscale → Gaussian blur → Adaptive threshold → Morphological closing" },
              { title: "Node Detection", desc: "Find contours, classify shapes by circularity and vertex count" },
              { title: "Text Extraction", desc: "OCR with 2x upscaling and Otsu binarization for small diagram labels" },
              { title: "Merging & Grouping", desc: "Proximity-based clustering consolidates fragmented contours into logical nodes" },
              { title: "Classification", desc: "Shape + text + NLP assigns semantic meaning (start, process, decision, end)" },
              { title: "Edge Mapping", desc: "Hough lines clustered and mapped to nearest node boundaries" },
              { title: "Graph Construction", desc: "NetworkX DiGraph with sanity validation and BFS narrative generation" },
            ].map((step, idx) => (
              <div className="pipeline-step" key={idx}>
                <span className="pipeline-step-number">{idx + 1}</span>
                <div className="pipeline-step-content">
                  <h4>{step.title}</h4>
                  <p>{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Tech Stack */}
        <div className="tech-badges">
          {["FastAPI", "OpenCV", "Tesseract OCR", "NetworkX", "spaCy", "React 18", "Vite", "Docker"].map((t) => (
            <span className="tech-badge" key={t}>{t}</span>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="main-footer">
        <p>© {new Date().getFullYear()} Intelligent Node Detection · Built by Kaif</p>
      </footer>
    </div>
  );
}

export default App;
