#!/usr/bin/env python3
"""
FastAPI Server for Parking Lot Monitoring System
Provides REST API endpoints for video analysis and monitoring.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
import threading

# Import existing modules
from parking_analyzer import ParkingAnalyzer
from parking_space import ParkingSpaceManager
from logger import ParkingLogger
from config_manager import ConfigManager

app = FastAPI(title="Parking Lot Monitoring API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_analyses = {}
analysis_results = {}
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


class AnalysisRequest(BaseModel):
    """Request model for starting analysis"""
    video_path: Optional[str] = None
    config_path: str
    confidence: float = 0.5
    min_occupancy: float = 0.2
    fps_limit: int = 30
    use_simple_detector: bool = False
    device: str = "cpu"


class AnalysisStatus(BaseModel):
    """Analysis status response"""
    analysis_id: str
    status: str  # "running", "completed", "error"
    progress: float
    current_frame: int
    total_frames: int
    empty_count: int
    occupied_count: int
    message: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Parking Lot Monitoring API",
        "version": "1.0.0",
        "endpoints": {
            "upload_video": "/api/upload/video",
            "upload_config": "/api/upload/config",
            "start_analysis": "/api/analyze/start",
            "get_status": "/api/analyze/{analysis_id}/status",
            "get_results": "/api/analyze/{analysis_id}/results",
            "download_results": "/api/analyze/{analysis_id}/download",
            "list_analyses": "/api/analyze/list"
        }
    }


@app.post("/api/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file"""
    try:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/upload/config")
async def upload_config(file: UploadFile = File(...)):
    """Upload a parking spaces configuration file"""
    try:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate JSON
        try:
            json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Invalid JSON file")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "path": str(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


