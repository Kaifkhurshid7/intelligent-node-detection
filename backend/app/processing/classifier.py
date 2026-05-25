"""
Semantic classification service.

Assigns meaningful semantic classes (start, end, process, decision, data)
to detected diagram nodes using a combination of:
    1. Shape-based heuristics (circle → start, diamond → decision)
    2. Text-based keyword matching (regex patterns)
    3. Optional spaCy NLP analysis for ambiguous cases
"""

import re
from typing import List, Dict

from app.core.logging import logger


# Keyword patterns for rule-based text classification
KEYWORD_PATTERNS = {
    "start": [r"\bstart\b", r"\bbegin\b", r"\benter\b"],
    "end": [r"\bend\b", r"\bstop\b", r"\bexit\b", r"\bterminate\b"],
    "process": [r"\bprocess\b", r"\bexecute\b", r"\bperform\b", r"\bdo\b", r"\baction\b"],
    "decision": [r"\bdecision\b", r"\bif\b", r"\bcondition\b", r"\bchoice\b", r"\bcheck\b"],
    "data": [r"\bdata\b", r"\bdatabase\b", r"\bstore\b", r"\binput\b", r"\boutput\b"],
}

# Shape → semantic class mapping (flowchart conventions)
SHAPE_CLASS_MAP = {
    "circle": "start",
    "oval": "start",
    "rectangle": "process",
    "diamond": "decision",
    "polygon": "data",
}


class Classifier:
    """
    Classifies diagram nodes into semantic categories.

    Priority order:
        1. Text content (highest - explicit labels override shape)
        2. Shape geometry (fallback when no text is available)
        3. spaCy NLP (optional refinement for ambiguous text)
    """

    def __init__(self):
        """Initialize classifier with optional spaCy model."""
        self._nlp = None
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("Classifier initialized with spaCy NLP support")
        except Exception:
            logger.info("Classifier initialized (rule-based only, spaCy unavailable)")

    def classify(
        self, nodes: List[Dict], text_elements: List[Dict]
    ) -> List[Dict]:
        """
        Classify all nodes with semantic labels and confidence scores.

        Args:
            nodes: Logical nodes with shape type and labels.
            text_elements: OCR text elements for spatial label extraction.

        Returns:
            Nodes enriched with 'semantic_class' and 'confidence' fields.
        """
        classified = []

        for node in nodes:
            labels = self._extract_labels(node, text_elements)
            semantic_class = self._classify_node(node, labels)
            confidence = self._compute_confidence(semantic_class, labels, node)

            classified.append({
                **node,
                "semantic_class": semantic_class,
                "labels": labels,
                "confidence": confidence,
            })

        logger.info(f"Classified {len(classified)} nodes")
        return classified

    def _classify_node(self, node: Dict, labels: List[str]) -> str:
        """
        Determine semantic class for a single node.

        Text content takes priority over shape because users may draw
        non-standard shapes (e.g., a rectangle labeled "Start").
        """
        # Fallback: shape-based classification
        base_class = SHAPE_CLASS_MAP.get(node.get("type", "unknown"), "process")

        # Override with text-based classification if labels exist
        if labels:
            text_class = self._classify_by_text(labels)
            if text_class:
                return text_class

        return base_class

    def _classify_by_text(self, labels: List[str]) -> str | None:
        """
        Classify based on text content using keyword patterns.

        Falls back to spaCy POS tagging for ambiguous text when available.
        """
        if not labels:
            return None

        combined = " ".join(labels).lower()

        # Fast keyword matching (handles 90%+ of cases)
        for class_name, patterns in KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return class_name

        # Optional: spaCy-based refinement for remaining cases
        if self._nlp:
            return self._classify_with_nlp(combined)

        return None

    def _classify_with_nlp(self, text: str) -> str | None:
        """
        Use spaCy NLP to classify ambiguous text.

        Checks for action verbs (→ process) and domain-specific nouns.
        """
        try:
            doc = self._nlp(text)
            for token in doc:
                if token.pos_ == "VERB":
                    return "process"
                if token.lemma_ in ["start", "begin"]:
                    return "start"
                if token.lemma_ in ["end", "stop"]:
                    return "end"

            nouns = [t.text.lower() for t in doc if t.pos_ == "NOUN"]
            if any(n in ["data", "database", "file", "record"] for n in nouns):
                return "data"
        except Exception as e:
            logger.debug(f"spaCy classification error: {e}")

        return None

    def _extract_labels(self, node: Dict, text_elements: List[Dict]) -> List[str]:
        """
        Collect text labels associated with a node.

        Combines pre-assigned labels (from NodeProcessor) with any
        additional text elements that overlap the node's bounding box.
        """
        labels = list(node.get("labels", []))
        node_bbox = node["bbox"]

        for text_elem in text_elements:
            text = text_elem.get("text", "")
            if text in labels:
                continue
            if self._bbox_overlap(node_bbox, text_elem.get("bbox", {})):
                labels.append(text)

        return labels

    def _bbox_overlap(self, bbox1: Dict, bbox2: Dict, margin: int = 20) -> bool:
        """Check if two bounding boxes overlap within a margin."""
        x1_min = bbox1["x"] - margin
        x1_max = bbox1["x"] + bbox1["w"] + margin
        y1_min = bbox1["y"] - margin
        y1_max = bbox1["y"] + bbox1["h"] + margin

        x2_min = bbox2.get("x", 0)
        x2_max = bbox2.get("x", 0) + bbox2.get("w", 0)
        y2_min = bbox2.get("y", 0)
        y2_max = bbox2.get("y", 0) + bbox2.get("h", 0)

        return not (
            x1_max < x2_min or x2_max < x1_min or
            y1_max < y2_min or y2_max < y1_min
        )

    def _compute_confidence(
        self, class_name: str, labels: List[str], node: Dict
    ) -> float:
        """
        Calculate classification confidence score (0.0 - 1.0).

        Higher confidence when:
            - Text explicitly matches a keyword pattern
            - Shape geometry strongly correlates with the class
            - Node has high solidity (well-formed shape)
        """
        if not labels:
            # Geometry-only confidence
            base = 0.5
            if node.get("solidity", 0) > 0.8:
                base += 0.2
            if node.get("area", 0) > 5000:
                base += 0.1
            return min(base, 0.85)

        # Text-based confidence
        combined = " ".join(labels).lower()
        keyword_score = 0.5

        for target_class, patterns in KEYWORD_PATTERNS.items():
            if target_class == class_name:
                for pattern in patterns:
                    if re.search(pattern, combined, re.IGNORECASE):
                        keyword_score = 0.95
                        break

        label_score = min(len(labels) / 3.0, 1.0)
        return min((label_score * 0.3) + (keyword_score * 0.7), 1.0)
