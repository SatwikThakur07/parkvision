# ParkVision - Integrated Vehicle Monitoring System

A comprehensive parking management system that combines **License Plate Recognition (NPR)** and **Parking Space Detection (PSD1)** into a unified real-time monitoring platform.

## 🚀 Features

- **Real-time License Plate Detection**: Detect and recognize license plates from live camera feeds or video files
- **Parking Space Monitoring**: Track parking space occupancy with visual indicators (green = available, red = occupied)
- **Interactive Annotation**: Draw parking space polygons directly on captured frames
- **Comprehensive Logging**: Automatic logging of all detections and parking state changes
- **Modern Web Interface**: Beautiful, responsive UI with real-time updates
- **API Documentation**: Full REST API with interactive Swagger documentation

## 📋 Prerequisites

- Python 3.8 or higher
- Webcam or video file for processing
- Model files (see Setup section)

## 🛠️ Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements_integrated.txt
```

### 2. Verify Model Files

- **License Plate Model**: `npr/license_plate_best.pt` (should already exist)
- **Vehicle Detection Model**: `psd1/yolov8n.pt` (downloads automatically on first run)

### 3. Start the Server

```bash
python3 run_integrated.py
```

### 4. Access the Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

### Real-Time Detection (Webcam)

1. **Start Camera**: Click "Start Camera" and allow browser camera access
2. **Annotate Parking Spaces** (First Time):
   - Click "Capture Frame" to freeze the current view
   - Click "Annotate Spaces" to enter annotation mode
   - Draw polygons around each parking space by clicking points
   - Press **S** or **Enter** to save current polygon
   - Press **A** or click "Save All & Finish" to complete annotation
3. **View Results**:
   - **Parking Layout**: Real-time visualization (green = available, red = occupied)
   - **Detected Plates**: List of all detected license plates
   - **Dashboard Stats**: Total spaces, available, occupied, and today's entries

### Video File Processing

1. **License Plate Detection**:
   - Upload a video file
   - Click "Start Processing"
   - Download results when complete

2. **Parking Space Monitoring**:
   - Upload video file and parking space configuration (JSON)
   - Click "Start Processing"
   - View metrics and download results

## 📁 Project Structure

```
npr_and_psd/
├── integrated_api.py          # Main FastAPI server
├── run_integrated.py          # Server startup script
├── static/
│   └── index.html            # Web frontend
├── npr/                       # License Plate Recognition module
│   ├── src/
│   │   ├── plate_processor.py
│   │   └── video_processor.py
│   └── license_plate_best.pt  # YOLO model for plates
├── psd1/                      # Parking Space Detection module
│   ├── parking_analyzer.py
│   ├── vehicle_detector.py
│   └── config_manager.py
├── results/                   # Log files and outputs
│   ├── all_plate_detections.csv
│   └── realtime_parking_changes.csv
└── uploads/                   # User uploaded files
```

## 🔌 API Endpoints

### Real-Time Detection
- `POST /api/realtime/plate-detect` - Detect license plates from frame
- `POST /api/realtime/parking-detect` - Detect parking space occupancy
- `GET /api/realtime/plates` - Get recent plate detections
- `GET /api/realtime/dashboard` - Get dashboard statistics

### Annotation Management
- `POST /api/annotations/save` - Save parking space annotations
- `GET /api/annotations/list` - List saved annotations
- `GET /api/annotations/load/{name}` - Load specific annotation

### Logs
- `GET /api/logs/parking-changes` - View parking change logs
- `GET /api/logs/plate-detections` - View plate detection logs
- `GET /api/logs/download/parking-changes` - Download parking logs
- `GET /api/logs/download/plate-detections` - Download plate logs

## 📊 Log Files

All detections are automatically logged to:
- `results/all_plate_detections.csv` - All license plate detections
- `results/realtime_parking_changes.csv` - Parking space state changes

## 🐛 Troubleshooting

### Port Already in Use
The server automatically finds the next available port. Check console output for the actual port number.

### Camera Not Working
- Grant camera permissions in your browser
- Try a different browser (Chrome, Firefox, Safari)
- Ensure no other application is using the camera

### Model File Not Found
- Verify `npr/license_plate_best.pt` exists
- The PSD1 model downloads automatically on first run

### Module Import Errors
Make sure you're running from the project root directory:
```bash
cd /path/to/npr_and_psd
python3 run_integrated.py
```

## 📝 Documentation

- [Quick Start Guide](HOW_TO_RUN.md) - Detailed setup instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)
- [NPR Module README](npr/README.md) - License plate detection details
- [PSD1 Module README](psd1/README.md) - Parking space detection details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available for use.

## 👤 Author

**Satwik Thakur**

- GitHub: [@SatwikThakur07](https://github.com/SatwikThakur07)

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- EasyOCR for text recognition
- FastAPI for the web framework

