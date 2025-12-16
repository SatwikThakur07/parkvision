#!/usr/bin/env python3
"""
Integrated API Server for NPR and PSD1
Combines license plate detection and parking space monitoring in one API
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import uuid
import base64
from datetime import datetime
from pathlib import Path
import threading
import sys

# Debug logging setup (container-safe)
DEBUG_DIR = Path(__file__).parent / ".cursor"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_LOG = DEBUG_DIR / "debug.log"

def safe_debug(message: str, data: dict | None = None, location: str = "integrated_api"):
    """Write lightweight debug info; ignore all failures."""
    if data is None:
        data = {}
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "pre-fix",
                "hypothesisId": "A",
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }) + "\n")
    except Exception:
        pass

# Initial debug log
safe_debug("Before sys.path manipulation", {"current_paths": sys.path[:3], "base_dir": str(Path(__file__).parent)}, "integrated_api.py:22")

# Add both project directories to path
# FIX: Add 'npr' instead of 'npr/src' so 'src.config' imports resolve correctly
base_dir = Path(__file__).parent
npr_path = str(base_dir / "npr")
psd1_path = str(base_dir / "psd1")

safe_debug("Path values before insertion (FIXED)", {"npr_path": npr_path, "psd1_path": psd1_path, "npr_path_exists": Path(npr_path).exists()}, "integrated_api.py:30")

sys.path.insert(0, npr_path)  # FIX: Changed from npr/src to npr
sys.path.insert(0, psd1_path)

safe_debug("After sys.path insertion (FIXED)", {"first_3_paths": sys.path[:3]}, "integrated_api.py:37")

# Import NPR modules
try:
    safe_debug("Attempting to import plate_processor (FIXED)", {}, "integrated_api.py:42")
    from src.plate_processor import PlateProcessor
    safe_debug("Successfully imported PlateProcessor", {}, "integrated_api.py:45")
except Exception as e:
    safe_debug("Failed to import PlateProcessor", {"error": str(e), "error_type": type(e).__name__}, "integrated_api.py:49")
    raise

from src.video_processor import VideoProcessor as NPRVideoProcessor
from src.config import settings as npr_settings

# Import PSD1 modules
from parking_analyzer import ParkingAnalyzer
from parking_space import ParkingSpaceManager
from logger import ParkingLogger
from config_manager import ConfigManager

app = FastAPI(
    title="Integrated Vehicle Monitoring System",
    version="2.0.0",
    description="Combined License Plate Detection and Parking Space Monitoring"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
STATIC_DIR = BASE_DIR / "static"

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Global state
npr_jobs = {}
psd1_jobs = {}


# ==================== NPR (License Plate Detection) ====================

class NPRJobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    total_detections: Optional[int] = None
    unique_plates: Optional[int] = None
    output_video: Optional[str] = None
    detection_files: Optional[dict] = None
    error: Optional[str] = None


def process_npr_video(job_id: str, video_path: str):
    """Background task for NPR video processing"""
    try:
        npr_jobs[job_id]["status"] = "processing"
        
        # Initialize processor
        processor = NPRVideoProcessor()
        
        # Process video
        output_path = str(RESULTS_DIR / f"npr_{job_id}_output.mp4")
        result = processor.process_video(
            video_path,
            output_path=output_path,
            save_detections=True,
            show_preview=False
        )
        
        npr_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "total_detections": result["total_detections"],
            "unique_plates": result["unique_plates"],
            "output_video": result["output_video"],
            "detection_files": result.get("detection_files", {})
        })
        
    except Exception as e:
        npr_jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })


@app.post("/api/npr/process-video")
async def npr_process_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process video for license plate detection"""
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        video_path = UPLOAD_DIR / f"npr_{job_id}_{file.filename}"
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create job entry
        npr_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "input_file": file.filename
        }
        
        # Start background processing
        background_tasks.add_task(process_npr_video, job_id, str(video_path))
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Video processing started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/npr/job/{job_id}", response_model=NPRJobStatus)
async def npr_get_job_status(job_id: str):
    """Get NPR job status"""
    if job_id not in npr_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return NPRJobStatus(**npr_jobs[job_id])


