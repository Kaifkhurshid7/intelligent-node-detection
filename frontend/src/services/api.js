/**
 * API Service Layer
 *
 * Centralized HTTP client for backend communication.
 * All API calls go through this module for consistent error handling
 * and easy endpoint management.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/**
 * Analyze a diagram image through the detection pipeline.
 *
 * @param {File} file - Image file to analyze.
 * @returns {Promise<Object>} Analysis result with nodes, edges, and graph data.
 * @throws {Error} If the request fails or returns a non-OK status.
 */
export async function analyzeDiagram(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Analysis failed (${response.status}): ${errorText}`);
  }

  return response.json();
}

/**
 * Check if the backend API is reachable and healthy.
 *
 * @returns {Promise<boolean>} True if the backend responds with a healthy status.
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

const api = { analyzeDiagram, checkHealth };
export default api;
