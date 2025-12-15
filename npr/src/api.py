"""FastAPI REST API for license plate detection"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
from pathlib import Path
from src.config import settings
from src.logger import setup_logger
from src.video_processor import VideoProcessor

logger = setup_logger(__name__, settings.log_level, settings.log_dir)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="License Plate Detection and Recognition Service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global processor instance
processor = None


@app.on_event("startup")
async def startup_event():
    """Initialize processor on startup"""
    global processor
    try:
        logger.info("Initializing video processor...")
        processor = VideoProcessor()
        logger.info("Service ready")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "processor_ready": processor is not None
    }


class ProcessVideoResponse(BaseModel):
    """Response model for video processing"""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status model"""
    job_id: str
    status: str
    input_video: Optional[str] = None
    output_video: Optional[str] = None
    total_detections: Optional[int] = None
    unique_plates: Optional[int] = None
    detection_files: Optional[dict] = None
    error: Optional[str] = None


# In-memory job storage (use Redis/DB in production)
jobs = {}


async def process_video_background(job_id: str, input_path: str):
    """Background task for video processing"""
    try:
        jobs[job_id]["status"] = "processing"
        logger.info(f"Starting background processing for job {job_id}")
        
        result = processor.process_video(
            input_path,
            save_detections=True,
            show_preview=False
        )
        
        jobs[job_id].update({
            "status": "completed",
            "output_video": result["output_video"],
            "total_detections": result["total_detections"],
            "unique_plates": result["unique_plates"],
            "detection_files": result["detection_files"]
        })
        
        logger.info(f"Job {job_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })


@app.post("/api/v1/process-video", response_model=ProcessVideoResponse)
async def process_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process video file"""
    if processor is None:
        raise HTTPException(status_code=503, detail="Processor not initialized")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_path = Path(settings.upload_dir) / f"{job_id}_{file.filename}"
    try:
        with open(upload_path, "wb") as f:
            content = await file.read()
            # Check file size
            size_mb = len(content) / (1024 * 1024)
            if size_mb > settings.max_upload_size_mb:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Max size: {settings.max_upload_size_mb}MB"
                )
            f.write(content)
        
        # Create job entry
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "input_video": str(upload_path)
        }
        
        # Start background processing
        background_tasks.add_task(process_video_background, job_id, str(upload_path))
        
        return ProcessVideoResponse(
            job_id=job_id,
            status="queued",
            message="Video processing started"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


@app.get("/api/v1/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**jobs[job_id])


@app.get("/api/v1/job/{job_id}/download")
async def download_output(job_id: str):
    """Download processed video"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    output_path = job.get("output_video")
    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=Path(output_path).name
    )


@app.get("/api/v1/detections/{job_id}")
async def get_detections(job_id: str):
    """Get detection results for a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    detection_files = job.get("detection_files", {})
    json_file = detection_files.get("json")
    
    if not json_file or not Path(json_file).exists():
        raise HTTPException(status_code=404, detail="Detection file not found")
    
    import json
    with open(json_file, 'r') as f:
        detections = json.load(f)
    
    return JSONResponse(content=detections)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )

