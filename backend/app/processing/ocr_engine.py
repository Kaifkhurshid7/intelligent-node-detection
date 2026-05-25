"""
OCR (Optical Character Recognition) service.

Extracts text content from diagram images using Tesseract OCR.
Text elements are returned with bounding boxes for spatial mapping
to their containing diagram nodes.
"""

import cv2
import numpy as np
from typing import List, Dict, Any

from app.core.logging import logger


class OCREngine:
    """
    Handles text extraction from diagram images.

    Uses pytesseract with image preprocessing (upscaling + Otsu threshold)
    to improve recognition accuracy on small diagram labels.
    """

    def __init__(self):
        """Initialize OCR engine with graceful fallback if Tesseract is unavailable."""
        try:
            import pytesseract
            self._pytesseract = pytesseract
            self._available = True
            logger.info("OCR engine initialized (pytesseract available)")
        except ImportError:
            self._pytesseract = None
            self._available = False
            logger.warning(
                "pytesseract not installed. Text extraction will be disabled."
            )

    @property
    def is_available(self) -> bool:
        """Whether the OCR engine is operational."""
        return self._available

    def extract_text(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract all text elements from an image with bounding boxes.

        Preprocessing steps for better OCR accuracy:
            1. Convert to grayscale
            2. 2x upscale (small text becomes more readable)
            3. Otsu binarization (clean black/white for Tesseract)

        Only text with confidence > 30% is included to filter noise.

        Args:
            image: BGR color image.

        Returns:
            List of text elements with 'text', 'bbox', and 'confidence'.
        """
        if not self._available:
            return []

        try:
            # Prepare image for OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            upscaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Run Tesseract with word-level bounding boxes
            data = self._pytesseract.image_to_data(
                binary, output_type=self._pytesseract.Output.DICT
            )

            text_elements = []
            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                if not text:
                    continue

                confidence = float(data["conf"][i])
                if confidence <= 30:
                    continue

                # Scale coordinates back to original image size (undo 2x upscale)
                text_elements.append({
                    "text": text,
                    "bbox": {
                        "x": int(data["left"][i] / 2),
                        "y": int(data["top"][i] / 2),
                        "w": int(data["width"][i] / 2),
                        "h": int(data["height"][i] / 2),
                    },
                    "confidence": confidence / 100.0,
                })

            logger.info(f"OCR extracted {len(text_elements)} text elements")
            return text_elements

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
