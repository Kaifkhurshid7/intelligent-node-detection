"""NLP-based classification module"""
from typing import List, Dict, Any
import re


class Classifier:
    """Classifies diagram elements using NLP and rule-based logic"""
    
    def __init__(self):
        """Initialize classifier"""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
        except Exception as e:
            print(f"Warning: spaCy not available ({e}). Using rule-based classification only.")
            self.spacy_available = False
            self.nlp = None
        
        # Rule-based keyword mappings
        self.keyword_mappings = {
            'start': [r'\bstart\b', r'\bbegin\b', r'\benter\b'],
            'end': [r'\bend\b', r'\bstop\b', r'\bexit\b', r'\bterminate\b'],
            'process': [r'\bprocess\b', r'\bexecute\b', r'\bperform\b', r'\bdo\b', r'\baction\b'],
            'decision': [r'\bdecision\b', r'\bif\b', r'\bcondition\b', r'\bchoice\b', r'\bcheck\b'],
            'data': [r'\bdata\b', r'\bdatabase\b', r'\bstore\b', r'\binput\b', r'\boutput\b'],
        }
        
        self.element_classes = list(self.keyword_mappings.keys())
    
    def classify(self, nodes: List[Dict], text_elements: List[Dict]) -> List[Dict]:
        """
        Classify diagram elements.
        
        Args:
            nodes: List of detected nodes
            text_elements: List of detected text elements
            
        Returns:
            List of classified elements with semantic information
        """
        classified = []
        
        for node in nodes:
            # Extract labels for this node
            labels = self._extract_labels(node, text_elements)
            
            # Classify the node
            semantic_class = self._classify_node(node, labels)
            
            classified_node = {
                **node,
                'semantic_class': semantic_class,
                'labels': labels,
                'confidence': self._get_classification_confidence(semantic_class, labels),
            }
            classified.append(classified_node)
        
        return classified
    
    def _classify_node(self, node: Dict, labels: List[str]) -> str:
        """
        Classify a single node based on shape, type, and text.
        
        Args:
            node: Node dictionary with shape info
            labels: Associated text labels
            
        Returns:
            Classification string
        """
        # Post-Merge Semantic Classification (Step 5)
        node_type = node.get('type', 'unknown')
        # 1. Shape Geometry based defaults
        shape_mapping = {
            'circle': 'terminal',
            'oval': 'terminal',
            'rectangle': 'process',
            'diamond': 'decision',
            'polygon': 'data',
        }
        
        base_class = shape_mapping.get(node_type, 'connector')
        
        # 2. Refine with text content (FAANG-grade semantic grouping)
        if labels:
            text_class = self._classify_by_text(labels)
            if text_class and text_class != 'connector':
                # Higher weight to text meaning (e.g., text "Start" in a rectangle -> terminal)
                return text_class
        
        return base_class
    
    def _classify_by_text(self, labels: List[str]) -> str:
        """
        Classify based on text content using spaCy or keyword matching.
        
        Args:
            labels: List of label strings
            
        Returns:
            Classification string
        """
        if not labels:
            return 'connector'
        
        combined_text = ' '.join(labels).lower()
        
        # Try keyword-based classification first (fast and reliable)
        for class_name, keywords in self.keyword_mappings.items():
            for pattern in keywords:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return class_name
        
        # Try spaCy if available
        if self.spacy_available and self.nlp:
            try:
                doc = self.nlp(combined_text)
                
                # Simple heuristic: check for action verbs or specific entities
                for token in doc:
                    if token.pos_ == "VERB":
                        return 'process'
                    if token.lemma_ in ['start', 'begin']:
                        return 'start'
                    if token.lemma_ in ['end', 'stop']:
                        return 'end'
                
                # Check for nouns that might indicate data
                nouns = [token.text for token in doc if token.pos_ == "NOUN"]
                if any(n.lower() in ['data', 'database', 'file', 'record'] for n in nouns):
                    return 'data'
            
            except Exception as e:
                print(f"spaCy classification error: {str(e)}")
        
        return 'connector'
    
    def _extract_labels(self, node: Dict, text_elements: List[Dict]) -> List[str]:
        """
        Extract text labels associated with a node.
        
        Args:
            node: Node dictionary
            text_elements: List of text elements
            
        Returns:
            List of label strings
        """
        labels = []
        node_bbox = node['bbox']
        
        # Find text elements within or near the node
        for text_elem in text_elements:
            text_bbox = text_elem.get('bbox', {})
            if self._bbox_overlap(node_bbox, text_bbox):
                labels.append(text_elem.get('text', ''))
        
        return labels
    
    def _bbox_overlap(self, bbox1: Dict, bbox2: Dict, margin: int = 20) -> bool:
        """
        Check if two bounding boxes overlap or are close.
        
        Args:
            bbox1: First bounding box
            bbox2: Second bounding box
            margin: Distance margin for "close" detection
            
        Returns:
            True if boxes overlap or are nearby
        """
        x1_min = bbox1['x'] - margin
        x1_max = bbox1['x'] + bbox1['w'] + margin
        y1_min = bbox1['y'] - margin
        y1_max = bbox1['y'] + bbox1['h'] + margin
        
        x2_min = bbox2.get('x', 0)
        x2_max = bbox2.get('x', 0) + bbox2.get('w', 0)
        y2_min = bbox2.get('y', 0)
        y2_max = bbox2.get('y', 0) + bbox2.get('h', 0)
        
        return not (x1_max < x2_min or x2_max < x1_min or
                    y1_max < y2_min or y2_max < y1_min)
    
    def _get_classification_confidence(self, class_name: str, labels: List[str]) -> float:
        """
        Calculate confidence score for classification.
        
        Args:
            class_name: Classified class name
            labels: Associated labels
            
        Returns:
            Confidence score 0.0-1.0
        """
        if not labels:
            return 0.5  # Default confidence when no labels
        
        # Higher confidence with more labels
        label_count_score = min(len(labels) / 3.0, 1.0)
        
        # Higher confidence if text matches keywords
        combined_text = ' '.join(labels).lower()
        keyword_score = 0.5
        
        for pattern in self.keyword_mappings.get(class_name, []):
            if re.search(pattern, combined_text, re.IGNORECASE):
                keyword_score = 0.95
                break
        
        return (label_count_score * 0.3) + (keyword_score * 0.7)
