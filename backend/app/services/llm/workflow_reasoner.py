"""
Workflow Reasoning Engine.

Orchestrates LLM calls for semantic workflow intelligence:
    - Summarization
    - Explanation
    - Narrative enhancement
    - Validation
    - Q&A
    - Mermaid export

All methods gracefully degrade to None when LLM is unavailable,
allowing the system to fall back to template-based outputs.
"""

from typing import List, Dict, Any, Optional

from app.core.logging import logger
from app.services.llm.provider import LLMService
from app.services.llm.prompt_builder import (
    prompt_workflow_summary,
    prompt_workflow_explanation,
    prompt_narrative_enhancement,
    prompt_graph_validation,
    prompt_chat_question,
    prompt_mermaid_export,
)


# In-memory cache for repeated requests (simple LRU-style)
_cache: Dict[str, str] = {}
_CACHE_MAX = 50


def _cache_key(prefix: str, nodes: List[Dict], edges: List[Dict]) -> str:
    """Generate a deterministic cache key from graph structure."""
    node_ids = tuple(n.get("id", "") for n in nodes)
    edge_ids = tuple((e.get("source", ""), e.get("target", "")) for e in edges)
    return f"{prefix}:{hash((node_ids, edge_ids))}"


class WorkflowReasoner:
    """
    High-level AI reasoning interface for workflow intelligence.

    Wraps the LLM service with domain-specific prompt engineering,
    caching, and graceful fallback behavior.
    """

    def __init__(self):
        self._llm = LLMService()

    @property
    def is_available(self) -> bool:
        """Whether AI reasoning is operational."""
        return self._llm.is_available

    @property
    def provider_name(self) -> str:
        """Active LLM provider name."""
        return self._llm.provider_name

    async def summarize_workflow(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> Optional[str]:
        """
        Generate a concise AI summary of the detected workflow.

        Returns a markdown-formatted summary with business interpretation,
        decision points, and complexity assessment.
        """
        cache_key = _cache_key("summary", nodes, edges)
        if cache_key in _cache:
            return _cache[cache_key]

        prompt = prompt_workflow_summary(nodes, edges)
        result = await self._llm.generate(prompt, max_tokens=512)

        if result:
            _set_cache(cache_key, result)
            logger.info("AI workflow summary generated")

        return result

    async def explain_workflow(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> Optional[str]:
        """
        Generate a detailed step-by-step workflow explanation.

        Produces natural-language documentation of the process flow
        suitable for technical documentation.
        """
        cache_key = _cache_key("explain", nodes, edges)
        if cache_key in _cache:
            return _cache[cache_key]

        prompt = prompt_workflow_explanation(nodes, edges)
        result = await self._llm.generate(prompt, max_tokens=768)

        if result:
            _set_cache(cache_key, result)

        return result

    async def enhance_narrative(
        self, narrative: List[str], nodes: List[Dict], edges: List[Dict]
    ) -> Optional[List[str]]:
        """
        Enhance template-based narrative steps with AI-generated language.

        Transforms generic steps like "Access data" into descriptive
        sentences like "Read user credentials from the input form".
        """
        if not narrative:
            return None

        prompt = prompt_narrative_enhancement(narrative, nodes, edges)
        result = await self._llm.generate(prompt, max_tokens=768)

        if result:
            # Parse response into individual steps
            lines = [
                line.strip()
                for line in result.strip().split("\n")
                if line.strip() and not line.strip().startswith("---")
            ]
            if lines:
                logger.info(f"AI enhanced {len(lines)} narrative steps")
                return lines

        return None

    async def validate_graph(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> Optional[str]:
        """
        AI-powered structural validation of the workflow graph.

        Identifies disconnected nodes, missing branches, unreachable
        states, and provides optimization suggestions.
        """
        cache_key = _cache_key("validate", nodes, edges)
        if cache_key in _cache:
            return _cache[cache_key]

        prompt = prompt_graph_validation(nodes, edges)
        result = await self._llm.generate(prompt, max_tokens=512)

        if result:
            _set_cache(cache_key, result)

        return result

    async def answer_question(
        self, question: str, nodes: List[Dict], edges: List[Dict]
    ) -> Optional[str]:
        """
        Answer a user's natural-language question about the diagram.

        Uses graph context to provide accurate, grounded responses.
        """
        prompt = prompt_chat_question(question, nodes, edges)
        result = await self._llm.generate(prompt, max_tokens=512)
        return result

    async def generate_mermaid(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> Optional[str]:
        """
        Generate Mermaid.js flowchart syntax from the graph structure.

        Output can be directly rendered by Mermaid-compatible viewers.
        """
        cache_key = _cache_key("mermaid", nodes, edges)
        if cache_key in _cache:
            return _cache[cache_key]

        prompt = prompt_mermaid_export(nodes, edges)
        result = await self._llm.generate(prompt, max_tokens=512)

        if result:
            # Clean up: extract just the mermaid code if wrapped in backticks
            if "```" in result:
                lines = result.split("\n")
                code_lines = []
                in_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block:
                        code_lines.append(line)
                result = "\n".join(code_lines) if code_lines else result

            _set_cache(cache_key, result)
            logger.info("Mermaid diagram generated")

        return result


def _set_cache(key: str, value: str) -> None:
    """Set cache entry, evicting oldest if at capacity."""
    global _cache
    if len(_cache) >= _CACHE_MAX:
        # Remove first (oldest) entry
        oldest_key = next(iter(_cache))
        del _cache[oldest_key]
    _cache[key] = value
