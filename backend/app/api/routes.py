"""
API route definitions.

Thin controller layer that handles HTTP concerns (validation, file I/O,
response formatting) and delegates business logic to the pipeline service.

Design principles:
    - Controllers validate input and format output only
    - Business logic lives in services/pipeline.py
    - Errors are raised as typed exceptions, caught by global handlers
"""

from fastapi import APIRouter, File, UploadFile, Request
from fastapi.responses import FileResponse

from app.core.config import (
    API_VERSION,
    UPLOADS_DIR,
    GRAPHS_OUTPUT_DIR,
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_SIZE,
)
from app.core.logging import logger
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.services.pipeline import AnalysisPipeline
from app.utils.helpers import save_uploaded_file, create_response, validate_file_extension

router = APIRouter()

# Singleton pipeline instance — stateless, safe to share across requests
_pipeline = AnalysisPipeline()


@router.get("/health")
async def health_check():
    """
    Health check with dependency status reporting.

    Returns availability of optional dependencies (OCR, NLP) so
    operators can understand degraded functionality without diving into logs.
    """
    return {
        "status": "healthy",
        "service": "node-detection-api",
        "version": API_VERSION,
        "dependencies": {
            "ocr": _pipeline.ocr_available,
            "nlp": _pipeline.nlp_available,
        },
    }


@router.post("/analyze")
async def analyze_diagram(request: Request, file: UploadFile = File(...)):
    """
    Analyze a diagram image and extract its graph structure.

    Runs the full 8-stage detection pipeline:
        1. Preprocessing (resize, threshold, morphology)
        2. Node detection (contour analysis)
        3. OCR (text extraction)
        4. Merging (proximity clustering)
        5. Classification (semantic labeling)
        6. Filtering (noise removal, edge label separation)
        7. Edge detection (Hough transform + node mapping)
        8. Graph construction (NetworkX + narrative)

    Args:
        file: Uploaded image file (PNG, JPG, GIF, BMP). Max 50MB.

    Returns:
        JSON with nodes, edges, graph metadata, narrative, and timing.
    """
    request_id = getattr(request.state, "request_id", None)

    # --- Input Validation ---
    if not file.filename:
        raise ValidationError("No file provided")

    if not validate_file_extension(file.filename, ALLOWED_EXTENSIONS):
        raise ValidationError(
            f"Unsupported file type '{file.filename}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read file content and check size
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise ValidationError(
            f"File too large ({len(content) / 1024 / 1024:.1f}MB). "
            f"Maximum: {MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
        )

    # --- Processing ---
    filepath = save_uploaded_file(file, UPLOADS_DIR, content=content)
    result = _pipeline.analyze(str(filepath))

    return create_response(
        success=True,
        data=result,
        message="Diagram analyzed successfully",
        request_id=request_id,
    )


@router.post("/upload")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """
    Upload an image for storage without processing.

    Useful for batch uploads or deferred processing workflows.
    """
    request_id = getattr(request.state, "request_id", None)
    content = await file.read()
    filepath = save_uploaded_file(file, UPLOADS_DIR, content=content)

    return create_response(
        success=True,
        data={"filepath": str(filepath), "filename": file.filename},
        message="File uploaded successfully",
        request_id=request_id,
    )


@router.get("/graph/{graph_id}")
async def get_graph(graph_id: str):
    """Retrieve a previously generated graph by ID."""
    graph_path = GRAPHS_OUTPUT_DIR / f"{graph_id}.json"
    if not graph_path.exists():
        raise ResourceNotFoundError("Graph", graph_id)
    return FileResponse(graph_path, media_type="application/json")
