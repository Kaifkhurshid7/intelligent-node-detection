"""
Diagram analysis pipeline orchestrator.

Coordinates the full processing flow from raw image to structured graph.
This is the core business logic layer that ties together all processing
modules in the correct sequence.
"""

from typing import Dict, Any

from app.core.config import MIN_CONFIDENCE, MIN_NODE_AREA
from app.core.logging import logger
from app.processing.preprocessor import Preprocessor
from app.processing.node_detector import NodeDetector
from app.processing.node_processor import NodeProcessor
from app.processing.edge_detector import EdgeDetector
from app.processing.ocr_engine import OCREngine
from app.processing.classifier import Classifier
from app.processing.graph_builder import GraphBuilder


class AnalysisPipeline:
    """
    Orchestrates the complete diagram-to-graph analysis pipeline.

    Stages:
        1. Preprocessing - normalize and binarize the input image
        2. Detection - find raw contours and line segments
        3. OCR - extract text labels from the image
        4. Merging - consolidate fragmented detections into logical nodes
        5. Classification - assign semantic meaning to each node
        6. Filtering - remove noise and identify edge labels
        7. Edge detection - connect nodes with directed edges
        8. Graph construction - build final graph with metrics
    """

    def __init__(self):
        self._preprocessor = Preprocessor()
        self._node_detector = NodeDetector()
        self._node_processor = NodeProcessor()
        self._edge_detector = EdgeDetector()
        self._ocr_engine = OCREngine()
        self._classifier = Classifier()
        self._graph_builder = GraphBuilder()

    def analyze(self, filepath: str) -> Dict[str, Any]:
        """
        Run the full analysis pipeline on an uploaded image.

        Args:
            filepath: Path to the uploaded image file.

        Returns:
            Complete analysis result with graph, nodes, edges, and text.

        Raises:
            ValueError: If the image cannot be loaded.
            RuntimeError: If a critical pipeline stage fails.
        """
        logger.info(f"Starting analysis pipeline for: {filepath}")

        # Stage 1: Image preprocessing
        original = self._preprocessor.load_image(filepath)
        resized = self._preprocessor.resize(original)
        binary, gray, color = self._preprocessor.preprocess_for_detection(resized)

        # Stage 2: Raw primitive detection
        raw_nodes = self._node_detector.detect(binary)
        raw_edges_count = len(self._edge_detector._detect_lines(binary))

        # Stage 3: Text extraction via OCR
        text_elements = self._ocr_engine.extract_text(resized)

        # Stage 4: Merge fragmented contours into logical nodes
        logical_nodes = self._node_processor.merge_proximal_nodes(raw_nodes)
        logical_nodes = self._node_processor.assign_text_to_nodes(
            logical_nodes, text_elements
        )

        # Stage 5: Semantic classification
        classified_nodes = self._classifier.classify(logical_nodes, text_elements)

        # Stage 6: Filter noise and separate edge labels
        final_nodes, edge_labels = self._filter_nodes(classified_nodes)

        # Stage 7: Detect logical edges between nodes
        edges = self._edge_detector.detect(binary, final_nodes, edge_labels)

        # Stage 8: Build graph and compute metrics
        graph_data = self._graph_builder.build(
            elements=final_nodes,
            edges=edges,
            raw_nodes_count=len(raw_nodes),
            raw_edges_count=raw_edges_count,
        )

        logger.info("Pipeline complete")

        return {
            **graph_data,
            "nodes": final_nodes,
            "edges": edges,
            "text": text_elements,
        }

    def _filter_nodes(self, nodes: list) -> tuple:
        """
        Apply confidence and area thresholds, and separate edge labels.

        Edge labels are small text nodes (e.g., "Yes", "No") that should
        be attached to edges rather than treated as standalone nodes.

        Returns:
            Tuple of (final_nodes, edge_label_nodes).
        """
        final_nodes = []
        edge_labels = []

        # Common edge label keywords in flowcharts
        edge_label_keywords = {"yes", "no", "y", "n", "true", "false", "t", "f"}

        for node in nodes:
            text = " ".join(node.get("labels", [])).strip().lower()

            # Identify edge labels: small text that belongs on connections
            is_edge_keyword = text in edge_label_keywords
            is_small_data = (
                node.get("semantic_class") == "data" and 1 <= len(text) <= 3
            )

            if is_edge_keyword or is_small_data:
                edge_labels.append(node)
                continue

            # Keep nodes that have text labels (definitely meaningful)
            # or pass confidence + area thresholds
            has_labels = len(node.get("labels", [])) > 0
            passes_threshold = (
                node["confidence"] >= MIN_CONFIDENCE
                and node.get("area", 0) >= MIN_NODE_AREA
            )

            if has_labels or passes_threshold:
                final_nodes.append(node)

        logger.info(
            f"Filtering: {len(final_nodes)} nodes kept, "
            f"{len(edge_labels)} edge labels separated"
        )
        return final_nodes, edge_labels
