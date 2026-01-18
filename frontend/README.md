# Frontend - Intelligent Node Detection

React + Vite frontend for the Intelligent Node Detection application.

## Features

- Image upload with drag-and-drop support
- Real-time diagram analysis
- Interactive visualization of detected nodes
- Graph structure exploration
- JSON data export

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

This creates an optimized production build in the `dist` directory.

## Components

- **Upload.jsx** - File upload component with preview
- **GraphView.jsx** - Results visualization component
- **api.js** - Backend API service

## API Integration

The frontend communicates with the backend API at `http://localhost:8000` by default.
Configure the API URL via the `REACT_APP_API_URL` environment variable.

## Environment Variables

```bash
REACT_APP_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Upload.jsx
│   │   └── GraphView.jsx
│   ├── services/
│   │   └── api.js
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── package.json
└── vite.config.js
```
