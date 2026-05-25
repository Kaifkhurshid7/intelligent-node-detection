"""
Image preprocessing service.

Handles the initial transformation of raw uploaded images into
binary representations suitable for contour-based node detection.

Pipeline: Load → Resize → Grayscale → Blur → Threshold → Morphology
"""

import cv2
import numpy as np

from app.core.config import (
    RESIZE_WIDTH,
    RESIZE_HEIGHT,
    GAUSSIAN_KERNEL_SIZE,
    ADAPTIVE_BLOCK_SIZE,
    ADAPTIVE_CONSTANT,
    MORPHOLOGY_KERNEL_SIZE,
)
from app.core.logging import logger


class Preprocessor:
    """
    Transforms raw images into binary masks optimized for shape detection.

    The preprocessing pipeline is tuned for flowchart-style diagrams with
    both clean digital lines and noisy hand-drawn strokes.
    """

    def __init__(self):
        self.target_size = (RESIZE_WIDTH, RESIZE_HEIGHT)

    def load_image(self, filepath: str) -> np.ndarray:
        """
        Load an image from disk.

        Args:
            filepath: Absolute path to the image file.

        Returns:
            BGR color image as numpy array.

        Raises:
            ValueError: If the file cannot be read by OpenCV.
        """
        image = cv2.imread(str(filepath))
        if image is None:
            raise ValueError(f"Failed to load image: {filepath}")
        logger.info(f"Loaded image: {filepath} ({image.shape})")
        return image

    def resize(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image dimensions to a consistent size.

        Using INTER_AREA interpolation preserves edge quality during
        downscaling, which is critical for contour detection accuracy.
        """
        return cv2.resize(image, self.target_size, interpolation=cv2.INTER_AREA)

    def preprocess_for_detection(self, image: np.ndarray) -> tuple:
        """
        Execute the full preprocessing pipeline.

        Steps:
            1. Grayscale conversion - reduces 3-channel to single intensity
            2. Gaussian blur (7x7) - suppresses high-frequency noise while
               preserving structural edges in flowchart lines
            3. Adaptive thresholding (inverted) - handles uneven lighting
               from scanned documents; shapes become white on black
            4. Morphological closing (5x5 ellipse) - bridges small gaps in
               broken contours and arrow segments

        Args:
            image: BGR color image (already resized).

        Returns:
            Tuple of (binary_mask, grayscale, original_color).
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Gaussian blur suppresses scanner noise without destroying thin lines
        kernel_size = (GAUSSIAN_KERNEL_SIZE, GAUSSIAN_KERNEL_SIZE)
        blurred = cv2.GaussianBlur(gray, kernel_size, 0)

        # Adaptive threshold handles varying illumination across the image.
        # BINARY_INV makes diagram strokes white (foreground) for findContours.
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            ADAPTIVE_BLOCK_SIZE,
            ADAPTIVE_CONSTANT,
        )

        # Morphological closing connects small breaks in contour boundaries
        # that would otherwise fragment a single shape into multiple detections.
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (MORPHOLOGY_KERNEL_SIZE, MORPHOLOGY_KERNEL_SIZE),
        )
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        logger.debug(
            f"Preprocessing complete: binary white pixels = "
            f"{np.count_nonzero(closed)}/{closed.size}"
        )
        return closed, gray, image
