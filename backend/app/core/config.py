"""
Centralized application configuration.

All environment variables, paths, and tunable parameters are defined here.
This provides a single source of truth for the entire backend.

Loads .env file automatically for local development.
In production (Docker/Render), env vars are injected by the platform.
"""

import os
from pathlib import Path

# Load .env file if present (local development)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed — rely on system env vars


# =============================================================================
# Path Configuration
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output"
GRAPHS_OUTPUT_DIR = OUTPUT_DIR / "graphs"
VISUALS_OUTPUT_DIR = OUTPUT_DIR / "visuals"

# Ensure required directories exist at startup
for _dir in [UPLOADS_DIR, SAMPLES_DIR, GRAPHS_OUTPUT_DIR, VISUALS_OUTPUT_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


# =============================================================================
# API Configuration
# =============================================================================

API_TITLE = "Intelligent Node Detection API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Transforms diagram images into structured directed graphs "
    "with semantic node classification and workflow narrative generation."
)


# =============================================================================
# File Upload Constraints
# =============================================================================

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}


# =============================================================================
# Image Processing Parameters
# =============================================================================

# Target dimensions for input normalization (width x height)
RESIZE_WIDTH = int(os.getenv("RESIZE_WIDTH", "1280"))
RESIZE_HEIGHT = int(os.getenv("RESIZE_HEIGHT", "960"))

# Preprocessing thresholds
GAUSSIAN_KERNEL_SIZE = 7
ADAPTIVE_BLOCK_SIZE = 11
ADAPTIVE_CONSTANT = 5
MORPHOLOGY_KERNEL_SIZE = 5

# Node detection thresholds
MIN_CONTOUR_AREA = 30
MIN_BBOX_SIZE = 100
MIN_CONFIDENCE = 0.4
MIN_NODE_AREA = 500

# Edge detection parameters
HOUGH_THRESHOLD = 50
MIN_LINE_LENGTH = 50
MAX_LINE_GAP = 20
SEGMENT_CLUSTER_DISTANCE = 40
SEGMENT_ANGLE_TOLERANCE = 15
MAX_EDGE_NODE_DISTANCE = 200
MAX_LABEL_EDGE_DISTANCE = 150

# Node merging parameters
PROXIMAL_MERGE_THRESHOLD = 50


# =============================================================================
# Server Configuration
# =============================================================================

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")


# =============================================================================
# LLM / AI Configuration
# =============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