def run_analysis(analysis_id: str, video_path: str, config_path: str,
                confidence: float, min_occupancy: float, fps_limit: int,
                use_simple_detector: bool, device: str):
    """Run analysis in background thread"""
    try:
        active_analyses[analysis_id]["status"] = "running"
        
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
        log_file = RESULTS_DIR / f"{analysis_id}_changes.csv"
        analyzer.logger = ParkingLogger(str(log_file))
        
        # Get video properties
        import cv2
        cap_video = cv2.VideoCapture(video_path)
        total_frames = int(cap_video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap_video.get(cv2.CAP_PROP_FPS)
        cap_video.release()
        
        active_analyses[analysis_id]["total_frames"] = total_frames
        
        # Process frames
        cap = cv2.VideoCapture(video_path)
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_idx += 1
            timestamp = datetime.now()
            
            # Process frame
            processed_frame = analyzer.process_frame(frame, timestamp)
            
            # Update status periodically (every 10 frames to reduce overhead)
            if frame_idx % 10 == 0:
                empty, occupied = analyzer.space_manager.get_counts()
                active_analyses[analysis_id].update({
                    "current_frame": frame_idx,
                    "progress": (frame_idx / total_frames) * 100 if total_frames > 0 else 0,
                    "empty_count": empty,
                    "occupied_count": occupied
                })
        
        # Final status update
        empty, occupied = analyzer.space_manager.get_counts()
        active_analyses[analysis_id].update({
            "current_frame": frame_idx,
            "progress": 100.0,
            "empty_count": empty,
            "occupied_count": occupied
        })
        
        cap.release()
        
        # Export results
        analyzer.export_results(str(RESULTS_DIR / analysis_id))
        
        # Mark as completed
        active_analyses[analysis_id]["status"] = "completed"
        
        # Store results
        analysis_results[analysis_id] = {
            "empty_count": empty,
            "occupied_count": occupied,
            "total_spaces": analyzer.space_manager.total_spaces,
            "metrics_file": str(RESULTS_DIR / f"{analysis_id}_metrics_*.json"),
            "csv_file": str(log_file)
        }
        
    except Exception as e:
        active_analyses[analysis_id]["status"] = "error"
        active_analyses[analysis_id]["message"] = str(e)


@app.post("/api/analyze/start")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start a new analysis"""
    try:
        # Validate paths
        if request.video_path and not os.path.exists(request.video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        if not os.path.exists(request.config_path):
            raise HTTPException(status_code=404, detail="Config file not found")
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Initialize analysis status
        active_analyses[analysis_id] = {
            "status": "starting",
            "progress": 0.0,
            "current_frame": 0,
            "total_frames": 0,
            "empty_count": 0,
            "occupied_count": 0,
            "started_at": datetime.now().isoformat()
        }
        
        # Start analysis in background
        thread = threading.Thread(
            target=run_analysis,
            args=(
                analysis_id,
                request.video_path,
                request.config_path,
                request.confidence,
                request.min_occupancy,
                request.fps_limit,
                request.use_simple_detector,
                request.device
            ),
            daemon=True
        )
        thread.start()
        
        return {
            "analysis_id": analysis_id,
            "status": "started",
            "message": "Analysis started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@app.get("/api/analyze/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get status of an analysis"""
    if analysis_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    status = active_analyses[analysis_id]
    return AnalysisStatus(
        analysis_id=analysis_id,
        status=status["status"],
        progress=status["progress"],
        current_frame=status["current_frame"],
        total_frames=status["total_frames"],
        empty_count=status["empty_count"],
        occupied_count=status["occupied_count"],
        message=status.get("message")
    )


@app.get("/api/analyze/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get analysis results"""
    if analysis_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if active_analyses[analysis_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = analysis_results[analysis_id]
    
    # Try to load metrics JSON if available
    metrics_file = None
    metrics_dir = RESULTS_DIR / analysis_id
    if metrics_dir.exists():
        json_files = list(metrics_dir.glob("metrics_*.json"))
        if json_files:
            metrics_file = json_files[0]
    
    response = {
        "analysis_id": analysis_id,
        "empty_count": results["empty_count"],
        "occupied_count": results["occupied_count"],
        "total_spaces": results["total_spaces"],
        "occupancy_rate": results["occupied_count"] / results["total_spaces"] if results["total_spaces"] > 0 else 0,
        "csv_file": results["csv_file"]
    }
    
    if metrics_file:
        try:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
                response["metrics"] = metrics_data.get("summary", {})
        except:
            pass
    
    return response


@app.get("/api/analyze/{analysis_id}/download")
async def download_results(analysis_id: str, file_type: str = "csv"):
    """Download analysis results"""
    if analysis_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if active_analyses[analysis_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    if file_type == "csv":
        csv_file = RESULTS_DIR / f"{analysis_id}_changes.csv"
        if csv_file.exists():
            return FileResponse(
                str(csv_file),
                media_type="text/csv",
                filename=f"{analysis_id}_changes.csv"
            )
    
    elif file_type == "json":
        metrics_dir = RESULTS_DIR / analysis_id
        if metrics_dir.exists():
            json_files = list(metrics_dir.glob("metrics_*.json"))
            if json_files:
                return FileResponse(
                    str(json_files[0]),
                    media_type="application/json",
                    filename=f"{analysis_id}_metrics.json"
                )
    
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/analyze/list")
async def list_analyses():
    """List all analyses"""
    return {
        "active": len([a for a in active_analyses.values() if a["status"] == "running"]),
        "completed": len([a for a in active_analyses.values() if a["status"] == "completed"]),
        "analyses": [
            {
                "analysis_id": aid,
                "status": status["status"],
                "progress": status["progress"],
                "started_at": status.get("started_at")
            }
            for aid, status in active_analyses.items()
        ]
    }


@app.get("/api/spaces/load")
async def load_spaces(config_path: str):
    """Load and return parking spaces configuration"""
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Config file not found")
    
    try:
        spaces = ConfigManager.load_spaces(config_path)
        return {
            "config_path": config_path,
            "total_spaces": len(spaces),
            "spaces": [
                {
                    "id": s.space_id,
                    "polygon": s.polygon.tolist(),
                    "min_occupancy_ratio": s.min_occupancy_ratio
                }
                for s in spaces
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

