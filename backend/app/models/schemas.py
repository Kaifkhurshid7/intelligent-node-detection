"""
Pydantic schemas for API request/response validation.

Defines typed contracts between the API layer and consumers,
ensuring consistent serialization and automatic OpenAPI documentation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Domain Models
# =============================================================================


class BoundingBox(BaseModel):
    """Pixel-space bounding box for a detected element."""
    x: int
    y: int
    w: int = Field(description="Width in pixels")
    h: int = Field(description="Height in pixels")


class Point(BaseModel):
    """2D coordinate point."""
    x: int
    y: int


class DetectedNode(BaseModel):
    """A classified diagram node with all computed properties."""
    id: str
    label: str = ""
    type: str = Field(description="Semantic class: start, end, process, decision, data")
    shape: str = Field(description="Geometric shape: circle, rectangle, diamond, etc.")
    bbox: BoundingBox
    center: Optional[Point] = None
    confidence: float = Field(ge=0.0, le=1.0)
    labels: List[str] = []


class DetectedEdge(BaseModel):
    """A directed connection between two nodes."""
    source: str
    target: str
    label: str = ""
    direction: str = "->"


class GraphMetadata(BaseModel):
    """Aggregate metrics about the constructed graph."""
    node_count: int
    edge_count: int
    node_reduction_pct: float = Field(description="Percentage of raw contours filtered out")
    sanity_violations: List[str] = []
    start_nodes: List[str] = []
    end_nodes: List[str] = []


class LogicalGraph(BaseModel):
    """The final structured graph with narrative."""
    nodes: List[DetectedNode]
    edges: List[DetectedEdge]
    metadata: GraphMetadata
    narrative: List[str] = []


class RawGraphStats(BaseModel):
    """Raw detection counts before filtering."""
    nodes: int
    edges: int


class PipelineTimings(BaseModel):
    """Execution time for each pipeline stage (milliseconds)."""
    preprocessing_ms: float
    detection_ms: float
    ocr_ms: float
    merging_ms: float
    classification_ms: float
    filtering_ms: float
    edge_detection_ms: float
    graph_construction_ms: float
    total_ms: float


# =============================================================================
# API Response Schemas
# =============================================================================


class AnalysisResult(BaseModel):
    """Complete analysis output from the pipeline."""
    raw_graph: RawGraphStats
    logical_graph: LogicalGraph
    graph: LogicalGraph  # Backward compatibility alias
    nodes: List[Any] = Field(description="Full node data with all CV properties")
    edges: List[Any] = Field(description="Full edge data")
    text: List[Any] = Field(description="Raw OCR text elements")
    timings: Optional[PipelineTimings] = None


class APIResponse(BaseModel):
    """Standardized API response envelope."""
    success: bool
    timestamp: datetime
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response with dependency status."""
    status: str = "healthy"
    service: str = "node-detection-api"
    version: str
    dependencies: dict = Field(default_factory=dict)
