"""Global configuration for the application"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output"
GRAPHS_OUTPUT_DIR = OUTPUT_DIR / "graphs"
VISUALS_OUTPUT_DIR = OUTPUT_DIR / "visuals"

# Create directories if they don't exist
for directory in [UPLOADS_DIR, SAMPLES_DIR, GRAPHS_OUTPUT_DIR, VISUALS_OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Configuration
API_TITLE = "Intelligent Node Detection API"
API_VERSION = "0.1.0"
API_DESCRIPTION = "API for detecting and analyzing diagram components"

# File upload configuration
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

# Processing configuration
OPENCV_RESIZE_WIDTH = 1280
OPENCV_RESIZE_HEIGHT = 960
CONFIDENCE_THRESHOLD = 0.5

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
