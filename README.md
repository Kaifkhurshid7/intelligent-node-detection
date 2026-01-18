# Intelligent Node Detection

A full-stack application for detecting, analyzing, and extracting structure from diagram images using Computer Vision and NLP.

## 🎯 Overview

This project automatically analyzes diagram images to:
- Detect nodes and shapes (circles, rectangles, diamonds, polygons)
- Extract and recognize text labels (OCR)
- Classify diagram elements semantically
- Build graph representations of diagram structure
- Visualize results in an interactive web interface

## 📋 Project Structure

```
intelligent-node-detection/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Global configuration
│   │   ├── cv/                      # Computer Vision modules
│   │   │   ├── preprocess.py        # Image preprocessing
│   │   │   ├── node_detector.py     # Shape & node detection
│   │   │   └── edge_detector.py     # Edge detection (future)
│   │   ├── ocr/                     # Optical Character Recognition
│   │   │   └── ocr_engine.py        # Text extraction
│   │   ├── nlp/                     # Natural Language Processing
│   │   │   └── classifier.py        # Element classification
│   │   ├── graph/                   # Graph processing
│   │   │   └── graph_builder.py     # Graph construction
│   │   ├── utils/
│   │   │   └── helpers.py           # Utility functions
│   │   └── __init__.py
│   ├── data/
│   │   ├── uploads/                 # Uploaded images
│   │   └── samples/                 # Sample diagrams
│   ├── output/
│   │   ├── graphs/                  # JSON graph outputs
│   │   └── visuals/                 # Debug visualizations
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend container config
│   └── run.sh                        # Backend startup script
│
├── frontend/                         # React + Vite frontend
│   ├── public/
│   │   └── index.html               # HTML entry point
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload.jsx           # File upload component
│   │   │   └── GraphView.jsx        # Results visualization
│   │   ├── services/
│   │   │   └── api.js               # Backend API client
│   │   ├── App.jsx                  # Root component
│   │   ├── main.jsx                 # React entry point
│   │   └── index.css                # Global styles
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
├── .gitignore                        # Git ignore rules
├── README.md                         # This file
└── docker-compose.yml               # Full-stack deployment config
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 🐳 Docker Deployment

Run the entire stack with Docker Compose:

```bash
docker-compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/analyze` | Analyze diagram image |
| POST | `/upload` | Upload image |
| GET | `/graph/{id}` | Retrieve graph by ID |

## 🎨 Features

### Computer Vision
- Image preprocessing (resize, grayscale, blur, threshold)
- Contour detection and analysis
- Shape classification (circle, rectangle, diamond, polygon)
- Node property extraction (area, perimeter, circularity)

### OCR
- Text extraction from images
- Bounding box detection
- Confidence scoring

### NLP Classification
- Element semantic classification (start, end, process, decision, data)
- Label association with nodes
- Shape-to-class mapping

### Graph Processing
- NetworkX graph construction
- Node and edge management
- Graph statistics and analysis
- JSON export

### Frontend UI
- Drag-and-drop image upload
- Image preview
- Real-time analysis
- Interactive results viewer
- Node details inspection
- Edge visualization
- Raw JSON display

## 🔧 Configuration

### Backend (config.py)

Key configuration variables:
- `MAX_UPLOAD_SIZE`: Maximum file size (default: 50 MB)
- `ALLOWED_EXTENSIONS`: Supported file types
- `OPENCV_RESIZE_WIDTH/HEIGHT`: Image processing dimensions
- `CONFIDENCE_THRESHOLD`: Detection confidence threshold
- `HOST`/`PORT`: Server configuration
- `DEBUG`: Development mode

### Frontend (.env)

```bash
REACT_APP_API_URL=http://localhost:8000
```

## 📦 Dependencies

### Backend
- **FastAPI**: Web framework
- **OpenCV**: Computer vision
- **NumPy**: Numerical computing
- **NetworkX**: Graph processing
- **Pillow**: Image processing

### Frontend
- **React 18**: UI library
- **Vite**: Build tool and dev server

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚢 Deployment

### Docker
```bash
docker-compose up -d
```

### Manual Deployment

**Backend (Linux/macOS):**
```bash
cd backend
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve the dist directory with your web server
```

## 📝 Development Notes

### Future Improvements
- [ ] Edge and arrow detection
- [ ] Advanced OCR (Tesseract, EasyOCR)
- [ ] NLP model training
- [ ] Database integration
- [ ] Authentication & authorization
- [ ] Rate limiting
- [ ] Caching
- [ ] Batch processing
- [ ] Real-time analysis with WebSockets
- [ ] Result export (PDF, SVG, XML)

### Known Limitations
- Edge detection is not yet implemented
- OCR requires additional setup (Tesseract, EasyOCR)
- NLP classification is rule-based, not ML-based
- No persistent storage

## 🤝 Contributing

Contributions welcome! Please:
1. Create a feature branch
2. Make your changes
3. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Support

For issues or questions, please open an issue on GitHub.

## 🙏 Acknowledgments

- OpenCV community
- FastAPI framework
- React community
- NetworkX library

---

**Happy analyzing! 🎯**
