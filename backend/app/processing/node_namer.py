"""
Semantic Node Naming Engine.

Transforms raw detected nodes with meaningless IDs (logical_node_1, logical_node_2)
into production-grade semantic identifiers that encode workflow meaning.

Naming strategy:
    1. Extract OCR text labels from the node
    2. Determine semantic class (start, end, decision, process, input, output, data)
    3. Sanitize text into a clean snake_case slug
    4. Prefix with the semantic class
    5. Deduplicate by appending a counter only when collisions occur

Example transformations:
    "Start"              → start_process
    "Read A, B, C"       → input_read_a_b_c
    "Is A > B?"          → decision_is_a_greater_than_b
    "Print largest"      → output_print_largest
    "Stop"               → end_process
"""

import re
from typing import List, Dict

from app.core.logging import logger


# =============================================================================
# Symbol replacement map for common operators found in diagram text
# =============================================================================
SYMBOL_REPLACEMENTS = {
    ">": "greater_than",
    "<": "less_than",
    ">=": "greater_than_or_equal",
    "<=": "less_than_or_equal",
    "==": "equals",
    "!=": "not_equals",
    "=": "equals",
    "+": "plus",
    "-": "minus",
    "*": "times",
    "/": "divided_by",
    "%": "modulo",
    "&": "and",
    "|": "or",
}

# Words to strip from generated IDs (noise that doesn't add meaning)
STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being"}

# Semantic class → default fallback name when no text is available
DEFAULT_NAMES = {
    "start": "process",
    "end": "process",
    "decision": "check",
    "process": "action",
    "data": "data",
    "input": "read",
    "output": "write",
    "database": "query",
    "connector": "link",
}

# Prefix mapping for each semantic class
CLASS_PREFIXES = {
    "start": "start",
    "end": "end",
    "decision": "decision",
    "process": "process",
    "data": "data",
    "input": "input",
    "output": "output",
    "database": "database",
    "connector": "connector",
}


class NodeNamer:
    """
    Generates deterministic semantic node identifiers using OCR-derived
    labels and classification-aware prefix normalization.

    Produces both:
        - id: machine-friendly snake_case semantic identifier
        - display_name: human-readable label for UI rendering

    Thread-safe: each call to name_nodes() resets internal state.
    """

    def __init__(self):
        self._used_ids: Dict[str, int] = {}

    def name_nodes(self, nodes: List[Dict]) -> List[Dict]:
        """
        Assign semantic IDs and display names to all nodes.

        Args:
            nodes: Classified nodes with 'semantic_class' and 'labels' fields.

        Returns:
            Nodes enriched with 'id', 'display_name', and 'sequence' fields.
        """
        self._used_ids = {}
        named_nodes = []

        for idx, node in enumerate(nodes):
            semantic_class = node.get("semantic_class", "process")
            labels = node.get("labels", [])
            raw_text = " ".join(labels).strip()

            # Generate the semantic ID
            node_id = self._generate_id(semantic_class, raw_text)

            # Generate human-readable display name
            display_name = self._generate_display_name(semantic_class, raw_text)

            # Enrich the node
            named_node = {
                **node,
                "_original_id": node.get("id", ""),
                "id": node_id,
                "display_name": display_name,
                "sequence": idx + 1,
            }

            logger.debug(
                f"[NodeNaming] Raw OCR: \"{raw_text}\" | "
                f"Sanitized: \"{node_id}\" | Type: {semantic_class}"
            )

            named_nodes.append(named_node)

        logger.info(f"Named {len(named_nodes)} nodes with semantic identifiers")
        return named_nodes

    def _generate_id(self, semantic_class: str, raw_text: str) -> str:
        """
        Generate a deterministic, semantic, snake_case node ID.

        Strategy:
            1. Get the class prefix (e.g., "decision")
            2. Sanitize the OCR text into a slug
            3. Combine: prefix_slug
            4. Deduplicate if collision occurs
        """
        prefix = CLASS_PREFIXES.get(semantic_class, "node")
        slug = self._sanitize_text(raw_text)

        if not slug:
            slug = DEFAULT_NAMES.get(semantic_class, "unnamed")

        candidate = f"{prefix}_{slug}"

        # Deduplicate: only append counter if there's a collision
        if candidate in self._used_ids:
            self._used_ids[candidate] += 1
            candidate = f"{candidate}_{self._used_ids[candidate]}"
        else:
            self._used_ids[candidate] = 0

        return candidate

    def _generate_display_name(self, semantic_class: str, raw_text: str) -> str:
        """
        Generate a human-readable display name for UI rendering.

        If OCR text exists, use it directly (cleaned up).
        Otherwise, generate a descriptive fallback.
        """
        if raw_text:
            # Clean up but preserve readability
            cleaned = raw_text.strip()
            # Capitalize first letter
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:]
            return cleaned

        # Fallback display names
        fallbacks = {
            "start": "Start",
            "end": "End",
            "decision": "Decision",
            "process": "Process",
            "data": "Data",
            "input": "Input",
            "output": "Output",
            "database": "Database",
            "connector": "Connector",
        }
        return fallbacks.get(semantic_class, "Node")

    def _sanitize_text(self, text: str) -> str:
        """
        Convert raw OCR text into a clean snake_case identifier slug.

        Transformations:
            1. Lowercase
            2. Replace mathematical operators with words
            3. Remove quotes, punctuation, and special characters
            4. Collapse whitespace into underscores
            5. Remove duplicate underscores
            6. Trim to reasonable length (max 50 chars)
        """
        if not text:
            return ""

        result = text.lower().strip()

        # Replace multi-char operators first (order matters)
        for symbol in sorted(SYMBOL_REPLACEMENTS.keys(), key=len, reverse=True):
            if symbol in result:
                result = result.replace(symbol, f" {SYMBOL_REPLACEMENTS[symbol]} ")

        # Remove quotes and parentheses
        result = re.sub(r"['\"\(\)\[\]\{\}]", "", result)

        # Remove remaining special characters (keep letters, digits, spaces)
        result = re.sub(r"[^a-z0-9\s]", " ", result)

        # Collapse multiple spaces
        result = re.sub(r"\s+", " ", result).strip()

        # Convert spaces to underscores
        result = result.replace(" ", "_")

        # Remove duplicate underscores
        result = re.sub(r"_+", "_", result)

        # Trim leading/trailing underscores
        result = result.strip("_")

        # Truncate to keep IDs reasonable
        if len(result) > 50:
            # Cut at last underscore before limit to avoid mid-word truncation
            truncated = result[:50]
            last_underscore = truncated.rfind("_")
            if last_underscore > 20:
                result = truncated[:last_underscore]
            else:
                result = truncated

        return result
