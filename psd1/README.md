# Parking Lot Monitoring System

A comprehensive Python application for real-time parking space detection and occupancy tracking using computer vision and deep learning.

## Features

- **Multi-Input Support**: Process video files (MP4/AVI), webcam feeds, or RTSP streams
- **Vehicle Detection**: Uses YOLOv8 for accurate vehicle detection (cars, trucks, motorcycles, buses)
- **Parking Space Management**: Define custom parking spaces using polygon annotations
- **Real-time Tracking**: Monitor occupancy changes with temporal smoothing to handle flickering
- **Comprehensive Logging**: Track state changes, compute metrics (turnover rate, peak hours, occupancy duration)
- **Visualization**: Real-time display with color-coded spaces (green=empty, red=occupied)
- **Web Dashboard**: Optional Flask-based web server for remote monitoring
- **Export Capabilities**: Export metrics to JSON and CSV formats

## Requirements

- Python 3.8 or higher
- OpenCV 4.8+
- NumPy 1.24+
- Ultralytics (YOLOv8)
- Pandas 2.0+
- Flask 2.3+ (for web server)
- Matplotlib 3.7+ (for metrics visualization)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. YOLOv8 model will be automatically downloaded on first run (requires internet connection)

## Quick Start

### 1. Annotate Parking Spaces

First, you need to define your parking spaces. Use the annotation tool:

```bash
python annotate_spaces.py path/to/video_or_image.jpg --output spaces.json
```

This opens an interactive window where you can:
- Click to draw polygon points around each parking space
- Press ENTER to finish a polygon
- Press 'd' to delete the last space
- Press 's' to save and exit

Alternatively, you can manually edit `spaces.json` or use the sample configuration.

### 2. Run Analysis

**Process a video file:**
```bash
python parking_analyzer.py --video input.mp4 --config spaces.json --log changes.csv
```

**Use webcam:**
```bash
python parking_analyzer.py --webcam 0 --config spaces.json
```

**Process RTSP stream:**
```bash
python parking_analyzer.py --rtsp rtsp://camera-ip:port/stream --config spaces.json
```

