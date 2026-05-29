"""
Structured Prompt Builder.

Constructs well-engineered prompts for the LLM by serializing
graph context (nodes, edges, topology) into structured text
that the model can reason over effectively.
"""

import json
from typing import List, Dict, Any


def build_graph_context(nodes: List[Dict], edges: List[Dict]) -> str:
    """
    Serialize graph structure into a compact text representation
    suitable for LLM consumption.
    """
    lines = ["GRAPH STRUCTURE:", ""]

    lines.append(f"Nodes ({len(nodes)}):")
    for n in nodes:
        display = n.get("display_name", n.get("id", "?"))
        ntype = n.get("type", n.get("semantic_class", "unknown"))
        labels = ", ".join(n.get("labels", []))
        lines.append(f"  - [{ntype.upper()}] {display}" + (f" (text: {labels})" if labels else ""))

    lines.append(f"\nEdges ({len(edges)}):")
    for e in edges:
        src = e.get("source", "?")
        tgt = e.get("target", "?")
        label = e.get("label", "")
        cond = f" [{label}]" if label else ""
        lines.append(f"  - {src} → {tgt}{cond}")

    return "\n".join(lines)


def prompt_workflow_summary(nodes: List[Dict], edges: List[Dict]) -> str:
    """Prompt for generating a concise workflow summary."""
    context = build_graph_context(nodes, edges)
    return f"""You are a workflow analysis expert. Analyze this detected diagram graph and provide:

1. **Summary** (2-3 sentences): What does this workflow do?
2. **Business Interpretation**: What real-world process does this represent?
3. **Key Decision Points**: List any branching logic.
4. **Complexity**: Simple/Medium/Complex and why.

{context}

Respond in clean markdown. Be concise and professional."""


def prompt_workflow_explanation(nodes: List[Dict], edges: List[Dict]) -> str:
    """Prompt for detailed step-by-step workflow explanation."""
    context = build_graph_context(nodes, edges)
    return f"""You are a technical documentation writer. Given this workflow graph, write a clear step-by-step explanation of the process flow.

{context}

Write each step as a natural sentence. Include decision branching (if/else paths). Keep it professional and concise. Use numbered steps."""


def prompt_narrative_enhancement(
    narrative: List[str], nodes: List[Dict], edges: List[Dict]
) -> str:
    """Prompt for enhancing template-based narratives into natural language."""
    context = build_graph_context(nodes, edges)
    raw_narrative = "\n".join(narrative)
    return f"""You are a technical writer. Improve this auto-generated workflow narrative into professional, natural language. Keep the same number of steps but make each one clearer and more descriptive.

CURRENT NARRATIVE:
{raw_narrative}

GRAPH CONTEXT:
{context}

Rewrite each step as a clear, professional sentence. Maintain the step numbering. Output only the improved steps, one per line."""


def prompt_graph_validation(nodes: List[Dict], edges: List[Dict]) -> str:
    """Prompt for AI-powered graph validation and suggestions."""
    context = build_graph_context(nodes, edges)
    return f"""You are a workflow architect. Analyze this graph for structural issues:

{context}

Check for:
1. Disconnected nodes (no incoming or outgoing edges that should have them)
2. Missing branches (decision nodes with only one path)
3. Unreachable states
4. Redundant paths
5. Missing start/end nodes

Provide:
- **Issues Found**: List each problem
- **Suggestions**: How to fix each issue
- **Overall Assessment**: Is this a valid workflow?

Be concise. If the graph looks correct, say so."""


def prompt_chat_question(
    question: str, nodes: List[Dict], edges: List[Dict]
) -> str:
    """Prompt for answering user questions about the diagram."""
    context = build_graph_context(nodes, edges)
    return f"""You are an AI assistant that answers questions about workflow diagrams. Use ONLY the graph data below to answer. If you cannot determine the answer from the data, say so.

{context}

USER QUESTION: {question}

Answer concisely and accurately based on the graph structure above."""


def prompt_mermaid_export(nodes: List[Dict], edges: List[Dict]) -> str:
    """Prompt for generating Mermaid.js diagram syntax."""
    context = build_graph_context(nodes, edges)
    return f"""Convert this graph into valid Mermaid.js flowchart syntax.

{context}

Rules:
- Use `graph TD` (top-down)
- Use appropriate shapes: ([Start/End]), [Process], {{Decision}}, [(Database)]
- Include edge labels where available
- Use short readable node IDs (A, B, C or short names)

Output ONLY the Mermaid code block, no explanation."""
