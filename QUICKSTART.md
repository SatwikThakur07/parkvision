# Quick Start Guide - Integrated System

Get up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements_integrated.txt
```

## Step 2: Verify Model Files

### For License Plate Detection (NPR):
Make sure the YOLO model exists:
```bash
ls npr/license_plate_best.pt
```

If it doesn't exist, you'll need to obtain the trained model file.

### For Parking Space Monitoring (PSD1):
The YOLOv8 model will be downloaded automatically on first run.

## Step 3: Start the Server

```bash
python run_integrated.py
```

You should see:
```
============================================================
Starting Integrated Vehicle Monitoring System
============================================================
Access the frontend at: http://localhost:8000
API documentation at: http://localhost:8000/docs
============================================================
```

## Step 4: Open the Frontend

Open your web browser and go to:
**http://localhost:8000**

## Using License Plate Detection

1. Click the **"License Plate Detection"** tab
2. Click **"Choose Video File"** or drag & drop a video
3. Click **"Start Processing"**
4. Wait for processing to complete
5. View results and download files

## Using Parking Space Monitoring

### First Time: Create Configuration

1. Extract a frame from your video or take a screenshot
2. Run the annotation tool:
   ```bash
   cd psd1
   python annotate_spaces.py your_frame.jpg --output my_spaces.json
   ```
3. In the annotation window:
   - Click to draw polygon points around each parking space
   - Press **ENTER** to finish a polygon
   - Press **'d'** to delete last space
   - Press **'s'** to save

### Process Video

1. Click the **"Parking Space Monitoring"** tab
2. Upload your video file
3. Upload the configuration JSON file (e.g., `my_spaces.json`)
4. Adjust settings if needed:
   - **Confidence**: 0.5 (default) - lower = more detections
   - **Min Occupancy**: 0.2 (default) - minimum overlap to consider occupied
   - **FPS Limit**: 30 (default) - processing speed limit
5. Click **"Start Processing"**
6. View metrics and download results

## Troubleshooting

### Port 8000 Already in Use

Edit `run_integrated.py` and change the port:
```python
uvicorn.run(..., port=8001)
```

### Module Not Found Errors

Make sure you're in the project root directory:
```bash
cd /path/to/npr_and_psd
python run_integrated.py
```

### GPU Issues

The system works on CPU by default. For GPU:
- Install CUDA for NVIDIA GPUs
- Set `device='cuda'` in the API (or modify the frontend)

### Large Videos

For very large videos:
- Use lower FPS limits
- Process shorter clips
- Ensure sufficient disk space in `uploads/` and `results/` directories

## Next Steps

- Read `README_INTEGRATED.md` for detailed documentation
- Check API documentation at http://localhost:8000/docs
- Explore the individual project READMEs for advanced features

