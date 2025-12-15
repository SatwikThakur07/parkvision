# Deployment Guide

## Issue: Docker Daemon Not Running

If you see the error: `Cannot connect to the Docker daemon`, follow these steps:

## Option 1: Start Docker and Deploy (Recommended for Production)

### Step 1: Start Docker Desktop

**On macOS:**
```bash
# Start Docker Desktop
open -a Docker

# Wait for Docker to start (check the Docker icon in menu bar)
# Then verify it's running:
docker info
```

**On Linux:**
```bash
sudo systemctl start docker
# Or
sudo service docker start
```

### Step 2: Deploy with Docker

Once Docker is running:
```bash
./deploy.sh
# OR
docker-compose up -d
```

### Step 3: Verify Deployment

```bash
# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

## Option 2: Run Locally Without Docker (Quick Start)

If you don't want to use Docker, you can run the service directly:

### Step 1: Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 2: Create Required Directories

```bash
mkdir -p uploads outputs logs
```

### Step 3: Run the API Server

```bash
python3 run_api.py
```

The API will be available at `http://localhost:8000`

### Step 4: Test the Service

```bash
# In another terminal, test the health endpoint
curl http://localhost:8000/health

# Or open in browser
open http://localhost:8000/docs
```

## Option 3: Use CLI Mode (No Server)

For simple video processing without API:

```bash
python3 run_cli.py cars_plate_video.mp4
```

## Troubleshooting

### Docker Issues

1. **Docker Desktop not installed?**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Permission denied?**
   ```bash
   # On Linux, add user to docker group
   sudo usermod -aG docker $USER
   # Then log out and back in
   ```

3. **Port 8000 already in use?**
   ```bash
   # Change port in docker-compose.yml or .env
   # Or kill the process using port 8000
   lsof -ti:8000 | xargs kill
   ```

### Local Deployment Issues

1. **Missing dependencies?**
   ```bash
   pip3 install --upgrade -r requirements.txt
   ```

2. **Import errors?**
   ```bash
   # Make sure you're in the project directory
   cd /Users/user/number_plate_detection
   python3 -c "from src.config import settings; print('OK')"
   ```

3. **Model file missing?**
   ```bash
   # Ensure license_plate_best.pt exists
   ls -lh license_plate_best.pt
   ```

## Quick Commands Reference

### Docker Commands
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose build --no-cache

# Check status
docker-compose ps
```

### Local Commands
```bash
# Start API
python3 run_api.py

# Process video (CLI)
python3 run_cli.py input.mp4

# Check health
curl http://localhost:8000/health
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [QUICKSTART.md](QUICKSTART.md) for quick examples
- Access API docs at http://localhost:8000/docs

