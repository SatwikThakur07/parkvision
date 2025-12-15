# Project Structure

## Core Modules

### `parking_analyzer.py`
Main application entry point with CLI interface. Handles:
- Video/webcam/RTSP input processing
- Frame-by-frame analysis loop
- Integration of all modules
- Performance tracking (FPS)
- Result export

### `parking_space.py`
Parking space management:
- `ParkingSpace` class: Individual space with polygon boundaries
- `ParkingSpaceManager` class: Manages multiple spaces
- State tracking (empty/occupied)
- Occupancy detection using intersection ratios
- Temporal smoothing for flicker reduction

### `vehicle_detector.py`
Vehicle detection wrapper:
- `VehicleDetector`: YOLOv8 integration
- `SimpleVehicleDetector`: Fallback background subtraction
- Filters for vehicle classes only (car, truck, bus, motorcycle)
- Bounding box and centroid extraction

### `config_manager.py`
Configuration management:
- Load/save parking space definitions from JSON
- Create sample grid-based configurations
- Polygon validation

### `logger.py`
Logging and metrics:
- State change logging to CSV
- Metrics computation (turnover rate, peak hours, occupancy duration)
- JSON/CSV export
- Time-series data tracking

### `visualizer.py`
Real-time visualization:
- Draw parking space polygons with color coding
- Overlay statistics (counts, occupancy rate, FPS)
- Vehicle detection bounding boxes
- Legend and labels

### `web_server.py`
Optional Flask web server:
- RESTful API endpoints
- HTML dashboard
- Real-time status updates
- Remote monitoring capability

## Utility Scripts

### `annotate_spaces.py`
Interactive tool for drawing parking space polygons:
- Mouse-based polygon drawing
- Visual feedback
- Save to JSON configuration

### `visualize_metrics.py`
Post-analysis visualization:
- Occupancy over time graphs
- Occupancy rate charts
- State changes timeline
- Summary statistics

## Configuration Files

### `spaces.json`
Sample parking space configuration:
- Polygon definitions
- Space IDs
- Occupancy thresholds

### `requirements.txt`
Python dependencies:
- OpenCV
- NumPy
- Ultralytics (YOLOv8)
- Pandas
- Flask
- Matplotlib

## Documentation

### `README.md`
Comprehensive documentation:
- Features overview
- Installation instructions
- Usage examples
- API reference
- Troubleshooting

### `QUICKSTART.md`
Quick start guide:
- 5-minute setup
- Common use cases
- Performance tips

## Data Flow

```
Video Input → Preprocessing → Vehicle Detection → Space Matching → 
State Update → Logging → Visualization → Output
```

## Key Design Decisions

1. **Modular Architecture**: Each component is independent and swappable
2. **Polygon-based Spaces**: Flexible space definitions, not limited to rectangles
3. **Temporal Smoothing**: Prevents flickering from detection noise
4. **Multiple Input Sources**: Video files, webcam, RTSP streams
5. **Comprehensive Logging**: Full audit trail of state changes
6. **Performance Options**: Configurable FPS, GPU support, simple detector fallback

## Extension Points

- **Detection Models**: Swap YOLOv8 for other models in `vehicle_detector.py`
- **Storage Backend**: Replace CSV with database in `logger.py`
- **Visualization**: Add custom overlays in `visualizer.py`
- **API Integration**: Add MQTT/HTTP publishers in `logger.py`
- **Multi-camera**: Extend `parking_analyzer.py` for parallel processing

