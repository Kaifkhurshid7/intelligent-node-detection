/**
 * AI Service Layer
 *
 * Handles communication with the backend AI endpoints for
 * workflow intelligence features (summarize, explain, chat, validate, mermaid).
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/**
 * Check if AI features are available on the backend.
 */
export async function getAIStatus() {
  try {
    const res = await fetch(`${API_BASE}/ai/status`);
    return res.ok ? await res.json() : { available: false };
  } catch {
    return { available: false };
  }
}

/**
 * Generate an AI workflow summary.
 */
export async function summarizeWorkflow(nodes, edges) {
  const res = await fetch(`${API_BASE}/ai/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nodes, edges }),
  });
  return res.json();
}

/**
 * Generate a detailed workflow explanation.
 */
export async function explainWorkflow(nodes, edges) {
  const res = await fetch(`${API_BASE}/ai/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nodes, edges }),
  });
  return res.json();
}

/**
 * Ask a question about the diagram.
 */
export async function chatAboutDiagram(question, nodes, edges) {
  const res = await fetch(`${API_BASE}/ai/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, nodes, edges }),
  });
  return res.json();
}

/**
 * Validate graph structure with AI.
 */
export async function validateGraph(nodes, edges) {
  const res = await fetch(`${API_BASE}/ai/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nodes, edges }),
  });
  return res.json();
}

/**
 * Generate Mermaid.js diagram code.
 */
export async function generateMermaid(nodes, edges) {
  const res = await fetch(`${API_BASE}/ai/mermaid`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nodes, edges }),
  });
  return res.json();
}
