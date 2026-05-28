"""
Shared utility functions.

Provides reusable helpers for file handling, response formatting,
and input validation used across the application.
"""

import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Set


def save_uploaded_file(
    file, upload_dir: Path, content: Optional[bytes] = None
) -> Path:
    """
    Save an uploaded file with a unique filename.

    Generates a UUID-based filename to prevent collisions and
    path traversal attacks from user-supplied filenames.

    Args:
        file: FastAPI UploadFile object.
        upload_dir: Target directory for the saved file.
        content: Pre-read file bytes (avoids double-read in async context).

    Returns:
        Path to the saved file on disk.
    """
    upload_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4()}{extension}"
    filepath = upload_dir / unique_name

    if content is not None:
        filepath.write_bytes(content)
    else:
        with open(filepath, "wb") as f:
            f.write(file.file.read())

    return filepath


def create_response(
    success: bool,
    data: Optional[Dict[str, Any]] = None,
    message: str = "",
    error: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a standardized API response envelope.

    Consistent structure across all endpoints makes it easier for
    frontend consumers to handle success/error states uniformly.

    Args:
        success: Whether the operation completed successfully.
        data: Response payload.
        message: Human-readable status message.
        error: Error description (only for failures).
        request_id: Trace ID for this request.

    Returns:
        Standardized response dictionary.
    """
    response = {
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message or ("Success" if success else "Error"),
        "data": data,
    }

    if error:
        response["error"] = error
    if request_id:
        response["request_id"] = request_id

    return response


def validate_file_extension(filename: str, allowed: Set[str]) -> bool:
    """
    Check if a filename has an allowed extension.

    Args:
        filename: Original filename from upload.
        allowed: Set of permitted extensions (e.g., {'.png', '.jpg'}).

    Returns:
        True if the file extension is in the allowed set.
    """
    return Path(filename).suffix.lower() in allowed