@app.get("/api/npr/job/{job_id}/download")
async def npr_download_output(job_id: str):
    """Download processed video"""
    if job_id not in npr_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = npr_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    output_path = job.get("output_video")
    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"npr_output_{job_id}.mp4"
    )


@app.get("/api/npr/detections/{job_id}")
async def npr_get_detections(job_id: str):
    """Get detection results"""
    if job_id not in npr_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = npr_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    detection_files = job.get("detection_files", {})
    json_file = detection_files.get("json")
    
    if not json_file or not Path(json_file).exists():
        raise HTTPException(status_code=404, detail="Detection file not found")
    
    with open(json_file, 'r') as f:
        detections = json.load(f)
    
    return JSONResponse(content=detections)


# ==================== PSD1 (Parking Space Detection) ====================

class PSD1JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    current_frame: int
    total_frames: int
    empty_count: int
    occupied_count: int
    total_spaces: Optional[int] = None
    error: Optional[str] = None


def process_psd1_video(job_id: str, video_path: str, config_path: str,
                      confidence: float, min_occupancy: float, fps_limit: int,
                      use_simple_detector: bool, device: str):
    """Background task for PSD1 video processing"""
    try:
        psd1_jobs[job_id]["status"] = "processing"
        
        # Initialize analyzer
        analyzer = ParkingAnalyzer(
            config_path=config_path,
            confidence_threshold=confidence,
            min_occupancy_ratio=min_occupancy,
            fps_limit=fps_limit,
            use_simple_detector=use_simple_detector,
            device=device
        )
        
        # Setup logger
        log_file = RESULTS_DIR / f"psd1_{job_id}_changes.csv"
        analyzer.logger = ParkingLogger(str(log_file))
        
        # Get video properties
        import cv2
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        psd1_jobs[job_id]["total_frames"] = total_frames
        
        # Process video
        cap = cv2.VideoCapture(video_path)
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_idx += 1
            timestamp = datetime.now()
            
            # Process frame
            analyzer.process_frame(frame, timestamp)
            
            # Update status every 10 frames
            if frame_idx % 10 == 0:
                empty, occupied = analyzer.space_manager.get_counts()
                psd1_jobs[job_id].update({
                    "current_frame": frame_idx,
                    "progress": (frame_idx / total_frames) * 100 if total_frames > 0 else 0,
                    "empty_count": empty,
                    "occupied_count": occupied,
                    "total_spaces": analyzer.space_manager.total_spaces
                })
        
        # Final update
        empty, occupied = analyzer.space_manager.get_counts()
        psd1_jobs[job_id].update({
            "status": "completed",
            "current_frame": frame_idx,
            "progress": 100.0,
            "empty_count": empty,
            "occupied_count": occupied,
            "total_spaces": analyzer.space_manager.total_spaces
        })
        
        cap.release()
        
        # Export results
        output_dir = RESULTS_DIR / f"psd1_{job_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        analyzer.export_results(str(output_dir))
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        psd1_jobs[job_id].update({
            "status": "failed",
            "error": error_msg
        })


