# Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify installation
python -c "import cv2, ultralytics; print('OK')"
```

## Basic Usage (3 steps)

### Step 1: Annotate Parking Spaces

Use a frame from your video or a screenshot:

```bash
python annotate_spaces.py parking_lot_frame.jpg --output my_spaces.json
```

**Interactive controls:**
- Click to add polygon points
- Press **ENTER** to finish a polygon
- Press **'d'** to delete last space
- Press **'s'** to save

### Step 2: Run Analysis

```bash
python parking_analyzer.py --video parking_lot.mp4 --config my_spaces.json
```

### Step 3: View Results

Results are saved in the `output/` directory:
- `metrics_*.json` - Full metrics data
- `metrics_*.csv` - Time-series data
- State changes are printed to console

## Common Use Cases

### Process Video File
```bash
python parking_analyzer.py \
    --video input.mp4 \
    --config spaces.json \
    --log changes.csv \
    --output annotated_output.mp4
```

### Live Webcam Monitoring
```bash
python parking_analyzer.py \
    --webcam 0 \
    --config spaces.json \
    --log live_changes.csv
```

### RTSP Camera Stream
```bash
python parking_analyzer.py \
    --rtsp rtsp://192.168.1.100:554/stream \
    --config spaces.json
```

### With Web Dashboard
```bash
python parking_analyzer.py \
    --video input.mp4 \
    --config spaces.json \
    --web-server \
    --web-port 5000
```

Then open: http://localhost:5000

### Generate Sample Config (for testing)
```python
from config_manager import ConfigManager
ConfigManager.create_sample_config('sample_spaces.json', num_spaces=20, 
                                  image_width=1920, image_height=1080)
```

## Visualization

After running analysis, visualize metrics:

```bash
python visualize_metrics.py output/metrics_20240101_120000.json
```

This generates:
- Occupancy over time graph
- Occupancy rate graph
- State changes timeline

## Performance Tips

1. **For faster processing:**
   ```bash
   --fps-limit 10 --simple-detector
   ```

2. **For better accuracy:**
   ```bash
   --confidence 0.3 --min-occupancy 0.2
   ```

3. **For GPU acceleration:**
   ```bash
   --device cuda  # NVIDIA GPU
   --device mps   # Apple Silicon
   ```

## Troubleshooting

**Problem:** YOLOv8 not found
```bash
pip install ultralytics
```

**Problem:** Camera not working
- Try different index: `--webcam 1`
- Check camera permissions

**Problem:** Poor detection
- Lower confidence: `--confidence 0.3`
- Adjust occupancy ratio: `--min-occupancy 0.2`
- Ensure good lighting

## Example Workflow

```bash
# 1. Annotate spaces on a sample frame
python annotate_spaces.py sample_frame.jpg -o spaces.json

# 2. Run analysis on full video
python parking_analyzer.py --video lot_video.mp4 --config spaces.json --log results.csv

# 3. Visualize results
python visualize_metrics.py output/metrics_*.json

# 4. Check CSV log
cat results.csv
```

## Next Steps

- Customize parking space polygons in `spaces.json`
- Adjust detection parameters (`--confidence`, `--min-occupancy`)
- Set up web server for remote monitoring
- Integrate with your own systems via API

For detailed documentation, see `README.md`.

