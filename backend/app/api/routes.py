"""
API route definitions.

Thin controller layer that handles HTTP concerns (validation, file I/O,
response formatting) and delegates business logic to the pipeline service.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.core.config import UPLOADS_DIR, GRAPHS_OUTPUT_DIR, ALLOWED_EXTENSIONS
from app.core.logging import logger
from app.services.pipeline import AnalysisPipeline
from app.utils.helpers import save_uploaded_file, create_response, validate_file_extension

router = APIRouter()

# Single pipeline instance shared across requests
_pipeline = AnalysisPipeline()


@router.get("/health")
async def health_check():
    """Health check endpoint for container orchestration and monitoring."""
    return {"status": "healthy", "service": "node-detection-api"}


@router.post("/analyze")
async def analyze_diagram(file: UploadFile = File(...)):
    """
    Analyze a diagram image and extract its graph structure.

    Accepts an image file and runs the full detection pipeline:
    preprocessing → detection → OCR → classification → graph construction.

    Args:
        file: Uploaded image file (PNG, JPG, GIF, BMP).

    Returns:
        JSON with detected nodes, edges, graph metadata, and narrative.
    """
    # Validate input
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not validate_file_extension(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    try:
        # Save uploaded file to disk
        filepath = save_uploaded_file(file, UPLOADS_DIR)

        # Run analysis pipeline
        result = _pipeline.analyze(str(filepath))

        return create_response(
            success=True,
            data=result,
            message="Diagram analyzed successfully",
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image for storage without processing.

    Useful for batch uploads or deferred processing workflows.
    """
    try:
        filepath = save_uploaded_file(file, UPLOADS_DIR)
        return create_response(
            success=True,
            data={"filepath": str(filepath), "filename": file.filename},
            message="File uploaded successfully",
        )
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/graph/{graph_id}")
async def get_graph(graph_id: str):
    """Retrieve a previously generated graph by ID."""
    graph_path = GRAPHS_OUTPUT_DIR / f"{graph_id}.json"
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="Graph not found")
    return FileResponse(graph_path, media_type="application/json")
