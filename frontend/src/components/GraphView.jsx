/**
 * GraphView Component
 *
 * Multi-tab visualization of analysis results with:
 *   - Interactive force-directed graph
 *   - Workflow narrative with keyword highlighting
 *   - Expandable node inspector
 *   - Edge connection list
 *   - Raw JSON data viewer
 *   - Pipeline metrics dashboard
 */

import { useState, useRef, useEffect, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { VIEW_MODES } from "../constants";
import { getNodeColor, copyToClipboard } from "../utils/helpers";

import "../styles/tokens.css";
import "../styles/graphview.css";

/**
 * GraphView
 *
 * Responsive, accessible visualization panel for analysis results.
 * - Mobile-first layout that adapts to larger screens using CSS Grid.
 * - Canvas auto-resizes to its container via ResizeObserver for correct rendering.
 * - Keyboard-accessible tab navigation and focusable interactive elements.
 *
 * Props:
 *  - data: API response containing nodes, edges, narrative, metadata, and timings.
 */
export default function GraphView({ data }) {
  // ----------------------------
  // Local UI state
  // ----------------------------
  const [expandedNode, setExpandedNode] = useState(null);
  const [viewMode, setViewMode] = useState(VIEW_MODES.GRAPH);
  const [copySuccess, setCopySuccess] = useState(false);
  const [graphHeight, setGraphHeight] = useState(460);

  // Refs to DOM and graph instance
  const graphRef = useRef(null);
  const containerRef = useRef(null);

  // Early return for no-data state (keeps markup minimal)
  if (!data) return <p className="no-items">No data to display.</p>;

  // ----------------------------
  // Normalize API payloads
  // ----------------------------
  const nodes = data.nodes || [];
  const edges = data.edges || [];
  const narrative = data.logical_graph?.narrative || [];
  const metadata = data.graph?.metadata || {};
  const rawGraph = data.raw_graph || {};
  const timings = data.timings || null;

  // Prepare force-graph data structure (keeps original payload shape intact)
  const graphData = {
    nodes: nodes.map((node) => ({ id: node.id, name: node.id, val: node.area ? Math.sqrt(node.area) / 5 : 5, ...node })),
    links: edges.map((edge) => ({ source: edge.source, target: edge.target, ...edge })),
  };

  // ----------------------------
  // Canvas rendering helpers
  // ----------------------------
  /**
   * Render small labels for links on the canvas. Kept compact for performance.
   */
  const renderEdgeLabel = useCallback((link, ctx) => {
    if (!link.label) return;
    const start = link.source;
    const end = link.target;
    if (typeof start !== "object" || typeof end !== "object") return;

    const midX = start.x + (end.x - start.x) / 2;
    const midY = start.y + (end.y - start.y) / 2;
    const fontSize = 9; // readable across devices

    ctx.save();
    ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
    const textWidth = ctx.measureText(link.label).width;
    const pad = fontSize * 0.4;

    ctx.translate(midX, midY);
    ctx.fillStyle = "rgba(255,255,255,0.95)";
    ctx.fillRect(-(textWidth + pad) / 2, -(fontSize + pad) / 2, textWidth + pad, fontSize + pad);
    ctx.strokeStyle = "rgba(0,0,0,0.08)";
    ctx.lineWidth = 0.5;
    ctx.strokeRect(-(textWidth + pad) / 2, -(fontSize + pad) / 2, textWidth + pad, fontSize + pad);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#111827";
    ctx.fillText(link.label, 0, 0);
    ctx.restore();
  }, []);

  // ----------------------------
  // Responsive canvas sizing
  // ----------------------------
  useEffect(() => {
    if (!containerRef.current) return;

    // ResizeObserver keeps canvas size in-sync with container
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const h = Math.max(260, Math.round(entry.contentRect.height));
        setGraphHeight(h);
      }
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Ensure the graph zooms to fit when simulation settles
  const onEngineStop = () => {
    try { graphRef.current?.zoomToFit(300); } catch (e) { /* no-op */ }
  };

  // ----------------------------
  // Narrative highlighting
  // ----------------------------
  const KEYWORDS = ["Start", "End", "Decision", "action"];

 
  const highlightText = (text) => {
    if (!text) return text;
    // Split so we can wrap matched tokens
    const parts = text.split(new RegExp(`(${KEYWORDS.join("|")})`, "gi"));
    return parts.map((part, i) => {
      const match = KEYWORDS.find((k) => k.toLowerCase() === part.toLowerCase());
      if (match) return <span key={i} className={`hl-${match.toLowerCase()}`}>{part}</span>;
      return <span key={i}>{part}</span>;
    });
  };

  // ----------------------------
  // Copy narrative helper
  // ----------------------------
  const handleCopyNarrative = async () => {
    const success = await copyToClipboard(narrative.join("\n"));
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  // ----------------------------
  // Tabs (keyboard navigation support)
  // ----------------------------
  const tabs = [
    { id: VIEW_MODES.GRAPH, label: "Graph" },
    { id: VIEW_MODES.STEPS, label: "Narrative" },
    { id: VIEW_MODES.NODES, label: `Nodes (${nodes.length})` },
    { id: VIEW_MODES.EDGES, label: `Edges (${edges.length})` },
    { id: VIEW_MODES.RAW, label: "JSON" },
  ];

  const onTabKeyDown = (e) => {
    const idx = tabs.findIndex((t) => t.id === viewMode);
    if (e.key === "ArrowRight") setViewMode(tabs[(idx + 1) % tabs.length].id);
    if (e.key === "ArrowLeft") setViewMode(tabs[(idx - 1 + tabs.length) % tabs.length].id);
  };

  // ----------------------------
  // Render
  // ----------------------------
  return (
    <div className="graph-view-container container">
      {/* Tab Navigation: semantic tablist for assistive tech */}
      <nav className="view-controls" role="tablist" aria-label="Result view tabs" onKeyDown={onTabKeyDown}>
        {tabs.map((tab, i) => (
          <button
            key={tab.id}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={viewMode === tab.id}
            aria-controls={`panel-${tab.id}`}
            tabIndex={viewMode === tab.id ? 0 : -1}
            className={`control-btn ${viewMode === tab.id ? "active" : ""}`}
            onClick={() => setViewMode(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="graph-content">
        {/* Primary visualization column */}
        <div className="card" ref={containerRef} id={`panel-${VIEW_MODES.GRAPH}`} role="tabpanel" aria-labelledby={`tab-${VIEW_MODES.GRAPH}`}>
          {viewMode === VIEW_MODES.GRAPH && (
            <div className="force-graph-wrapper" aria-hidden={viewMode !== VIEW_MODES.GRAPH}>
              <ForceGraph2D
                ref={graphRef}
                graphData={graphData}
                nodeLabel="label"
                nodeColor={getNodeColor}
                nodeRelSize={6}
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                linkCurvature={0.2}
                linkColor={() => "#090909"}
                linkWidth={1.2}
                linkCanvasObjectMode={() => "after"}
                linkCanvasObject={renderEdgeLabel}
                // size is handled by CSS; set explicit pixel height for canvas
                height={graphHeight}
                cooldownTicks={100}
                onEngineStop={onEngineStop}
                backgroundColor={"var(--color-surface)"}
              />
            </div>
          )}

          {/* Narrative panel */}
          {viewMode === VIEW_MODES.STEPS && (
            <section id={`panel-${VIEW_MODES.STEPS}`} role="tabpanel" aria-labelledby={`tab-${VIEW_MODES.STEPS}`} className="steps-section">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0 }}>Workflow Narrative</h3>
                <button onClick={handleCopyNarrative} className="text-copy-btn">{copySuccess ? "✓ Copied" : "Copy"}</button>
              </div>

              {narrative.length === 0 ? (
                <p className="no-items">No logic could be interpreted from this diagram.</p>
              ) : (
                <div className="narrative-list">
                  {narrative.map((step, idx) => (
                    <div key={idx} className={`narrative-item ${step.includes("↳") ? "indent-branch" : ""}`}>
                      <span className="step-marker">{step.startsWith("Step") ? step.split(":")[0] : "•"}</span>
                      <span className="step-content">{highlightText(step.includes(":") ? step.split(":").slice(1).join(":").trim() : step)}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Nodes, Edges, Raw panels are rendered below; they surface structured data */}
          {viewMode === VIEW_MODES.NODES && (
            <section id={`panel-${VIEW_MODES.NODES}`} role="tabpanel" aria-labelledby={`tab-${VIEW_MODES.NODES}`} className="nodes-section">
              <h3>Detected Nodes</h3>
              {nodes.length === 0 ? (
                <p className="no-items">No nodes detected</p>
              ) : (
                <div className="nodes-list">
                  {nodes.map((node, idx) => (
                    <div key={idx} className={`node-item ${expandedNode === idx ? "expanded" : ""}`}>
                      <div
                        className="node-header"
                        onClick={() => setExpandedNode(expandedNode === idx ? null : idx)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setExpandedNode(expandedNode === idx ? null : idx); }}
                        style={{ borderLeft: `4px solid ${getNodeColor(node)}` }}
                        aria-expanded={expandedNode === idx}
                      >
                        <span className="node-type-badge" style={{ backgroundColor: getNodeColor(node) }}>{node.semantic_class || node.type}</span>
                        <span className="node-id">{node.id}</span>
                        <span className="node-label-preview">{node.labels?.join(", ") || "—"}</span>
                        <span className="expand-icon">{expandedNode === idx ? "▼" : "▶"}</span>
                      </div>
                      {expandedNode === idx && (
                        <div className="node-details">
                          <p><strong>Shape:</strong> {node.type}</p>
                          <p><strong>Semantic Class:</strong> {node.semantic_class || "Unclassified"}</p>
                          <p><strong>Labels:</strong> {node.labels?.join(", ") || "None"}</p>
                          <p><strong>Confidence:</strong> {(node.confidence * 100).toFixed(1)}%</p>
                          <p><strong>Position:</strong> ({node.center?.x}, {node.center?.y})</p>
                          <p><strong>Bounding Box:</strong> {node.bbox?.w}×{node.bbox?.h}px</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {viewMode === VIEW_MODES.EDGES && (
            <section id={`panel-${VIEW_MODES.EDGES}`} role="tabpanel" aria-labelledby={`tab-${VIEW_MODES.EDGES}`} className="edges-section">
              <h3>Detected Edges</h3>
              {edges.length === 0 ? (
                <p className="no-items">No edges detected</p>
              ) : (
                <div className="edges-list">
                  {edges.map((edge, idx) => (
                    <div key={idx} className="edge-item">
                      <p><strong>{edge.source}</strong> → <strong>{edge.target}</strong></p>
                      {edge.label && <p className="edge-label">Label: "{edge.label}"</p>}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {viewMode === VIEW_MODES.RAW && (
            <section id={`panel-${VIEW_MODES.RAW}`} role="tabpanel" aria-labelledby={`tab-${VIEW_MODES.RAW}`} className="raw-section">
              <h3>Raw API Response</h3>
              <pre className="json-display" style={{ overflowX: 'auto' }}>{JSON.stringify(data, null, 2)}</pre>
            </section>
          )}
        </div>

        {/* Sidebar: metrics and diagnostics */}
        <aside className="graph-metadata">
          {metadata.node_count != null && (
            <div>
              <div className="metadata-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ margin: 0 }}>Pipeline Metrics</h4>
                <span className="accuracy-badge">Processed</span>
              </div>

              <div className="metrics-grid" style={{ marginTop: 'var(--spacing-12)' }}>
                <div className="metric-card">
                  <span className="metric-label">Logical Nodes</span>
                  <span className="metric-value">{metadata.node_count}</span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Logical Edges</span>
                  <span className="metric-value">{metadata.edge_count}</span>
                </div>
                <div className="metric-card highlight">
                  <span className="metric-label">Noise Reduction</span>
                  <span className="metric-value">{metadata.node_reduction_pct}%</span>
                </div>
              </div>

              {rawGraph.nodes && (
                <div style={{ marginTop: 'var(--spacing-16)', fontSize: '13px', color: 'var(--color-muted-text)' }}>
                  <p style={{ margin: '4px 0' }}>
                    Raw contours: <strong style={{ color: '#090909' }}>{rawGraph.nodes}</strong> → Logical nodes: <strong style={{ color: '#090909' }}>{metadata.node_count}</strong>
                  </p>
                  <p style={{ margin: '4px 0' }}>
                    Raw segments: <strong style={{ color: '#090909' }}>{rawGraph.edges}</strong> → Logical edges: <strong style={{ color: '#090909' }}>{metadata.edge_count}</strong>
                  </p>
                </div>
              )}

              {metadata.sanity_violations?.length > 0 && (
                <div className="sanity-check-area" style={{ marginTop: 'var(--spacing-12)' }}>
                  <h5 className="warning-title">⚠ Logic Sanity Warnings</h5>
                  <ul className="violations-list">
                    {metadata.sanity_violations.map((v, i) => <li key={i}>{v}</li>)}
                  </ul>
                </div>
              )}

              {timings && (
                <div className="timings-section" style={{ marginTop: 'var(--spacing-12)' }}>
                  <h5 className="timings-title">⚡ Pipeline Performance</h5>
                  <div className="timings-grid">
                    <div className="timing-item"><span className="timing-label">Preprocessing</span><span className="timing-value">{timings.preprocessing_ms}ms</span></div>
                    <div className="timing-item"><span className="timing-label">Detection</span><span className="timing-value">{timings.detection_ms}ms</span></div>
                    <div className="timing-item"><span className="timing-label">OCR</span><span className="timing-value">{timings.ocr_ms}ms</span></div>
                    <div className="timing-item"><span className="timing-label">Merging</span><span className="timing-value">{timings.merging_ms}ms</span></div>
                    <div className="timing-item"><span className="timing-label">Classification</span><span className="timing-value">{timings.classification_ms}ms</span></div>
                    <div className="timing-item"><span className="timing-label">Edge Detection</span><span className="timing-value">{timings.edge_detection_ms}ms</span></div>
                    <div className="timing-item"><span className="timing-label">Graph Build</span><span className="timing-value">{timings.graph_construction_ms}ms</span></div>
                    <div className="timing-item timing-total"><span className="timing-label">Total</span><span className="timing-value">{timings.total_ms}ms</span></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
