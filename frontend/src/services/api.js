/**
 * API service for communication with backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = {
  /**
   * Analyze a diagram image
   */
  async analyzeDiagram(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE}/health`);
      return response.ok;
    } catch {
      return false;
    }
  },
};

export default api;
