import React, { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

/**
 * GraphView component for displaying detected nodes and graph structure
 */
export default function GraphView({ data }) {
  const [expandedNode, setExpandedNode] = useState(null);
  const [viewMode, setViewMode] = useState('graph'); // 'graph', 'steps', 'nodes', 'edges', 'raw'
  const graphRef = useRef();

  if (!data) {
    return (
      <div className="graph-view">
        <p className="no-data">No data to display. Upload an image first.</p>
      </div>
    );
  }

  const nodes = data.nodes || [];
  const edges = data.edges || [];
  const narrative = data.logical_graph?.narrative || [];
  const graphMetadata = data.graph?.metadata || {};

  const copyNarrativeToClipboard = () => {
    const text = narrative.join('\n');
    navigator.clipboard.writeText(text).then(() => {
      alert('Narrative copied to clipboard!');
    }, (err) => {
      console.error('Could not copy text: ', err);
    });
  };

  const highlightText = (text) => {
    const words = ['Start', 'End', 'Decision', 'action'];
    let highlighted = text;
    words.forEach(word => {
      const regex = new RegExp(`\\b${word}\\b`, 'gi');
      highlighted = highlighted.replace(regex, `<span class="hl-${word.toLowerCase()}">$&</span>`);
    });
    return <span dangerouslySetInnerHTML={{ __html: highlighted }} />;
  };

  // Prepare graph data for ForceGraph2D
  const graphData = {
    nodes: nodes.map(node => ({
      id: node.id,
      name: node.id,
      val: node.area ? Math.sqrt(node.area) / 5 : 5, // scaled size
      ...node
    })),
    links: edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      ...edge
    }))
  };

  const getNodeColor = (node) => {
    const type = node.semantic_class || node.type || 'unknown';
    switch (type.toLowerCase()) {
      case 'start': return '#4CAF50'; // Green
      case 'end': return '#f44336';   // Red
      case 'process': return '#2196F3'; // Blue
      case 'decision': return '#FF9800'; // Orange
      case 'data': return '#9C27B0';     // Purple
      default: return '#607D8B';      // Grey
    }
  };

  const renderNodeDetails = (node) => (
    <div className="node-details">
      <h4>{node.type} ({node.semantic_class || 'Unclassified'})</h4>
      <p><strong>ID:</strong> {node.id}</p>
      <p><strong>Labels:</strong> {node.labels?.join(', ') || 'None'}</p>
      <p><strong>Confidence:</strong> {(node.confidence * 100).toFixed(1)}%</p>
      <div className="bbox-info">
        <p><strong>Location:</strong> ({node.center?.x}, {node.center?.y})</p>
      </div>
    </div>
  );

  return (
    <div className="graph-view-container">
      <div className="view-controls">
        <button
          className={`control-btn ${viewMode === 'graph' ? 'active' : ''}`}
          onClick={() => setViewMode('graph')}
        >
          Graph Visual
        </button>
        <button
          className={`control-btn ${viewMode === 'steps' ? 'active' : ''}`}
          onClick={() => setViewMode('steps')}
        >
          Logical Steps
        </button>
        <button
          className={`control-btn ${viewMode === 'nodes' ? 'active' : ''}`}
          onClick={() => setViewMode('nodes')}
        >
          Nodes ({nodes.length})
        </button>
        <button
          className={`control-btn ${viewMode === 'edges' ? 'active' : ''}`}
          onClick={() => setViewMode('edges')}
        >
          Edges ({edges.length})
        </button>
        <button
          className={`control-btn ${viewMode === 'raw' ? 'active' : ''}`}
          onClick={() => setViewMode('raw')}
        >
          Raw Data
        </button>
      </div>

      <div className="graph-content">
        {viewMode === 'graph' && (
          <div className="force-graph-wrapper" style={{ height: '500px', border: '1px solid #eee', borderRadius: '4px', overflow: 'hidden' }}>
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeLabel="label"
              nodeColor={getNodeColor}
              nodeRelSize={6}
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              linkCurvature={0.25}
              linkLabel="label"
              linkCanvasObjectMode={() => 'after'}
              linkCanvasObject={(link, ctx) => {
                const MAX_FONT_SIZE = 4;
                if (!link.label) return;

                const start = link.source;
                const end = link.target;
                if (typeof start !== 'object' || typeof end !== 'object') return;

                const textPos = {
                  x: start.x + (end.x - start.x) / 2,
                  y: start.y + (end.y - start.y) / 2
                };

                const relLink = { x: end.x - start.x, y: end.y - start.y };
                const maxTextLength = Math.sqrt(Math.pow(relLink.x, 2) + Math.pow(relLink.y, 2)) / 2;

                let fontSize = Math.min(MAX_FONT_SIZE, maxTextLength / (link.label.length || 1));
                ctx.font = `${fontSize}px Sans-Serif`;
                const textWidth = ctx.measureText(link.label).width;
                const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

                ctx.save();
                ctx.translate(textPos.x, textPos.y);
                ctx.fillStyle = 'rgba(10, 10, 10, 0.8)';
                ctx.fillRect(-bckgDimensions[0] / 2, -bckgDimensions[1] / 2, ...bckgDimensions);

                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#a1a1aa';
                ctx.fillText(link.label, 0, 0);
                ctx.restore();
              }}
              width={800}
              height={500}
              cooldownTicks={100}
              onEngineStop={() => graphRef.current.zoomToFit(400)}
            />
          </div>
        )}

        {viewMode === 'steps' && (
          <div className="steps-section">
            <div className="section-header-flex">
              <h3>Intelligent Workflow Narrative</h3>
              <button onClick={copyNarrativeToClipboard} className="text-copy-btn">
                Copy to Clipboard
              </button>
            </div>
            {narrative.length === 0 ? (
              <p className="no-items">No logic could be interpreted from this graph.</p>
            ) : (
              <div className="narrative-list">
                {narrative.map((step, idx) => (
                  <div key={idx} className={`narrative-item ${step.includes('↳') ? 'indent-branch' : ''}`}>
                    <span className="step-marker">{step.startsWith('Step') ? step.split(':')[0] : '•'}</span>
                    <span className="step-content">
                      {highlightText(step.includes(':') ? step.split(':').slice(1).join(':').trim() : step)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {viewMode === 'nodes' && (
          <div className="nodes-section">
            <h3>Detected Nodes ({nodes.length})</h3>
            {nodes.length === 0 ? (
              <p className="no-items">No nodes detected</p>
            ) : (
              <div className="nodes-list">
                {nodes.map((node, idx) => (
                  <div
                    key={idx}
                    className={`node-item ${expandedNode === idx ? 'expanded' : ''}`}
                  >
                    <div
                      className="node-header"
                      onClick={() => setExpandedNode(expandedNode === idx ? null : idx)}
                      style={{ borderLeft: `4px solid ${getNodeColor(node)}` }}
                    >
                      <span className="node-type-badge" style={{ backgroundColor: getNodeColor(node) }}>
                        {node.semantic_class || node.type}
                      </span>
                      <span className="node-id">{node.id}</span>
                      <span className="node-label-preview">{node.labels?.[0]}</span>
                      <span className="expand-icon">
                        {expandedNode === idx ? '▼' : '▶'}
                      </span>
                    </div>
                    {expandedNode === idx && renderNodeDetails(node)}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {viewMode === 'edges' && (
          <div className="edges-section">
            <h3>Detected Edges ({edges.length})</h3>
            {edges.length === 0 ? (
              <p className="no-items">No edges detected</p>
            ) : (
              <div className="edges-list">
                {edges.map((edge, idx) => (
                  <div key={idx} className="edge-item">
                    <p>
                      <strong>{edge.source}</strong> → <strong>{edge.target}</strong>
                    </p>
                    {edge.label && <p>Label: {edge.label}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {viewMode === 'raw' && (
          <div className="raw-section">
            <h3>Raw JSON Data</h3>
            <pre className="json-display">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {graphMetadata && (
        <div className="graph-metadata">
          <div className="metadata-header">
            <h4>Accuracy Metrics & Logic</h4>
            <span className="accuracy-badge">High Improvement</span>
          </div>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-label">Nodes Detected</span>
              <span className="metric-value">{graphMetadata.node_count}</span>
            </div>
            <div className="metric-card highlight">
              <span className="metric-label">Noise Reduction</span>
              <span className="metric-value">{graphMetadata.node_reduction_pct}%</span>
            </div>
          </div>

          {graphMetadata.sanity_violations && graphMetadata.sanity_violations.length > 0 && (
            <div className="sanity-check-area">
              <h5 className="warning-title">⚠️ Logic Sanity Warnings</h5>
              <ul className="violations-list">
                {graphMetadata.sanity_violations.map((v, i) => (
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