**With web server (runs on http://localhost:5000):**
```bash
python parking_analyzer.py --video input.mp4 --config spaces.json --web-server
```

## Command Line Options

```
Required:
  --video PATH          Path to input video file
  --webcam [INDEX]      Use webcam (optional camera index, default: 0)
  --rtsp URL            RTSP stream URL
  --config PATH         Path to parking spaces JSON config file

Optional:
  --output PATH         Path to save output video (video input only)
  --log PATH            Path to CSV log file for state changes
  --export-dir DIR      Directory for exporting metrics (default: output)
  --confidence FLOAT    Detection confidence threshold 0-1 (default: 0.5)
  --min-occupancy FLOAT Minimum occupancy ratio 0-1 (default: 0.3)
  --fps-limit INT       Maximum processing FPS, 0=unlimited (default: 30)
  --simple-detector     Use simple background subtraction (no YOLO)
  --device DEVICE       YOLO device: cpu, cuda, mps (default: cpu)
  --no-display          Disable live display window
```

## Configuration File Format

The parking spaces configuration is a JSON file with the following structure:

```json
{
  "default_min_occupancy_ratio": 0.3,
  "spaces": [
    {
      "id": 1,
      "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
      "min_occupancy_ratio": 0.3
    },
    ...
  ]
}
```

- `id`: Unique identifier for the parking space
- `polygon`: List of [x, y] coordinates defining the space boundary (minimum 3 points)
- `min_occupancy_ratio`: Minimum area ratio (0-1) of vehicle overlap to consider space occupied

## Architecture

The system is modular and consists of:

- **parking_analyzer.py**: Main application with CLI and video processing
- **parking_space.py**: Parking space management and state tracking
- **vehicle_detector.py**: YOLOv8 wrapper for vehicle detection
- **config_manager.py**: Configuration file loading/saving
- **logger.py**: State change logging and metrics computation
- **visualizer.py**: Real-time visualization and display
- **web_server.py**: Optional Flask web server for remote monitoring
- **annotate_spaces.py**: Interactive tool for annotating parking spaces

## Performance Optimization

- **Frame Rate Limiting**: Use `--fps-limit` to control processing speed
- **GPU Acceleration**: Use `--device cuda` for NVIDIA GPUs or `--device mps` for Apple Silicon
- **Simple Detector**: Use `--simple-detector` for faster processing (less accurate)
- **Confidence Threshold**: Lower `--confidence` for more detections (may increase false positives)

## Output Files

The system generates several output files:

1. **State Change Log** (`--log`): CSV file with timestamped state changes
2. **Metrics JSON** (`output/metrics_*.json`): Comprehensive metrics and history
3. **Metrics CSV** (`output/metrics_*.csv`): Time-series occupancy data
4. **Output Video** (`--output`): Annotated video with overlays

## Metrics Computed

- **Turnover Rate**: Number of state changes per hour
- **Average Occupancy Duration**: How long spaces stay occupied
- **Peak Hours**: Time periods with highest occupancy rates
- **Real-time Counts**: Empty vs. occupied spaces

## Edge Cases Handled

- **Multi-vehicle in one space**: Treated as occupied
- **Partial occlusions**: Uses area-based intersection ratio
- **Lighting changes**: CLAHE enhancement for low-light conditions
- **Flickering**: Temporal smoothing with 5-frame window
- **Slow-moving vehicles**: State persistence prevents false negatives

## Web Server API

If using the web server, the following endpoints are available:

- `GET /`: Dashboard HTML page
- `GET /api/status`: Current parking lot status (JSON)
- `GET /api/spaces`: Detailed space information (JSON)
- `GET /api/metrics`: Computed metrics (JSON)
- `GET /api/changes`: Recent state changes (JSON)

## Troubleshooting

**YOLOv8 not found:**
```bash
pip install ultralytics
```

**Camera not working:**
- Check camera permissions
- Try different camera index: `--webcam 1`

**Poor detection accuracy:**
- Adjust `--confidence` threshold
- Increase `--min-occupancy` ratio
- Ensure good lighting conditions
- Use GPU acceleration if available

**Performance issues:**
- Reduce `--fps-limit`
- Use `--simple-detector` for faster processing
- Resize input video to lower resolution

## Example Workflow

1. **Record or obtain parking lot video**
2. **Annotate spaces**: `python annotate_spaces.py parking_lot.mp4 --output my_spaces.json`
3. **Run analysis**: `python parking_analyzer.py --video parking_lot.mp4 --config my_spaces.json --log results.csv`
4. **Review metrics**: Check `output/metrics_*.json` and `output/metrics_*.csv`
5. **Deploy live**: `python parking_analyzer.py --webcam 0 --config my_spaces.json`

## Extensibility

The modular design allows easy extensions:

- **Swap detectors**: Replace YOLOv8 with SSD, Faster R-CNN, etc. in `vehicle_detector.py`
- **Add prediction**: Implement LSTM-based occupancy prediction
- **IoT integration**: Add MQTT publisher for real-time alerts
- **Database storage**: Replace CSV logging with database backend
- **Multi-camera**: Extend to handle multiple camera feeds

## License

This project is provided as-is for educational and commercial use.

## Contributing

Contributions are welcome! Areas for improvement:
- Additional vehicle detection models
- Better handling of camera shake/motion
- Machine learning-based space detection
- Mobile app integration
- Cloud deployment guides

## Support

For issues or questions, please check:
1. Configuration file format
2. Video/camera compatibility
3. Dependencies installation
4. System requirements (CPU/GPU)

---

**Note**: This system is designed for static camera setups. For moving cameras, additional stabilization (optical flow) may be required.

