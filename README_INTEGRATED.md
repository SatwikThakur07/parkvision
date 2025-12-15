# Integrated Vehicle Monitoring System

A unified web interface combining License Plate Detection (NPR) and Parking Space Monitoring (PSD1) into a single, easy-to-use frontend.

## Features

- 🚗 **License Plate Detection**: Upload videos to detect and recognize license plates
- 🅿️ **Parking Space Monitoring**: Track parking space occupancy with detailed metrics
- 🌐 **Modern Web Interface**: Beautiful, responsive UI with real-time progress tracking
- 📊 **Comprehensive Results**: View statistics, download results, and export data

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_integrated.txt
```

### 2. Ensure Model Files Exist

- **NPR**: Make sure `npr/license_plate_best.pt` exists
- **PSD1**: YOLOv8 model will be downloaded automatically on first run

### 3. Start the Server

```bash
python run_integrated.py
```

Or directly:

```bash
python integrated_api.py
```

### 4. Access the Frontend

Open your browser and navigate to:
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage

### License Plate Detection (NPR)

1. Click on the "License Plate Detection" tab
2. Upload a video file (MP4, AVI, MOV)
3. Click "Start Processing"
4. Monitor progress in real-time
5. View results:
   - Total detections
   - Unique plates found
   - List of detected plates
6. Download:
   - Annotated video with bounding boxes
   - Detection data in JSON format

### Parking Space Monitoring (PSD1)

1. **First Time Setup**: Create parking space configuration
   ```bash
   cd psd1
   python annotate_spaces.py your_video_frame.jpg --output spaces.json
   ```

2. **Process Video**:
   - Click on the "Parking Space Monitoring" tab
   - Upload your video file
   - Upload the parking spaces configuration JSON
   - Adjust parameters (confidence, occupancy ratio, FPS limit)
   - Click "Start Processing"

3. **View Results**:
   - Current occupancy status (empty/occupied)
   - Total spaces and occupancy rate
   - Metrics summary (turnover rate, average duration)
   - Download metrics in JSON or CSV format

## API Endpoints

### NPR (License Plate Detection)

- `POST /api/npr/process-video` - Upload and process video
- `GET /api/npr/job/{job_id}` - Get job status
- `GET /api/npr/job/{job_id}/download` - Download processed video
- `GET /api/npr/detections/{job_id}` - Get detection results

### PSD1 (Parking Space Monitoring)

- `POST /api/psd1/upload-config` - Upload parking spaces config
- `POST /api/psd1/process-video` - Upload and process video
- `GET /api/psd1/job/{job_id}` - Get job status
- `GET /api/psd1/metrics/{job_id}` - Get parking metrics
- `GET /api/psd1/download/{job_id}` - Download results

## Configuration

### NPR Settings

Can be configured via environment variables (see `npr/src/config.py`):
- `YOLO_MODEL_PATH`: Path to YOLO model
- `CONFIDENCE_THRESHOLD`: Detection confidence (default: 0.3)
- `GPU_ENABLED`: Enable GPU for YOLO
- `OCR_GPU_ENABLED`: Enable GPU for OCR

### PSD1 Settings

Configured via API parameters:
- `confidence`: Vehicle detection confidence (0.0-1.0)
- `min_occupancy`: Minimum occupancy ratio (0.0-1.0)
- `fps_limit`: Maximum processing FPS (0 = unlimited)
- `device`: Processing device ('cpu', 'cuda', 'mps')

## Directory Structure

```
npr_and_psd/
├── integrated_api.py          # Main API server
├── run_integrated.py          # Startup script
├── requirements_integrated.txt
├── static/
│   └── index.html             # Frontend UI
├── uploads/                    # Uploaded files
├── results/                    # Processing results
├── npr/                        # NPR project files
└── psd1/                       # PSD1 project files
```

## Troubleshooting

### Port Already in Use

If port 8000 is occupied, modify `run_integrated.py` to use a different port:

```python
uvicorn.run(..., port=8001)
```

### Model Files Not Found

- **NPR**: Ensure `npr/license_plate_best.pt` exists
- **PSD1**: YOLOv8 model downloads automatically on first run

### GPU Issues

If GPU is not available, the system will fall back to CPU. For NPR, set:
```bash
export GPU_ENABLED=false
export OCR_GPU_ENABLED=false
```

### Large Video Files

For large videos:
- Increase upload size limits in the API
- Process in smaller chunks
- Use lower FPS limits

## Development

### Frontend Customization

Edit `static/index.html` to customize the UI:
- Colors and styling
- Layout and components
- Additional features

### API Extensions

Extend `integrated_api.py` to add:
- Authentication
- User management
- Database storage
- Additional endpoints

## Production Deployment

For production use:

1. **Use a production ASGI server**:
   ```bash
   gunicorn integrated_api:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Add reverse proxy** (nginx/traefik)

3. **Implement authentication** for API endpoints

4. **Use database** instead of in-memory job storage

5. **Add monitoring** (Prometheus, Grafana)

6. **Set up logging** to files

## License

[Add your license here]

## Support

For issues or questions:
1. Check the individual project READMEs (`npr/README.md`, `psd1/README.md`)
2. Review API documentation at `/docs`
3. Check logs in the console output

