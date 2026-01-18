import React, { useState, useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

/**
 * GraphView component for displaying detected nodes and graph structure
 */
export default function GraphView({ data }) {
  const [expandedNode, setExpandedNode] = useState(null);
  const [viewMode, setViewMode] = useState('graph'); // 'graph', 'nodes', 'edges', 'raw'
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
  const graphMetadata = data.graph?.metadata || {};

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
              width={800}
              height={500}
              cooldownTicks={100}
              onEngineStop={() => graphRef.current.zoomToFit(400)}
            />
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
          <h4>Graph Statistics</h4>
          <ul>
            <li>Nodes: {graphMetadata.node_count}</li>
            <li>Edges: {graphMetadata.edge_count}</li>
            <li>Type: {graphMetadata.graph_type}</li>
          </ul>
        </div>
      )}
    </div>
  );
}
