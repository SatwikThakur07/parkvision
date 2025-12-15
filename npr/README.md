# License Plate Detection Service

A production-ready license plate detection and recognition system using YOLO and EasyOCR. This service can process video files to detect and recognize UK-style license plates.

## Features

- 🚗 Real-time license plate detection using YOLO
- 📝 OCR text recognition with EasyOCR
- 🎥 Video processing with frame-by-frame analysis
- 📊 Detection results export (JSON & CSV)
- 🌐 REST API for video processing
- 🐳 Docker support for easy deployment
- 📈 Comprehensive logging and error handling

## Project Structure

```
number_plate_detection/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logger.py           # Logging setup
│   ├── plate_processor.py  # Core detection logic
│   ├── video_processor.py  # Video processing
│   └── api.py              # FastAPI REST API
├── main.py                 # Original script (legacy)
├── run_api.py              # API server entry point
├── run_cli.py              # CLI interface
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Installation

### Local Development

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables** (optional)
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Ensure model file exists**
   - Make sure `license_plate_best.pt` is in the project root

## Usage

### CLI Mode

Process a video file directly:

```bash
python run_cli.py input_video.mp4

# With options
python run_cli.py input_video.mp4 -o output.mp4 --preview
```

Options:
- `-o, --output`: Specify output video path
- `--no-detections`: Don't save detection files
- `--preview`: Show preview window during processing

### API Mode

1. **Start the API server**
```bash
python run_api.py
```

The API will be available at `http://localhost:8000`

2. **API Endpoints**

   - `GET /` - Service information
   - `GET /health` - Health check
   - `POST /api/v1/process-video` - Upload and process video
   - `GET /api/v1/job/{job_id}` - Get job status
   - `GET /api/v1/job/{job_id}/download` - Download processed video
   - `GET /api/v1/detections/{job_id}` - Get detection results

3. **Example API Usage**

   Upload video:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/process-video" \
        -F "file=@input_video.mp4"
   ```

   Check job status:
   ```bash
   curl "http://localhost:8000/api/v1/job/{job_id}"
   ```

   Download results:
   ```bash
   curl "http://localhost:8000/api/v1/job/{job_id}/download" -o output.mp4
   ```

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and start services**
```bash
docker-compose up -d
```

2. **View logs**
```bash
docker-compose logs -f
```

3. **Stop services**
```bash
docker-compose down
```

### Using Docker directly

1. **Build image**
```bash
docker build -t license-plate-detection .
```

2. **Run container**
```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/license_plate_best.pt:/app/license_plate_best.pt \
  --name plate-detection \
  license-plate-detection
```

## Configuration

Configuration can be set via environment variables or `.env` file:

- `YOLO_MODEL_PATH`: Path to YOLO model file (default: `license_plate_best.pt`)
- `CONFIDENCE_THRESHOLD`: Detection confidence threshold (default: `0.3`)
- `GPU_ENABLED`: Enable GPU for YOLO (default: `true`)
- `OCR_GPU_ENABLED`: Enable GPU for OCR (default: `true`)
- `API_HOST`: API host address (default: `0.0.0.0`)
- `API_PORT`: API port (default: `8000`)
- `MAX_UPLOAD_SIZE_MB`: Maximum upload size in MB (default: `500`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Output Files

The service generates:

1. **Annotated Video** (`outputs/output_*.mp4`)
   - Video with bounding boxes and plate text overlays

2. **Detection JSON** (`outputs/detected_plates_*.json`)
   - Structured data with all detections including:
     - Plate numbers
     - Frame numbers and timestamps
     - Confidence scores
     - Bounding box coordinates

3. **Detection CSV** (`outputs/detected_plates_*.csv`)
   - Spreadsheet-friendly format for analysis

## Production Deployment

### Recommended Setup

1. **Use a reverse proxy** (nginx/traefik) in front of the API
2. **Use a proper job queue** (Redis + Celery) instead of in-memory storage
3. **Add database** for job persistence and detection history
4. **Set up monitoring** (Prometheus, Grafana)
5. **Use GPU-enabled containers** for better performance
6. **Implement authentication** for API endpoints
7. **Add rate limiting** to prevent abuse

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests (create as needed).

## Troubleshooting

### GPU Issues

If GPU is not available, set:
```bash
GPU_ENABLED=false
OCR_GPU_ENABLED=false
```

### Memory Issues

For large videos, consider:
- Processing in batches
- Reducing video resolution
- Using lower confidence threshold

### Model Loading

First run may take time to download EasyOCR models. Ensure internet connection.

## License

[Add your license here]

## Contributing

[Add contribution guidelines]

## Support

[Add support information]

