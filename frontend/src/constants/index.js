/**
 * Application-wide constants.
 *
 * Centralizes color mappings, status values, and configuration
 * to maintain consistency across all components.
 */

/** Semantic node type → display color mapping */
export const NODE_COLORS = {
  start: "#00a870",
  end: "#dc2626",
  process: "#0057f3",
  decision: "#ff5102",
  data: "#7c3aed",
  unknown: "#6b6b6b",
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
