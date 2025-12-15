# How to Run the Integrated System

## Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
cd /Users/user/Downloads/npr_and_psd
pip install -r requirements_integrated.txt
```

**Note:** If you encounter permission errors, use:
```bash
pip install --user -r requirements_integrated.txt
```

### Step 2: Verify Model Files

The system needs these model files:
- ✅ `npr/license_plate_best.pt` - License plate detection model (should already exist)
- ✅ `psd1/yolov8n.pt` - Vehicle detection model (downloads automatically on first run)

### Step 3: Start the Server

```bash
python3 run_integrated.py
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

## Access the Application

1. **Web Interface:** Open your browser and go to:
   - **http://localhost:8000**

2. **API Documentation:** View interactive API docs at:
   - **http://localhost:8000/docs**

## Using the System

### For Real-Time Detection (Webcam):

1. **Start Camera:**
   - Click "Start Camera" button
   - Allow browser camera access when prompted

2. **Annotate Parking Spaces (First Time Only):**
   - Click "Capture Frame" to freeze the current frame
   - Click "Annotate Spaces" to enter annotation mode
   - Draw polygons around each parking space by clicking points
   - Press **S** or **Enter** to save current polygon
   - Press **A** or click "Save All & Finish" to complete annotation
   - The system will automatically start detecting parking occupancy

3. **View Results:**
   - **Parking Layout:** Shows spaces in real-time (green = available, red = occupied)
   - **Detected Plates:** Lists all detected license plates
   - **Dashboard Stats:** Shows total spaces, available, occupied, and today's entries

### For Video File Processing:

1. **License Plate Detection:**
   - Go to "License Plate Detection" tab
   - Upload a video file
   - Click "Start Processing"
   - Download results when complete

2. **Parking Space Monitoring:**
   - Go to "Parking Space Monitoring" tab
   - Upload video file
   - Upload parking space configuration (JSON file)
   - Click "Start Processing"
   - View metrics and download results

## Troubleshooting

### Port Already in Use

If port 8000 is busy, the script will automatically use the next available port (8001, 8002, etc.). Check the console output for the actual port number.

### Camera Not Working

- Make sure you've granted camera permissions in your browser
- Try a different browser (Chrome, Firefox, Safari)
- Check if another application is using the camera

### Model File Not Found

If you see `FileNotFoundError` for `license_plate_best.pt`:
- Verify the file exists: `ls npr/license_plate_best.pt`
- The file should be in the `npr/` directory

### Module Import Errors

Make sure you're running from the project root:
```bash
cd /Users/user/Downloads/npr_and_psd
python3 run_integrated.py
```

### Dependencies Installation Issues

If you have issues installing dependencies:
```bash
# Try upgrading pip first
pip install --upgrade pip

# Then install requirements
pip install -r requirements_integrated.txt
```

## Log Files

The system creates log files in the `results/` directory:
- `results/all_plate_detections.csv` - All detected license plates
- `results/realtime_parking_changes.csv` - Parking space state changes

You can also access logs via API:
- `GET /api/logs/parking-changes` - View parking change logs
- `GET /api/logs/plate-detections` - View plate detection logs

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the server.

