# Intelligent Node Detection

A full-stack system that transforms diagram images (flowcharts, system architectures, hand-drawn sketches) into structured directed graphs with semantic classification and human-readable workflow narratives.

Upload a diagram → get back nodes, edges, classifications, and a step-by-step logic narrative.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React + Vite)                       │
│  Upload → Preview → API Call → Graph Visualization + Narrative View  │
└────────────────────────────────────┬────────────────────────────────┘
                                     │ HTTP POST /analyze
┌────────────────────────────────────▼────────────────────────────────┐
│                         Backend (FastAPI)                             │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌─────┐  ┌──────────┐  ┌───────────┐ │
│  │Preprocess│→ │ Detect   │→ │ OCR │→ │ Classify │→ │   Graph   │ │
│  │  Image   │  │  Nodes   │  │     │  │  Nodes   │  │  Builder  │ │
│  └──────────┘  └──────────┘  └─────┘  └──────────┘  └───────────┘ │
│       ↓              ↓                       ↓              ↓       │
│   Binary mask   Raw contours          Semantic types    DiGraph +   │
│                 + line segments        + confidence      Narrative   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Processing Pipeline

| Stage | Module | Description |
|-------|--------|-------------|
| 1 | `Preprocessor` | Resize → Grayscale → Gaussian blur → Adaptive threshold → Morphological closing |
| 2 | `NodeDetector` | Contour detection with shape classification (circle, rectangle, diamond, etc.) |
| 3 | `OCREngine` | Tesseract-based text extraction with 2x upscaling for small labels |
| 4 | `NodeProcessor` | Proximity-based merging of fragmented contours + text assignment |
| 5 | `Classifier` | Semantic labeling (start/end/process/decision) via shape + text + NLP |
| 6 | `EdgeDetector` | Hough line detection → segment clustering → node-to-node mapping |
| 7 | `GraphBuilder` | NetworkX DiGraph construction, sanity validation, BFS narrative generation |

---

## Project Structure

```
intelligent-node-detection/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API endpoint definitions
│   │   ├── core/
│   │   │   ├── config.py          # Centralized configuration
│   │   │   └── logging.py         # Structured logging setup
│   │   ├── processing/
│   │   │   ├── preprocessor.py    # Image preprocessing pipeline
│   │   │   ├── node_detector.py   # Contour-based shape detection
│   │   │   ├── node_processor.py  # Node merging and text grouping
│   │   │   ├── edge_detector.py   # Line/arrow detection
│   │   │   ├── classifier.py      # Semantic classification (NLP + rules)
│   │   │   ├── ocr_engine.py      # Text extraction (Tesseract)
│   │   │   └── graph_builder.py   # Graph construction + narrative
│   │   ├── services/
│   │   │   └── pipeline.py        # Pipeline orchestrator
│   │   ├── utils/
│   │   │   └── helpers.py         # File handling, response formatting
│   │   └── main.py                # FastAPI application factory
│   ├── data/
│   │   ├── samples/               # Test diagram images
│   │   └── uploads/               # User uploads (gitignored)
│   ├── output/                    # Generated graphs (gitignored)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload.jsx         # Drag-and-drop file upload
│   │   │   └── GraphView.jsx      # Multi-tab result visualization
│   │   ├── hooks/
│   │   │   └── useApiStatus.js    # Backend health monitoring
│   │   ├── services/
│   │   │   └── api.js             # HTTP client layer
│   │   ├── constants/
│   │   │   └── index.js           # App-wide constants
│   │   ├── utils/
│   │   │   └── helpers.js         # Shared utility functions
│   │   ├── App.jsx                # Root component
│   │   ├── App.css                # Application styles
│   │   ├── index.css              # Global CSS reset
│   │   └── main.jsx               # React entry point
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Tesseract OCR** installed on your system
  - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`

### Backend Setup

```bash
cd backend
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Optional: install spaCy model for enhanced NLP classification
python -m spacy download en_core_web_sm

# Start the server
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and connects to the backend at `http://localhost:8000`.

---

## Docker Deployment

```bash
# Build and start both services
docker compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## API Reference

### `POST /analyze`

Upload a diagram image for full pipeline analysis.

**Request:** `multipart/form-data` with `file` field (PNG, JPG, GIF, BMP)

**Response:**
```json
{
  "success": true,
  "timestamp": "2026-05-25T10:30:00Z",
  "message": "Diagram analyzed successfully",
  "data": {
    "raw_graph": { "nodes": 47, "edges": 120 },
    "logical_graph": {
      "nodes": [...],
      "edges": [...],
      "metadata": {
        "node_count": 6,
        "edge_count": 5,
        "node_reduction_pct": 87.2,
        "sanity_violations": [],
        "start_nodes": ["logical_node_1"],
        "end_nodes": ["logical_node_6"]
      },
      "narrative": [
        "Step 1: Start the process: Begin",
        "Step 2: Perform action: Process Data",
        "Step 3: Decision point: Is Valid?",
        "   ↳ If Yes, proceed to logical_node_4"
      ]
    }
  }
}
```

### `GET /health`

Health check for container orchestration.

### `GET /docs`

Interactive Swagger API documentation (auto-generated by FastAPI).

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Adaptive thresholding over Otsu | Handles uneven lighting from scanned documents |
| Morphological closing (5×5 ellipse) | Bridges broken contour gaps without merging separate shapes |
| Proximity-based node merging | More robust than IoU for hand-drawn diagrams with imprecise boundaries |
| Text overrides shape classification | Users may draw non-standard shapes (rectangle labeled "Start") |
| BFS for narrative generation | Produces natural reading order from entry to exit points |
| Segment clustering for edges | Hough transform fragments single arrows into multiple segments |

---

## Assumptions & Limitations

- Diagrams should have clear contrast between shapes and background
- Works best with standard flowchart conventions (circles for start/end, diamonds for decisions)
- OCR accuracy depends on text size and image resolution
- Edge detection assumes mostly straight-line connections (curved arrows may not be detected)
- Single-page diagrams only (no multi-page document support)

---

## Future Improvements

- [ ] Support for curved arrow detection (Bezier fitting)
- [ ] Multi-page PDF diagram processing
- [ ] Custom model training for shape detection (YOLO/Faster R-CNN)
- [ ] Real-time collaborative editing of detected graphs
- [ ] Export to standard formats (BPMN, Mermaid, PlantUML)
- [ ] Confidence-based user correction UI

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI + Uvicorn |
| Computer Vision | OpenCV (contour analysis, Hough transform) |
| OCR | Tesseract via pytesseract |
| NLP | spaCy (optional) + regex-based rules |
| Graph Engine | NetworkX (directed graphs) |
| Frontend | React 18 + Vite |
| Visualization | react-force-graph-2d |
| Styling | Custom CSS (dark theme, responsive grid) |
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Nginx (production frontend serving) |

---

## License

MIT
