"""OCR (Optical Character Recognition) module"""
from typing import List, Dict, Any
import cv2
import numpy as np


class OCREngine:
    """Handles text extraction from images"""
    
    def __init__(self):
        """Initialize OCR engine"""
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.available = True
        except ImportError:
            self.available = False
            print("Warning: pytesseract not available. Text extraction will be limited.")
    
    def extract_text(self, image) -> List[Dict[str, Any]]:
        """
        Extract text from image.
        
        Args:
            image: Image array (BGR color image)
            
        Returns:
            List of detected text elements with bounding boxes
        """
        text_elements = []
        
        if not self.available:
            return text_elements
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Preprocess image for better OCR
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Extract text with bounding boxes
            data = self.pytesseract.image_to_data(gray, output_type=self.pytesseract.Output.DICT)
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                
                if text and len(text) > 0:
                    conf = float(data['conf'][i])
                    
                    # Only include text with reasonable confidence
                    if conf > 30:
                        x = data['left'][i]
                        y = data['top'][i]
                        w = data['width'][i]
                        h = data['height'][i]
                        
                        # Scale back to original image size
                        x = int(x / 2)
                        y = int(y / 2)
                        w = int(w / 2)
                        h = int(h / 2)
                        
                        text_elements.append({
                            'text': text,
                            'bbox': {'x': x, 'y': y, 'w': w, 'h': h},
                            'confidence': conf / 100.0,
                        })
        
        except Exception as e:
            print(f"OCR extraction error: {str(e)}")
        
        return text_elements
    
    def extract_text_from_roi(self, image, bbox: Dict) -> str:
        """
        Extract text from a region of interest.
        
        Args:
            image: Image array
            bbox: Bounding box {'x': int, 'y': int, 'w': int, 'h': int}
            
        Returns:
            Extracted text string
        """
        if not self.available:
            return ""
        
        try:
            x = max(0, bbox['x'])
            y = max(0, bbox['y'])
            w = bbox['w']
            h = bbox['h']
            
            # Crop region
            roi = image[y:y+h, x:x+w]
            
            # Preprocess
            if len(roi.shape) == 3:
                roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Extract text
            text = self.pytesseract.image_to_string(roi)
            return text.strip()
        
        except Exception as e:
            print(f"ROI text extraction error: {str(e)}")
            return ""
    
    def extract_text_with_localization(self, image) -> List[Dict[str, Any]]:
        """
        Extract text with detailed localization information.
        
        Args:
            image: Image array
            
        Returns:
            List of text elements with precise localization
        """
        if not self.available:
            return []
        
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Use pytesseract to get configuration options
            custom_config = r'--oem 3 --psm 6'
            data = self.pytesseract.image_to_data(
                gray, config=custom_config, output_type=self.pytesseract.Output.DICT
            )
            
            results = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    results.append({
                        'text': data['text'][i],
                        'level': data['level'][i],
                        'page_num': data['page_num'][i],
                        'block_num': data['block_num'][i],
                        'par_num': data['par_num'][i],
                        'line_num': data['line_num'][i],
                        'word_num': data['word_num'][i],
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'w': data['width'][i],
                            'h': data['height'][i],
                        },
                        'confidence': data['conf'][i] / 100.0,
                    })
            
            return results
        
        except Exception as e:
            print(f"Detailed OCR error: {str(e)}")
            return []
