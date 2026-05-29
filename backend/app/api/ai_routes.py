"""
AI-powered workflow intelligence API routes.

Provides endpoints for:
    - Workflow summarization
    - Detailed explanation
    - Conversational Q&A
    - Graph validation
    - Mermaid export
    - AI-enhanced narratives

All endpoints gracefully degrade when no LLM provider is configured.
"""

from typing import List, Dict, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.services.llm.workflow_reasoner import WorkflowReasoner
from app.utils.helpers import create_response

ai_router = APIRouter(prefix="/ai", tags=["ai"])

# Singleton reasoner instance
_reasoner = WorkflowReasoner()


# =============================================================================
# Request/Response Models
# =============================================================================


class GraphPayload(BaseModel):
    """Graph data sent from the frontend for AI analysis."""
    nodes: List[Dict] = Field(description="Detected nodes with labels and types")
    edges: List[Dict] = Field(description="Detected edges with source/target")


class ChatPayload(BaseModel):
    """Chat request with question and graph context."""
    question: str = Field(description="User's natural-language question")
    nodes: List[Dict] = []
    edges: List[Dict] = []


# =============================================================================
# Endpoints
# =============================================================================


@ai_router.get("/status")
async def ai_status():
    """Check AI service availability and active provider."""
    return {
        "available": _reasoner.is_available,
        "provider": _reasoner.provider_name,
    }


@ai_router.post("/summarize")
async def summarize_workflow(payload: GraphPayload, request: Request):
    """
    Generate an AI-powered workflow summary.

    Returns a concise business and technical interpretation
    of the detected diagram structure.
    """
    request_id = getattr(request.state, "request_id", None)

    if not _reasoner.is_available:
        return create_response(
            success=False,
            message="AI service unavailable — no API key configured",
            request_id=request_id,
        )

    result = await _reasoner.summarize_workflow(payload.nodes, payload.edges)

    if result:
        return create_response(
            success=True,
            data={"summary": result},
            message="Workflow summary generated",
            request_id=request_id,
        )

    return create_response(
        success=False,
        message="Failed to generate summary",
        request_id=request_id,
    )


@ai_router.post("/explain")
async def explain_workflow(payload: GraphPayload, request: Request):
    """Generate a detailed step-by-step workflow explanation."""
    request_id = getattr(request.state, "request_id", None)

    if not _reasoner.is_available:
        return create_response(
            success=False,
            message="AI service unavailable",
            request_id=request_id,
        )

    result = await _reasoner.explain_workflow(payload.nodes, payload.edges)

    return create_response(
        success=True if result else False,
        data={"explanation": result} if result else None,
        message="Explanation generated" if result else "Failed",
        request_id=request_id,
    )


@ai_router.post("/chat")
async def chat_about_diagram(payload: ChatPayload, request: Request):
    """
    Conversational Q&A about the uploaded diagram.

    Users can ask natural-language questions and receive
    answers grounded in the detected graph structure.
    """
    request_id = getattr(request.state, "request_id", None)

    if not _reasoner.is_available:
        return create_response(
            success=False,
            message="AI service unavailable",
            request_id=request_id,
        )

    if not payload.question.strip():
        return create_response(
            success=False,
            message="Question cannot be empty",
            request_id=request_id,
        )

    result = await _reasoner.answer_question(
        payload.question, payload.nodes, payload.edges
    )

    return create_response(
        success=True if result else False,
        data={"answer": result} if result else None,
        message="Answer generated" if result else "Failed to generate answer",
        request_id=request_id,
    )


@ai_router.post("/validate")
async def validate_graph(payload: GraphPayload, request: Request):
    """AI-powered structural validation with optimization suggestions."""
    request_id = getattr(request.state, "request_id", None)

    if not _reasoner.is_available:
        return create_response(
            success=False,
            message="AI service unavailable",
            request_id=request_id,
        )

    result = await _reasoner.validate_graph(payload.nodes, payload.edges)

    return create_response(
        success=True if result else False,
        data={"validation": result} if result else None,
        message="Validation complete" if result else "Failed",
        request_id=request_id,
    )


@ai_router.post("/mermaid")
async def generate_mermaid(payload: GraphPayload, request: Request):
    """Generate Mermaid.js flowchart syntax from the graph."""
    request_id = getattr(request.state, "request_id", None)

    if not _reasoner.is_available:
        return create_response(
            success=False,
            message="AI service unavailable",
            request_id=request_id,
        )

    result = await _reasoner.generate_mermaid(payload.nodes, payload.edges)

    return create_response(
        success=True if result else False,
        data={"mermaid": result} if result else None,
        message="Mermaid diagram generated" if result else "Failed",
        request_id=request_id,
    )


@ai_router.post("/enhance-narrative")
async def enhance_narrative(request: Request, payload: dict):
    """Enhance template-based narrative with AI-generated language."""
    request_id = getattr(request.state, "request_id", None)

    if not _reasoner.is_available:
        return create_response(
            success=False,
            message="AI service unavailable",
            request_id=request_id,
        )

    narrative = payload.get("narrative", [])
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])

    result = await _reasoner.enhance_narrative(narrative, nodes, edges)

    return create_response(
        success=True if result else False,
        data={"enhanced_narrative": result} if result else None,
        message="Narrative enhanced" if result else "Failed",
        request_id=request_id,
    )