@app.post("/api/psd1/upload-config")
async def psd1_upload_config(file: UploadFile = File(...)):
    """Upload parking spaces configuration file"""
    global psd1_config_path, psd1_analyzer
    try:
        file_id = str(uuid.uuid4())
        config_path = UPLOAD_DIR / f"psd1_config_{file_id}_{file.filename}"
        
        with open(config_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate JSON
        try:
            json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            os.remove(config_path)
            raise HTTPException(status_code=400, detail="Invalid JSON file")
        
        # Set global config path and reset analyzer (will be lazy-loaded on next use)
        psd1_config_path = str(config_path)
        psd1_analyzer = None  # Reset so it reloads with new config
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "path": str(config_path),
            "message": "Configuration uploaded successfully. Parking analyzer will be initialized on first frame."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/psd1/process-video")
async def psd1_process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    config: UploadFile = File(...),
    confidence: float = 0.5,
    min_occupancy: float = 0.2,
    fps_limit: int = 30,
    use_simple_detector: bool = False,
    device: str = "cpu"
):
    """Upload and process video for parking space monitoring"""
    try:
        job_id = str(uuid.uuid4())
        
        # Save video
        video_path = UPLOAD_DIR / f"psd1_{job_id}_{video.filename}"
        with open(video_path, "wb") as f:
            f.write(await video.read())
        
        # Save config
        config_path = UPLOAD_DIR / f"psd1_{job_id}_{config.filename}"
        with open(config_path, "wb") as f:
            content = await config.read()
            f.write(content)
        
        # Validate config
        try:
            json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid config JSON")
        
        # Create job
        psd1_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "current_frame": 0,
            "total_frames": 0,
            "empty_count": 0,
            "occupied_count": 0
        }
        
        # Start processing
        background_tasks.add_task(
            process_psd1_video,
            job_id, str(video_path), str(config_path),
            confidence, min_occupancy, fps_limit,
            use_simple_detector, device
        )
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Video processing started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/psd1/job/{job_id}", response_model=PSD1JobStatus)
async def psd1_get_job_status(job_id: str):
    """Get PSD1 job status"""
    if job_id not in psd1_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return PSD1JobStatus(**psd1_jobs[job_id])


@app.get("/api/psd1/metrics/{job_id}")
async def psd1_get_metrics(job_id: str):
    """Get parking metrics"""
    if job_id not in psd1_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = psd1_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # Find metrics JSON
    metrics_dir = RESULTS_DIR / f"psd1_{job_id}"
    if metrics_dir.exists():
        json_files = list(metrics_dir.glob("metrics_*.json"))
        if json_files:
            with open(json_files[0], 'r') as f:
                return json.load(f)
    
    raise HTTPException(status_code=404, detail="Metrics not found")


@app.get("/api/psd1/download/{job_id}")
async def psd1_download_results(job_id: str, file_type: str = "json"):
    """Download results"""
    if job_id not in psd1_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    metrics_dir = RESULTS_DIR / f"psd1_{job_id}"
    
    if file_type == "json":
        json_files = list(metrics_dir.glob("metrics_*.json"))
        if json_files:
            return FileResponse(
                str(json_files[0]),
                media_type="application/json",
                filename=f"psd1_metrics_{job_id}.json"
            )
    elif file_type == "csv":
        csv_files = list(metrics_dir.glob("metrics_*.csv"))
        if csv_files:
            return FileResponse(
                str(csv_files[0]),
                media_type="text/csv",
                filename=f"psd1_metrics_{job_id}.csv"
            )
    
    raise HTTPException(status_code=404, detail="File not found")


# ==================== Real-time Dashboard APIs ====================

# Global state for real-time monitoring
gate_detections = []  # Store recent plate detections
parking_status = {
    "total_spaces": 0,  # Will be set from config
    "available": 0,
    "occupied": 0,
    "spaces": {}  # Individual space status
}
today_entries_count = 0  # Will be incremented with each plate detection

# Persistent logging for number plates
PLATE_LOG_CSV = RESULTS_DIR / "all_plate_detections.csv"
PLATE_LOG_JSON = RESULTS_DIR / "all_plate_detections.jsonl"

# Initialize plate log files
def init_plate_logs():
    """Initialize CSV and JSONL log files for plate detections"""
    # CSV header
    if not PLATE_LOG_CSV.exists():
        with open(PLATE_LOG_CSV, 'w', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'plate_number', 'confidence', 'direction', 'source'])
    # JSONL doesn't need header

init_plate_logs()

# Initialize processor instances (lazy loading)
npr_processor = None
psd1_analyzer = None
psd1_config_path = None  # Path to parking space configuration

