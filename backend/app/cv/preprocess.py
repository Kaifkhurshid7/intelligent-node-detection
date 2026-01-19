"""Image preprocessing module"""
import cv2
import numpy as np
from pathlib import Path
from skimage import restoration, filters


class PreprocessEngine:
    """Handles image preprocessing and normalization"""
    
    def __init__(self):
        """Initialize preprocessing engine"""
        self.default_resize = (1280, 960)
    
    def load_image(self, filepath):
        """
        Load image from file.
        
        Args:
            filepath: Path to image file
            
        Returns:
            Image array or None if load fails
        """
        try:
            image = cv2.imread(str(filepath))
            if image is None:
                raise ValueError(f"Failed to load image from {filepath}")
            return image
        except Exception as e:
            raise RuntimeError(f"Error loading image: {str(e)}")
    
    def save_image(self, image, filepath):
        """Save image to file"""
        cv2.imwrite(str(filepath), image)
    
    def resize_image(self, image, size=None):
        """
        Resize image to specified dimensions.
        
        Args:
            image: Input image array
            size: Tuple (width, height) for resize. Uses default if None.
            
        Returns:
            Resized image array
        """
        if size is None:
            size = self.default_resize
        
        return cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    
    def convert_to_grayscale(self, image):
        """
        Convert image to grayscale.
        
        Args:
            image: Input image array
            
        Returns:
            Grayscale image array
        """
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def apply_denoise(self, image):
        """
        Apply denoising to image.
        
        Args:
            image: Grayscale image array
            
        Returns:
            Denoised image array
        """
        return cv2.fastNlMeansDenoising(image, h=10, templateWindowSize=7, searchWindowSize=21)
    
    def apply_clahe(self, image):
        """
        Apply Contrast Limited Adaptive Histogram Equalization.
        
        Args:
            image: Grayscale image array
            
        Returns:
            Enhanced image array
        """
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    
    def apply_gaussian_blur(self, image, kernel_size=(5, 5)):
        """
        Apply Gaussian blur to image.
        
        Args:
            image: Input image array
            kernel_size: Size of the kernel
            
        Returns:
            Blurred image array
        """
        return cv2.GaussianBlur(image, kernel_size, 0)
    
    def apply_bilateral_filter(self, image):
        """Apply bilateral filter for edge-preserving smoothing"""
        return cv2.bilateralFilter(image, 9, 75, 75)
    
    def apply_adaptive_threshold(self, image, block_size=11, constant=2):
        """
        Apply adaptive threshold for better handling of varying lighting.
        
        Args:
            image: Grayscale image array
            block_size: Size of pixel neighborhood (must be odd)
            constant: Constant subtracted from mean
            
        Returns:
            Thresholded image array
        """
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, block_size, constant
        )
    
    def apply_threshold(self, image, threshold_value=127, max_value=255):
        """
        Apply binary threshold to image.
        
        Args:
            image: Grayscale image array
            threshold_value: Threshold value
            max_value: Maximum value
            
        Returns:
            Thresholded image array
        """
        _, thresholded = cv2.threshold(image, threshold_value, max_value, cv2.THRESH_BINARY)
        return thresholded
    
    def apply_otsu_threshold(self, image):
        """Apply Otsu's automatic thresholding"""
        _, thresholded = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresholded
    
    def apply_morphological_ops(self, image, operation='open', kernel_size=(3, 3)):
        """
        Apply morphological operations.
        
        Args:
            image: Binary image array
            operation: 'open', 'close', 'dilate', or 'erode'
            kernel_size: Size of the morphological kernel
            
        Returns:
            Processed image array
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        
        if operation == 'open':
            return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        elif operation == 'close':
            return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        elif operation == 'dilate':
            return cv2.dilate(image, kernel, iterations=2)
        elif operation == 'erode':
            return cv2.erode(image, kernel, iterations=2)
        else:
            raise ValueError(f"Unknown morphological operation: {operation}")
    
    def apply_edge_detection(self, image, method='canny', threshold1=50, threshold2=150):
        """
        Apply edge detection.
        
        Args:
            image: Grayscale image array
            method: 'canny' or 'sobel'
            threshold1: Lower threshold for Canny
            threshold2: Upper threshold for Canny
            
        Returns:
            Edge-detected image array
        """
        if method == 'canny':
            return cv2.Canny(image, threshold1, threshold2)
        elif method == 'sobel':
            sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            return np.sqrt(sobelx**2 + sobely**2).astype(np.uint8)
        else:
            raise ValueError(f"Unknown edge detection method: {method}")
    
    def preprocess_for_detection(self, image):
        """
        Refined preprocessing pipeline:
        1. Grayscale conversion
        2. Gaussian blur (noise reduction) - Tuned for flowchart lines
        3. Adaptive thresholding (handles uneven lighting/scans)
        4. Morphological closing (joins broken lines) - Optimized kernel
        """
        # Convert to grayscale
        gray = self.convert_to_grayscale(image)
        
        # Apply Gaussian Blur to smooth noise (Tuned: 7x7 often better for hand-drawn/noisy scans)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        
        # Adaptive Thresholding (Inverted: shapes become white)
        # block_size = 11, constant = 5 (Subtracted constant increased to ignore more background noise)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 5
        )
        
        # Morphological Closing to connect small gaps in contours/arrows
        # We use a slightly larger elliptical kernel (5x5) to heal more significant breaks
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return closed, gray, image
