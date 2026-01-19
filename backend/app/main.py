"""FastAPI entry point for the application"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import numpy as np
from pathlib import Path

from app import config
from app.cv.preprocess import PreprocessEngine
from app.cv.node_detector import NodeDetector
from app.cv.edge_detector import EdgeDetector
from app.cv.node_processor import NodeProcessor
from app.ocr.ocr_engine import OCREngine
from app.nlp.classifier import Classifier
from app.graph.graph_builder import GraphBuilder
from app.utils.helpers import save_uploaded_file, generate_response

# Initialize FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processing engines
preprocess_engine = PreprocessEngine()
node_detector = NodeDetector()
edge_detector = EdgeDetector()
node_processor = NodeProcessor()
ocr_engine = OCREngine()
classifier = Classifier()
graph_builder = GraphBuilder()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Intelligent Node Detection API",
        "version": config.API_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": config.API_VERSION,
    }


@app.post("/analyze")
async def analyze_diagram(file: UploadFile = File(...)):
    """
    Analyze a diagram image and extract nodes, edges, and text.
    Complete pipeline: preprocessing -> node detection -> OCR -> NLP classification -> graph construction
    
    Args:
        file: Uploaded image file
        
    Returns:
        JSON with detected nodes, edges, and extracted text
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Save uploaded file
        filepath = save_uploaded_file(file, config.UPLOADS_DIR)
        
        # === STAGE 1: Image Preprocessing (TASK 1) ===
        original_image = preprocess_engine.load_image(filepath)
        image_resized = preprocess_engine.resize_image(original_image)
        binary_image, gray_image, color_image = preprocess_engine.preprocess_for_detection(image_resized)
        
        # === STAGE 2: Raw Primitive Detection (TASK 2) ===
        raw_nodes = node_detector.detect(binary_image)
        # Get raw segments for metrics
        raw_lines = edge_detector.detect_lines(binary_image, threshold=50)
        raw_edges_count = len(raw_lines) if raw_lines is not None else 0
        
        # === STAGE 3: OCR (Text Extraction) ===
        text_elements = ocr_engine.extract_text(image_resized)
        
        # === STAGE 4: Logical Node Processing (Merging & Grouping) (TASK 3 & 4) ===
        # Merge fragmented contours using proximal distance (threshold=50px)
        logical_nodes = node_processor.merge_proximal_nodes(raw_nodes, threshold=50)
        
        # Group text into nodes spatially and sort by reading order
        logical_nodes = node_processor.group_text_into_nodes(logical_nodes, text_elements)
        
        # === STAGE 5: Semantic Classification (TASK 5) ===
        # Refine types using geometry + newly grouped text
        classified_nodes = classifier.classify(logical_nodes, text_elements)
        
        # Filter noise (Keep nodes that are large enough OR have text)
        final_nodes = [n for n in classified_nodes if n['area'] > 1000 or n['labels']]
        
        # === STAGE 6: Logical Edge Detection (TASK 6 & 7) ===
        # Connect logical shapes based on visual connectivity and proximity to boundaries
        edges = edge_detector.detect_edges_from_contours(binary_image, final_nodes)
        
        # === STAGE 7: Graph Construction and Sanity (TASK 8, 9, 10) ===
        # Build the graph and calculate metrics
        graph_data = graph_builder.build_from_elements(
            elements=final_nodes, 
            edges=edges,
            raw_nodes_count=len(raw_nodes),
            raw_edges_count=raw_edges_count
        )
        
        return generate_response(
            success=True,
            data={
                **graph_data,
                "nodes": final_nodes,
                "edges": edges,
                "text": text_elements
            },
            message="Diagram analyzed successfully with improved accuracy"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image for later processing.
    
    Args:
        file: Image file to upload
        
    Returns:
        File path and metadata
    """
    try:
        filepath = save_uploaded_file(file, config.UPLOADS_DIR)
        return generate_response(
            success=True,
            data={"filepath": str(filepath), "filename": file.filename},
            message="File uploaded successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/{graph_id}")
async def get_graph(graph_id: str):
    """
    Retrieve a previously generated graph.
    
    Args:
        graph_id: ID of the graph to retrieve
        
    Returns:
        Graph JSON data
    """
    try:
        graph_path = config.GRAPHS_OUTPUT_DIR / f"{graph_id}.json"
        if not graph_path.exists():
            raise HTTPException(status_code=404, detail="Graph not found")
        return FileResponse(graph_path, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
