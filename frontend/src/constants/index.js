/**
 * Application-wide constants.
 *
 * Centralizes magic values, color mappings, and configuration
 * to avoid scattered hardcoded values across components.
 */

/** Semantic node type → display color mapping */
export const NODE_COLORS = {
  start: "#4CAF50",
  end: "#f44336",
  process: "#2196F3",
  decision: "#FF9800",
  data: "#9C27B0",
  unknown: "#607D8B",
};

/** API connection status values */
export const API_STATUS = {
  CONNECTED: "connected",
  CHECKING: "checking",
  DISCONNECTED: "disconnected",
};

/** Graph view tab identifiers */
export const VIEW_MODES = {
  GRAPH: "graph",
  STEPS: "steps",
  NODES: "nodes",
  EDGES: "edges",
  RAW: "raw",
};

/** Maximum file upload size (10MB) */
export const MAX_FILE_SIZE_MB = 10;

/** Accepted image MIME types */
export const ACCEPTED_FILE_TYPES = "image/png,image/jpeg,image/gif,image/bmp";