def get_npr_processor():
    """Lazy load NPR processor"""
    global npr_processor
    if npr_processor is None:
        # #region agent log
        try:
            with open('/Users/user/Downloads/npr_and_psd/.cursor/debug.log', 'a') as f:
                import json
                from datetime import datetime
                f.write(json.dumps({"sessionId":"debug-session","runId":"model-path-fix","hypothesisId":"A","location":"integrated_api.py:516","message":"Starting NPR processor initialization","data":{"base_dir":str(BASE_DIR),"cwd":str(Path.cwd())},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
        except: pass
        # #endregion
        
        # Fix model path - ensure it points to the correct location
        model_path = BASE_DIR / "npr" / "license_plate_best.pt"
        
        # #region agent log
        try:
            with open('/Users/user/Downloads/npr_and_psd/.cursor/debug.log', 'a') as f:
                import json
                from datetime import datetime
                f.write(json.dumps({"sessionId":"debug-session","runId":"model-path-fix","hypothesisId":"B","location":"integrated_api.py:524","message":"Checking model path","data":{"model_path":str(model_path),"exists":model_path.exists()},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
        except: pass
        # #endregion
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found. Expected at: {model_path}")
        
        # Temporarily override the settings to use the correct path
        import os
        original_cwd = os.getcwd()
        original_path = npr_settings.yolo_model_path
        
        # #region agent log
        try:
            with open('/Users/user/Downloads/npr_and_psd/.cursor/debug.log', 'a') as f:
                import json
                from datetime import datetime
                f.write(json.dumps({"sessionId":"debug-session","runId":"model-path-fix","hypothesisId":"C","location":"integrated_api.py:535","message":"Before chdir","data":{"original_cwd":original_cwd,"original_path":original_path,"target_dir":str(BASE_DIR / "npr")},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
        except: pass
        # #endregion
        
        try:
            # Use absolute path instead of changing directory
            # Update settings to use absolute path
            npr_settings.yolo_model_path = str(model_path)
            
            # #region agent log
            try:
                with open('/Users/user/Downloads/npr_and_psd/.cursor/debug.log', 'a') as f:
                    import json
                    from datetime import datetime
                    f.write(json.dumps({"sessionId":"debug-session","runId":"model-path-fix","hypothesisId":"D","location":"integrated_api.py:543","message":"Creating PlateProcessor","data":{"model_path_setting":npr_settings.yolo_model_path},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
            except: pass
            # #endregion
            
            npr_processor = PlateProcessor()
            
            # #region agent log
            try:
                with open('/Users/user/Downloads/npr_and_psd/.cursor/debug.log', 'a') as f:
                    import json
                    from datetime import datetime
                    f.write(json.dumps({"sessionId":"debug-session","runId":"model-path-fix","hypothesisId":"E","location":"integrated_api.py:550","message":"PlateProcessor created successfully","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
            except: pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open('/Users/user/Downloads/npr_and_psd/.cursor/debug.log', 'a') as f:
                    import json
                    from datetime import datetime
                    f.write(json.dumps({"sessionId":"debug-session","runId":"model-path-fix","hypothesisId":"F","location":"integrated_api.py:555","message":"PlateProcessor creation failed","data":{"error":str(e),"error_type":type(e).__name__},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
            except: pass
            # #endregion
            raise
        finally:
            # Restore original path setting
            npr_settings.yolo_model_path = original_path
    return npr_processor

@app.post("/api/realtime/plate-detect")
async def realtime_plate_detect(file: UploadFile = File(...)):
    """Process a single frame for plate detection (real-time)"""
    try:
        import cv2
        import numpy as np
        from io import BytesIO
        
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        # Detect plates
        processor = get_npr_processor()
        detections = processor.detect_plates(frame)
        
        # Store detections and log to files
        timestamp = datetime.now()
        for det in detections:
            detection_record = {
                "plate_number": det["plate_number"],
                "confidence": det["confidence"],
                "timestamp": timestamp.isoformat(),
                "direction": "in",  # Could be determined by position/tracking
                "source": "realtime_webcam"
            }
            gate_detections.insert(0, detection_record)
            if len(gate_detections) > 100:
                gate_detections.pop()
            
            # Log to CSV file
            import csv
            with open(PLATE_LOG_CSV, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp.isoformat(),
                    det["plate_number"],
                    det["confidence"],
                    "in",
                    "realtime_webcam"
                ])
            
            # Log to JSONL file
            with open(PLATE_LOG_JSON, 'a') as f:
                f.write(json.dumps(detection_record) + '\n')
            
            # Increment today's entries
            global today_entries_count
            today_entries_count += 1
        
        # Format detections for frontend
        formatted_detections = []
        for det in detections:
            formatted_detections.append({
                "plate_number": det.get("plate_number", ""),
                "confidence": det.get("confidence", 0.0),
                "bbox": det.get("bbox", {}),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "detections": formatted_detections,
            "count": len(formatted_detections),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/realtime/plates")
async def get_realtime_plates(limit: int = 10):
    """Get recent plate detections"""
    # Format plates for frontend compatibility
    formatted_plates = []
    for det in gate_detections[:limit]:
        formatted_plates.append({
            "plate": det.get("plate_number", ""),
            "plate_number": det.get("plate_number", ""),
            "confidence": det.get("confidence", 0.0),
            "direction": det.get("direction", "in"),
            "timestamp": det.get("timestamp", datetime.now().isoformat()),
            "time": det.get("timestamp", datetime.now().isoformat())
        })
    
    return {
        "plates": formatted_plates,
        "total": len(gate_detections),
        "today_entries": today_entries_count
    }


@app.post("/api/realtime/parking-status")
async def update_parking_status(
    available: int,
    occupied: int,
    spaces: Optional[dict] = None
):
    """Update parking space status (called by PSD1 processing)"""
    global parking_status
    parking_status.update({
        "available": available,
        "occupied": occupied,
        "total_spaces": available + occupied,
        "last_update": datetime.now().isoformat()
    })
    if spaces:
        parking_status["spaces"] = spaces
    return parking_status


def convert_config_format_if_needed(config_path: str):
    """Convert annotation format to ConfigManager format if needed"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check if conversion is needed
        needs_conversion = False
        if 'spaces' in config and len(config['spaces']) > 0:
            first_space = config['spaces'][0]
            # Check if it's in annotation format (has space_id and polygon as objects)
            if 'space_id' in first_space or (isinstance(first_space.get('polygon', [{}])[0], dict) if first_space.get('polygon') else False):
                needs_conversion = True
        
        if needs_conversion:
            print(f"Converting config format: {config_path}")
            converted_spaces = []
            for idx, space in enumerate(config.get('spaces', [])):
                # Extract polygon points
                polygon_points = []
                for point in space.get('polygon', []):
                    if isinstance(point, dict):
                        polygon_points.append([int(point.get('x', 0)), int(point.get('y', 0))])
                    elif isinstance(point, (list, tuple)) and len(point) >= 2:
                        polygon_points.append([int(point[0]), int(point[1])])
                
                # Extract space_id
                space_id_str = space.get('space_id', f'space_{idx + 1}')
                if isinstance(space_id_str, str) and space_id_str.startswith('space_'):
                    try:
                        space_id = int(space_id_str.replace('space_', ''))
                    except:
                        space_id = idx + 1
                elif isinstance(space_id_str, int):
                    space_id = space_id_str
                else:
                    space_id = idx + 1
                
                converted_space = {
                    "id": space_id,
                    "polygon": polygon_points,
                    "min_occupancy_ratio": space.get('min_occupancy_ratio', config.get('default_min_occupancy_ratio', 0.2))
                }
                converted_spaces.append(converted_space)
            
            # Update config with converted spaces
            config['spaces'] = converted_spaces
            # Remove annotation-specific fields
            config.pop('name', None)
            config.pop('created_at', None)
            
            # Save converted config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Config converted successfully: {len(converted_spaces)} spaces")
    except Exception as e:
        print(f"Warning: Could not convert config format: {e}")
        # Don't raise - let ConfigManager handle it and show the actual error


def get_psd1_analyzer():
    """Lazy load PSD1 analyzer - requires config file to be uploaded first"""
    global psd1_analyzer, psd1_config_path
    
    if psd1_analyzer is None:
        if psd1_config_path is None or not Path(psd1_config_path).exists():
            raise HTTPException(
                status_code=400, 
                detail="Parking space configuration not loaded. Please upload a configuration file first."
            )
        
        try:
            # Convert config format if needed before loading
            convert_config_format_if_needed(psd1_config_path)
            
            psd1_analyzer = ParkingAnalyzer(
                config_path=psd1_config_path,
                confidence_threshold=0.5,
                min_occupancy_ratio=0.2,
                fps_limit=30,
                use_simple_detector=False,
                device='cpu'
            )
            # Setup logger for real-time changes
            log_file = RESULTS_DIR / "realtime_parking_changes.csv"
            psd1_analyzer.logger = ParkingLogger(str(log_file))
        except Exception as e:
            import traceback
            error_detail = f"Failed to initialize parking analyzer: {str(e)}"
            print(f"PSD1 Analyzer initialization error: {error_detail}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )
    
    return psd1_analyzer


@app.post("/api/realtime/parking-detect")
async def realtime_parking_detect(file: UploadFile = File(...)):
    """Process a single frame for parking space detection (real-time)"""
    try:
        import cv2
        import numpy as np
        from io import BytesIO
        
        # Check if config is loaded before processing
        global psd1_config_path
        if psd1_config_path is None or not Path(psd1_config_path).exists():
            raise HTTPException(
                status_code=400, 
                detail="Parking space configuration not loaded. Please annotate and save parking spaces first."
            )
        
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        # Get analyzer (will raise error if config not loaded)
        analyzer = get_psd1_analyzer()
        
        # Process frame
        timestamp = datetime.now()
        try:
            annotated_frame = analyzer.process_frame(frame, timestamp)
        except Exception as e:
            import traceback
            error_detail = f"Error processing frame: {str(e)}"
            print(f"Frame processing error: {error_detail}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=error_detail)
        
        # Get current status
        empty, occupied = analyzer.space_manager.get_counts()
        
        # Update global parking status
        global parking_status
        parking_status.update({
            "available": empty,
            "occupied": occupied,
            "total_spaces": analyzer.space_manager.total_spaces,
            "last_update": timestamp.isoformat()
        })
        
        # Get individual space statuses
        space_statuses = {}
        for space in analyzer.space_manager.spaces:
            # Convert space_id to string for consistency (frontend expects string keys)
            space_id_key = str(space.space_id)
            # Access state directly (it's a SpaceState enum)
            state_value = space.state.value if hasattr(space.state, 'value') else str(space.state)
            # Get occupancy ratio from the space's internal tracking
            occupancy_ratio = getattr(space, 'current_occupancy_ratio', 0.0)
            if not isinstance(occupancy_ratio, (int, float)):
                occupancy_ratio = 0.0
            
            space_statuses[space_id_key] = {
                "state": state_value,
                "occupancy_ratio": float(occupancy_ratio)
            }
        parking_status["spaces"] = space_statuses
        
        # Encode annotated frame as JPEG for response
        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()
        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
        
        return {
            "available": empty,
            "occupied": occupied,
            "total_spaces": analyzer.space_manager.total_spaces,
            "spaces": space_statuses,
            "annotated_frame": f"data:image/jpeg;base64,{frame_base64}",
            "timestamp": timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/realtime/parking-status")
async def get_parking_status():
    """Get current parking status"""
    # Return current parking status (updated by real-time detection)
    current_status = parking_status.copy()
    
    # If we have a config but no analyzer yet, get total_spaces from config
    global psd1_config_path
    if current_status["total_spaces"] == 0 and psd1_config_path and Path(psd1_config_path).exists():
        try:
            with open(psd1_config_path, 'r') as f:
                config = json.load(f)
                current_status["total_spaces"] = len(config.get("spaces", []))
        except:
            pass
    
    return current_status


@app.get("/api/realtime/dashboard")
async def get_dashboard_stats():
    """Get all dashboard statistics"""
    # Format plates for frontend compatibility
    formatted_plates = []
    for det in gate_detections[:10]:
        formatted_plates.append({
            "plate": det.get("plate_number", ""),
            "plate_number": det.get("plate_number", ""),
            "confidence": det.get("confidence", 0.0),
            "direction": det.get("direction", "in"),
            "timestamp": det.get("timestamp", datetime.now().isoformat()),
            "time": det.get("timestamp", datetime.now().isoformat())
        })
    
    # Get real-time parking status (use current values from parking_status)
    # If analyzer is loaded, try to get latest status
    current_parking = parking_status.copy()
    
    # If we have a config but no analyzer yet, get total_spaces from config
    global psd1_config_path
    if current_parking["total_spaces"] == 0 and psd1_config_path and Path(psd1_config_path).exists():
        try:
            with open(psd1_config_path, 'r') as f:
                config = json.load(f)
                current_parking["total_spaces"] = len(config.get("spaces", []))
        except:
            pass
    
    return {
        "parking": current_parking,
        "plates": {
            "recent": formatted_plates,
            "today_entries": today_entries_count  # Real count from plate detections
        },
        "timestamp": datetime.now().isoformat()
    }


class AnnotationSaveRequest(BaseModel):
    config_name: str
    spaces: List[dict]

@app.post("/api/annotations/save")
async def save_annotations(request: AnnotationSaveRequest):
    """Save parking space annotations"""
    global psd1_config_path, psd1_analyzer
    try:
        config_name = request.config_name
        spaces = request.spaces
        
        # Validate spaces data
        if not spaces or len(spaces) == 0:
            raise HTTPException(status_code=400, detail="No parking spaces provided")
        
        # Validate each space has required fields
        for idx, space in enumerate(spaces):
            if 'polygon' not in space:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Space {idx + 1} is missing 'polygon' field"
                )
            if not isinstance(space['polygon'], list) or len(space['polygon']) < 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"Space {idx + 1} polygon must have at least 3 points"
                )
        
        config_path = UPLOAD_DIR / f"annotations_{config_name}.json"
        
        # Convert spaces to the format expected by ConfigManager
        # ConfigManager expects: id (int), polygon ([[x,y], [x,y], ...])
        converted_spaces = []
        for idx, space in enumerate(spaces):
            # Extract polygon points - handle both {x, y} objects and [x, y] arrays
            polygon_points = []
            for point in space.get('polygon', []):
                if isinstance(point, dict):
                    # Format: {"x": 304, "y": 344}
                    polygon_points.append([int(point.get('x', 0)), int(point.get('y', 0))])
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    # Format: [x, y] or (x, y)
                    polygon_points.append([int(point[0]), int(point[1])])
            
            # Extract space_id - convert "space_1" to integer 1, or use index+1
            space_id_str = space.get('space_id', f'space_{idx + 1}')
            if isinstance(space_id_str, str) and space_id_str.startswith('space_'):
                try:
                    space_id = int(space_id_str.replace('space_', ''))
                except:
                    space_id = idx + 1
            elif isinstance(space_id_str, int):
                space_id = space_id_str
            else:
                space_id = idx + 1
            
            converted_space = {
                "id": space_id,
                "polygon": polygon_points,
                "min_occupancy_ratio": space.get('min_occupancy_ratio', 0.2)
            }
            converted_spaces.append(converted_space)
        
        # Save in format compatible with ConfigManager
        config = {
            "name": config_name,
            "created_at": datetime.now().isoformat(),
            "default_min_occupancy_ratio": 0.2,
            "spaces": converted_spaces
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set global config path and reset analyzer (will be lazy-loaded on next use)
        psd1_config_path = str(config_path)
        psd1_analyzer = None  # Reset so it reloads with new config
        
        # Update parking_status with total spaces from config
        global parking_status
        parking_status["total_spaces"] = len(spaces)
        parking_status["available"] = len(spaces)  # Initially all available
        parking_status["occupied"] = 0
        
        return {
            "success": True,
            "config_path": str(config_path),
            "spaces_count": len(spaces),
            "config": config,  # Return the full config so frontend can use it
            "message": "Configuration saved successfully. Parking analyzer will be initialized on first frame."
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error saving annotations: {str(e)}"
        print(f"Annotation save error: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/annotations/list")
async def list_annotations():
    """List all saved annotations"""
    annotation_files = list(UPLOAD_DIR.glob("annotations_*.json"))
    
    annotations = []
    for file in annotation_files:
        try:
            with open(file, 'r') as f:
                config = json.load(f)
                annotations.append({
                    "name": config.get("name", file.stem),
                    "spaces_count": len(config.get("spaces", [])),
                    "created_at": config.get("created_at"),
                    "file": file.name
                })
        except:
            continue
    
    return {"annotations": annotations}


@app.get("/api/annotations/load/{name}")
async def load_annotation(name: str):
    """Load a saved annotation"""
    config_path = UPLOAD_DIR / f"annotations_{name}.json"
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    with open(config_path, 'r') as f:
        return json.load(f)


@app.get("/api/annotations/current")
async def get_current_config():
    """Get the current parking space configuration"""
    global psd1_config_path
    try:
        if not psd1_config_path or not Path(psd1_config_path).exists():
            return {
                "success": False,
                "message": "No configuration loaded"
            }
        
        with open(psd1_config_path, 'r') as f:
            config = json.load(f)
        
        return {
            "success": True,
            "config": config,
            "config_path": psd1_config_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ==================== Frontend ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page"""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        with open(html_path, 'r') as f:
            return f.read()
    return """
    <html>
        <head><title>Integrated Vehicle Monitoring</title></head>
        <body>
            <h1>Integrated Vehicle Monitoring System</h1>
            <p>Frontend not found. Please ensure static/index.html exists.</p>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "npr_jobs": len(npr_jobs),
        "psd1_jobs": len(psd1_jobs)
    }


@app.get("/api/logs/parking-changes")
async def get_parking_changes_log():
    """Get parking space state change logs"""
    log_file = RESULTS_DIR / "realtime_parking_changes.csv"
    if not log_file.exists():
        return {"message": "No parking change logs found", "logs": []}
    
    try:
        import csv
        logs = []
        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
        return {
            "log_file": str(log_file),
            "total_entries": len(logs),
            "logs": logs[-100:]  # Return last 100 entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")


@app.get("/api/logs/plate-detections")
async def get_plate_detections_log(limit: int = 100):
    """Get number plate detection logs"""
    if not PLATE_LOG_CSV.exists():
        return {"message": "No plate detection logs found", "logs": []}
    
    try:
        import csv
        logs = []
        with open(PLATE_LOG_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
        return {
            "log_file": str(PLATE_LOG_CSV),
            "total_entries": len(logs),
            "logs": logs[-limit:]  # Return last N entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")


@app.get("/api/logs/download/parking-changes")
async def download_parking_changes_log():
    """Download parking space state change logs as CSV"""
    log_file = RESULTS_DIR / "realtime_parking_changes.csv"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        path=str(log_file),
        filename="parking_changes.csv",
        media_type="text/csv"
    )


@app.get("/api/logs/download/plate-detections")
async def download_plate_detections_log():
    """Download number plate detection logs as CSV"""
    if not PLATE_LOG_CSV.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        path=str(PLATE_LOG_CSV),
        filename="plate_detections.csv",
        media_type="text/csv"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

