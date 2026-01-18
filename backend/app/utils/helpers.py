"""Common utility functions"""
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


def save_uploaded_file(file, upload_dir: Path) -> Path:
    """
    Save an uploaded file to the specified directory.
    
    Args:
        file: FastAPI UploadFile object
        upload_dir: Directory to save the file
        
    Returns:
        Path to saved file
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    filepath = upload_dir / unique_filename
    
    # Save file
    with open(filepath, 'wb') as f:
        f.write(file.file.read())
    
    return filepath


def generate_response(
    success: bool,
    data: Optional[Dict[str, Any]] = None,
    message: str = "",
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a standardized API response.
    
    Args:
        success: Whether the operation was successful
        data: Response data
        message: Success message
        error: Error message
        
    Returns:
        Standardized response dictionary
    """
    return {
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
        'message': message or ('Success' if success else 'Error'),
        'data': data,
        'error': error,
    }


def get_file_size(filepath: Path) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in bytes
    """
    return filepath.stat().st_size if filepath.exists() else 0


def is_valid_image_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if file is a valid image.
    
    Args:
        filename: Name of file
        allowed_extensions: Set of allowed file extensions (e.g., {'.jpg', '.png'})
        
    Returns:
        True if file is valid image
    """
    return Path(filename).suffix.lower() in allowed_extensions


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Delete files older than specified age.
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum age in hours
    """
    if not directory.exists():
        return
    
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filepath in directory.iterdir():
        if filepath.is_file():
            file_age = current_time - filepath.stat().st_mtime
            if file_age > max_age_seconds:
                filepath.unlink()
