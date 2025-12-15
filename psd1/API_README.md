# FastAPI Server for Parking Lot Monitoring

## Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn[standard] python-multipart
```

### 2. Start the Server
```bash
python3 api_server.py
```

Or with uvicorn directly:
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Upload Files

**Upload Video:**
```bash
curl -X POST "http://localhost:8000/api/upload/video" \
  -F "file=@video.mp4"
```

**Upload Config:**
```bash
curl -X POST "http://localhost:8000/api/upload/config" \
  -F "file=@spaces.json"
```

### Start Analysis

```bash
curl -X POST "http://localhost:8000/api/analyze/start" \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "/path/to/video.mp4",
    "config_path": "/path/to/spaces.json",
    "confidence": 0.5,
    "min_occupancy": 0.2,
    "fps_limit": 30
  }'
```

Response:
```json
{
  "analysis_id": "uuid-here",
  "status": "started",
  "message": "Analysis started in background"
}
```

### Get Status

```bash
curl "http://localhost:8000/api/analyze/{analysis_id}/status"
```

Response:
```json
{
  "analysis_id": "uuid-here",
  "status": "running",
  "progress": 45.5,
  "current_frame": 289,
  "total_frames": 635,
  "empty_count": 12,
  "occupied_count": 3
}
```

### Get Results

```bash
curl "http://localhost:8000/api/analyze/{analysis_id}/results"
```

### Download Results

```bash
# Download CSV
curl "http://localhost:8000/api/analyze/{analysis_id}/download?file_type=csv" -o results.csv

# Download JSON
curl "http://localhost:8000/api/analyze/{analysis_id}/download?file_type=json" -o metrics.json
```

### List All Analyses

```bash
curl "http://localhost:8000/api/analyze/list"
```

### Load Spaces Config

```bash
curl "http://localhost:8000/api/spaces/load?config_path=/path/to/spaces.json"
```

## Python Client Example

```python
import requests

# Upload video
with open("video.mp4", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload/video",
        files={"file": f}
    )
    video_info = response.json()

# Start analysis
analysis_request = {
    "video_path": video_info["path"],
    "config_path": "spaces.json",
    "confidence": 0.5,
    "min_occupancy": 0.2
}
response = requests.post(
    "http://localhost:8000/api/analyze/start",
    json=analysis_request
)
analysis_id = response.json()["analysis_id"]

# Check status
while True:
    response = requests.get(
        f"http://localhost:8000/api/analyze/{analysis_id}/status"
    )
    status = response.json()
    print(f"Progress: {status['progress']:.1f}%")
    
    if status["status"] == "completed":
        break
    elif status["status"] == "error":
        print(f"Error: {status['message']}")
        break

# Get results
response = requests.get(
    f"http://localhost:8000/api/analyze/{analysis_id}/results"
)
results = response.json()
print(f"Empty: {results['empty_count']}, Occupied: {results['occupied_count']}")
```

## Web Interface

The API can be used with any frontend framework. Example HTML:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Parking Monitor API</title>
</head>
<body>
    <h1>Parking Lot Monitor</h1>
    <input type="file" id="videoFile" accept="video/*">
    <button onclick="startAnalysis()">Start Analysis</button>
    <div id="status"></div>
    
    <script>
        async function startAnalysis() {
            const file = document.getElementById('videoFile').files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            const uploadRes = await fetch('/api/upload/video', {
                method: 'POST',
                body: formData
            });
            const videoInfo = await uploadRes.json();
            
            const analysisRes = await fetch('/api/analyze/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    video_path: videoInfo.path,
                    config_path: 'spaces.json'
                })
            });
            const analysis = await analysisRes.json();
            
            // Poll for status
            const interval = setInterval(async () => {
                const statusRes = await fetch(`/api/analyze/${analysis.analysis_id}/status`);
                const status = await statusRes.json();
                document.getElementById('status').innerHTML = 
                    `Progress: ${status.progress.toFixed(1)}%`;
                
                if (status.status === 'completed') {
                    clearInterval(interval);
                    const resultsRes = await fetch(`/api/analyze/${analysis.analysis_id}/results`);
                    const results = await resultsRes.json();
                    document.getElementById('status').innerHTML = 
                        `Done! Empty: ${results.empty_count}, Occupied: ${results.occupied_count}`;
                }
            }, 1000);
        }
    </script>
</body>
</html>
```

## Notes

- Analyses run in background threads
- Results are stored in `output/` directory
- Uploaded files are stored in `uploads/` directory
- The API is stateless - use analysis_id to track progress
- CORS is enabled for all origins (adjust in production)

