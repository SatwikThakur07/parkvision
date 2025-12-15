# Quick Start Guide

## Option 1: Docker Deployment (Recommended for Production)

### Prerequisites
- Docker and Docker Compose installed

### Steps

1. **Deploy using the deployment script:**
```bash
./deploy.sh
```

Or manually:
```bash
docker-compose up -d
```

2. **Check service status:**
```bash
curl http://localhost:8000/health
```

3. **Access API documentation:**
Open http://localhost:8000/docs in your browser

4. **Process a video:**
```bash
curl -X POST "http://localhost:8000/api/v1/process-video" \
     -F "file=@cars_plate_video.mp4"
```

5. **Check job status:**
```bash
# Use the job_id from the previous response
curl "http://localhost:8000/api/v1/job/{job_id}"
```

6. **Download results:**
```bash
curl "http://localhost:8000/api/v1/job/{job_id}/download" -o output.mp4
```

## Option 2: Local Development

### Prerequisites
- Python 3.11+
- pip

### Steps

1. **Install dependencies:**
```bash
pip3 install -r requirements.txt
```

2. **Run CLI mode:**
```bash
python3 run_cli.py cars_plate_video.mp4
```

3. **Run API server:**
```bash
python3 run_api.py
```

Then access http://localhost:8000/docs

## Option 3: Use Original Script

The original `main.py` script is still available:

```bash
python3 main.py
```

## Testing the API

### Using curl:

```bash
# 1. Upload and process video
JOB_ID=$(curl -s -X POST "http://localhost:8000/api/v1/process-video" \
  -F "file=@cars_plate_video.mp4" | jq -r '.job_id')

# 2. Wait a bit, then check status
sleep 5
curl "http://localhost:8000/api/v1/job/$JOB_ID"

# 3. Get detections
curl "http://localhost:8000/api/v1/detections/$JOB_ID" | jq

# 4. Download video
curl "http://localhost:8000/api/v1/job/$JOB_ID/download" -o output.mp4
```

### Using Python:

```python
import requests

# Upload video
with open('cars_plate_video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/process-video',
        files={'file': f}
    )
job_id = response.json()['job_id']

# Check status
status = requests.get(f'http://localhost:8000/api/v1/job/{job_id}').json()
print(status)

# Get detections
detections = requests.get(f'http://localhost:8000/api/v1/detections/{job_id}').json()
print(f"Found {detections['unique_plates']} unique plates")
```

## Troubleshooting

### Service won't start
- Check Docker logs: `docker-compose logs`
- Verify model file exists: `ls license_plate_best.pt`
- Check ports: Ensure port 8000 is not in use

### GPU not working
- Set `GPU_ENABLED=false` in docker-compose.yml or .env
- For Docker, GPU support requires nvidia-docker

### Out of memory
- Reduce video resolution
- Process shorter clips
- Increase Docker memory limits

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check API documentation at http://localhost:8000/docs
- Review logs in `logs/` directory

