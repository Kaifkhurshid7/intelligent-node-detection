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

import React, { useState, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { VIEW_MODES } from "../constants";
import { getNodeColor, copyToClipboard } from "../utils/helpers";

export default function GraphView({ data }) {
  const [expandedNode, setExpandedNode] = useState(null);
  const [viewMode, setViewMode] = useState(VIEW_MODES.GRAPH);
  const [copySuccess, setCopySuccess] = useState(false);
  const graphRef = useRef();

  if (!data) {
    return <p className="no-items">No data to display.</p>;
  }

  const nodes = data.nodes || [];
  const edges = data.edges || [];
  const narrative = data.logical_graph?.narrative || [];
  const metadata = data.graph?.metadata || {};
  const rawGraph = data.raw_graph || {};

  // Prepare force-graph data
  const graphData = {
    nodes: nodes.map((node) => ({
      id: node.id,
      name: node.id,
      val: node.area ? Math.sqrt(node.area) / 5 : 5,
      ...node,
    })),
    links: edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      ...edge,
    })),
  };

  /** Render edge labels on the force-graph canvas. */
  const renderEdgeLabel = (link, ctx) => {
    if (!link.label) return;
    const start = link.source;
    const end = link.target;
    if (typeof start !== "object" || typeof end !== "object") return;

    const midX = start.x + (end.x - start.x) / 2;
    const midY = start.y + (end.y - start.y) / 2;
    const fontSize = 4;

    ctx.save();
    ctx.font = `${fontSize}px Inter, sans-serif`;
    const textWidth = ctx.measureText(link.label).width;
    const pad = fontSize * 0.3;

    ctx.translate(midX, midY);
    ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
    ctx.fillRect(-(textWidth + pad) / 2, -(fontSize + pad) / 2, textWidth + pad, fontSize + pad);
    ctx.strokeStyle = "#d9d9d9";
    ctx.lineWidth = 0.3;
    ctx.strokeRect(-(textWidth + pad) / 2, -(fontSize + pad) / 2, textWidth + pad, fontSize + pad);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#090909";
    ctx.fillText(link.label, 0, 0);
    ctx.restore();
  };

  /** Highlight semantic keywords in narrative text. */
  const highlightText = (text) => {
    const keywords = ["Start", "End", "Decision", "action"];
    let highlighted = text;
    keywords.forEach((word) => {
      const regex = new RegExp(`\\b${word}\\b`, "gi");
      highlighted = highlighted.replace(
        regex,
        `<span class="hl-${word.toLowerCase()}">$&</span>`
      );
    });
    return <span dangerouslySetInnerHTML={{ __html: highlighted }} />;
  };

  const handleCopyNarrative = async () => {
    const success = await copyToClipboard(narrative.join("\n"));
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  const tabs = [
    { id: VIEW_MODES.GRAPH, label: "Graph" },
    { id: VIEW_MODES.STEPS, label: "Narrative" },
    { id: VIEW_MODES.NODES, label: `Nodes (${nodes.length})` },
    { id: VIEW_MODES.EDGES, label: `Edges (${edges.length})` },
    { id: VIEW_MODES.RAW, label: "JSON" },
  ];

  return (
    <div className="graph-view-container">
      {/* Tab Navigation */}
      <nav className="view-controls" aria-label="Result view tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`control-btn ${viewMode === tab.id ? "active" : ""}`}
            onClick={() => setViewMode(tab.id)}
            aria-selected={viewMode === tab.id}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Tab Content */}
      <div className="graph-content">
        {viewMode === VIEW_MODES.GRAPH && (
          <div className="force-graph-wrapper">
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
              linkWidth={1.5}
              linkCanvasObjectMode={() => "after"}
              linkCanvasObject={renderEdgeLabel}
              width={750}
              height={500}
              cooldownTicks={100}
              onEngineStop={() => graphRef.current?.zoomToFit(400)}
              backgroundColor="#efefed"
            />
          </div>
        )}

        {viewMode === VIEW_MODES.STEPS && (
          <div className="steps-section">
            <div className="section-header-flex">
              <h3>Workflow Narrative</h3>
              <button onClick={handleCopyNarrative} className="text-copy-btn">
                {copySuccess ? "✓ Copied" : "Copy"}
              </button>
            </div>
            {narrative.length === 0 ? (
              <p className="no-items">No logic could be interpreted from this diagram.</p>
            ) : (
              <div className="narrative-list">
                {narrative.map((step, idx) => (
                  <div
                    key={idx}
                    className={`narrative-item ${step.includes("↳") ? "indent-branch" : ""}`}
                  >
                    <span className="step-marker">
                      {step.startsWith("Step") ? step.split(":")[0] : "•"}
                    </span>
                    <span className="step-content">
                      {highlightText(
                        step.includes(":") ? step.split(":").slice(1).join(":").trim() : step
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {viewMode === VIEW_MODES.NODES && (
          <div className="nodes-section">
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
                      style={{ borderLeft: `4px solid ${getNodeColor(node)}` }}
                    >
                      <span className="node-type-badge" style={{ backgroundColor: getNodeColor(node) }}>
                        {node.semantic_class || node.type}
                      </span>
                      <span className="node-id">{node.id}</span>
                      <span className="node-label-preview">
                        {node.labels?.join(", ") || "—"}
                      </span>
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
          </div>
        )}

        {viewMode === VIEW_MODES.EDGES && (
          <div className="edges-section">
            <h3>Detected Edges</h3>
            {edges.length === 0 ? (
              <p className="no-items">No edges detected</p>
            ) : (
              <div className="edges-list">
                {edges.map((edge, idx) => (
                  <div key={idx} className="edge-item">
                    <p>
                      <strong>{edge.source}</strong> → <strong>{edge.target}</strong>
                    </p>
                    {edge.label && <p className="edge-label">Label: "{edge.label}"</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {viewMode === VIEW_MODES.RAW && (
          <div className="raw-section">
            <h3>Raw API Response</h3>
            <pre className="json-display">{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Metrics Dashboard */}
      {metadata.node_count != null && (
        <div className="graph-metadata">
          <div className="metadata-header">
            <h4>Pipeline Metrics</h4>
            <span className="accuracy-badge">Processed</span>
          </div>
          <div className="metrics-grid">
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

          {/* Raw vs Logical comparison */}
          {rawGraph.nodes && (
            <div style={{ marginTop: "var(--spacing-16)", fontSize: "13px", color: "var(--color-muted-text)" }}>
              <p style={{ margin: "4px 0" }}>
                Raw contours: <strong style={{ color: "#090909" }}>{rawGraph.nodes}</strong> →
                Logical nodes: <strong style={{ color: "#090909" }}>{metadata.node_count}</strong>
              </p>
              <p style={{ margin: "4px 0" }}>
                Raw segments: <strong style={{ color: "#090909" }}>{rawGraph.edges}</strong> →
                Logical edges: <strong style={{ color: "#090909" }}>{metadata.edge_count}</strong>
              </p>
            </div>
          )}

          {metadata.sanity_violations?.length > 0 && (
            <div className="sanity-check-area">
              <h5 className="warning-title">⚠ Logic Sanity Warnings</h5>
              <ul className="violations-list">
                {metadata.sanity_violations.map((v, i) => (
                  <li key={i}>{v}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
