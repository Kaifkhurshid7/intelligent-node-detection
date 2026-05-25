/**
 * Shared utility functions for the frontend.
 */

import { NODE_COLORS } from "../constants";

/**
 * Get the display color for a node based on its semantic type.
 *
 * @param {Object} node - Node object with type or semantic_class field.
 * @returns {string} Hex color string.
 */
export function getNodeColor(node) {
  const type = (node.semantic_class || node.type || "unknown").toLowerCase();
  return NODE_COLORS[type] || NODE_COLORS.unknown;
}

/**
 * Copy text to the system clipboard.
 *
 * @param {string} text - Text content to copy.
 * @returns {Promise<boolean>} Whether the copy succeeded.
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
