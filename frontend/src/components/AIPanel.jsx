/**
 * AIPanel Component
 *
 * Provides AI-powered workflow intelligence features:
 *   - Workflow summary
 *   - Detailed explanation
 *   - Conversational Q&A
 *   - Graph validation
 *   - Mermaid export
 */

import { useState } from "react";
import {
  summarizeWorkflow,
  explainWorkflow,
  chatAboutDiagram,
  validateGraph,
  generateMermaid,
} from "../services/aiService";
import { copyToClipboard } from "../utils/helpers";

export default function AIPanel({ nodes, edges }) {
  const [activeTab, setActiveTab] = useState("summary");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);

  const handleAction = async (action) => {
    setLoading(true);
    setResult(null);

    try {
      let response;
      switch (action) {
        case "summary":
          response = await summarizeWorkflow(nodes, edges);
          if (response.success) setResult(response.data.summary);
          else setResult(response.message || "AI service unavailable. Restart backend with GEMINI_API_KEY in .env");
          break;
        case "explain":
          response = await explainWorkflow(nodes, edges);
          if (response.success) setResult(response.data.explanation);
          else setResult(response.message || "AI service unavailable.");
          break;
        case "validate":
          response = await validateGraph(nodes, edges);
          if (response.success) setResult(response.data.validation);
          else setResult(response.message || "AI service unavailable.");
          break;
        case "mermaid":
          response = await generateMermaid(nodes, edges);
          if (response.success) setResult(response.data.mermaid);
          else setResult(response.message || "AI service unavailable.");
          break;
        default:
          break;
      }
    } catch (err) {
      setResult("Error connecting to AI service.");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim()) return;

    const question = chatInput.trim();
    setChatHistory((prev) => [...prev, { role: "user", text: question }]);
    setChatInput("");
    setLoading(true);

    try {
      const response = await chatAboutDiagram(question, nodes, edges);
      const answer = response.success
        ? response.data.answer
        : "AI service unavailable.";
      setChatHistory((prev) => [...prev, { role: "ai", text: answer }]);
    } catch {
      setChatHistory((prev) => [...prev, { role: "ai", text: "Connection error." }]);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: "summary", label: "Summary" },
    { id: "explain", label: "Explain" },
    { id: "validate", label: "Validate" },
    { id: "mermaid", label: "Mermaid" },
    { id: "chat", label: "Chat" },
  ];

  return (
    <div className="ai-panel">
      <div className="ai-panel-header">
        <h4>AI Workflow Intelligence</h4>
      </div>

      {/* Tab Navigation */}
      <div className="ai-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`ai-tab-btn ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => { setActiveTab(tab.id); setResult(null); }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="ai-content">
        {activeTab !== "chat" && (
          <>
            <button
              className="ai-action-btn"
              onClick={() => handleAction(activeTab)}
              disabled={loading}
            >
              {loading ? "Generating..." : `Generate ${activeTab}`}
            </button>

            {result && (
              <div className="ai-result">
                <div className="ai-result-header">
                  <span>Result</span>
                  <button
                    className="ai-copy-btn"
                    onClick={() => copyToClipboard(result)}
                  >
                    Copy
                  </button>
                </div>
                <pre className="ai-result-text">{result}</pre>
              </div>
            )}
          </>
        )}

        {activeTab === "chat" && (
          <div className="ai-chat">
            <div className="ai-chat-history">
              {chatHistory.length === 0 && (
                <p className="ai-chat-empty">
                  Ask anything about your diagram...
                </p>
              )}
              {chatHistory.map((msg, idx) => (
                <div key={idx} className={`ai-chat-msg ${msg.role}`}>
                  <span className="ai-chat-role">
                    {msg.role === "user" ? "You" : "AI"}
                  </span>
                  <p>{msg.text}</p>
                </div>
              ))}
              {loading && <div className="ai-chat-msg ai"><p>Thinking...</p></div>}
            </div>
            <div className="ai-chat-input">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleChat()}
                placeholder="Ask about this workflow..."
                disabled={loading}
              />
              <button onClick={handleChat} disabled={loading || !chatInput.trim()}>
                Send
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
