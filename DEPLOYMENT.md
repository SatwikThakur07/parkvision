# ParkVision Deployment Guide

This guide covers deploying ParkVision using Docker containers.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Model file: `npr/license_plate_best.pt` (see Model File section below)

## 🚀 Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/SatwikThakur07/parkvision.git
cd parkvision
```

### 2. Model Files

✅ **Model files are included in the repository:**
- `npr/license_plate_best.pt` - License plate detection model (5.9MB)
- `psd1/yolov8n.pt` - Vehicle detection model (6.2MB)

These will be automatically included when you clone the repository and build the Docker image. No additional setup required!

### 3. Build and Run

```bash
# Build and start the container
docker compose up --build -d

# View logs
docker compose logs -f parkvision

# Stop the container
docker compose down
```

### 4. Access the Application

- **Web Interface**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## 🐳 Docker Compose Options

### Development Mode

```bash
docker compose up --build
```

### Production Mode

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Production mode includes:
- Resource limits (CPU/Memory)
- Health checks
- Auto-restart policies
- Log rotation

## 📁 Directory Structure

The following directories are created and mounted as volumes:

- `./results/` - Detection logs and output files
- `./uploads/` - User-uploaded files and annotations
- `./npr/license_plate_best.pt` - License plate detection model (must exist)

## 🔧 Configuration

### Environment Variables

You can customize the deployment by setting environment variables in `docker-compose.yml`:

```yaml
environment:
  PYTHONUNBUFFERED: "1"
  GPU_ENABLED: "false"        # Set to "true" if GPU available
  OCR_GPU_ENABLED: "false"    # Set to "true" for GPU-accelerated OCR
```

### Port Configuration

Default port mapping: `8001:8000` (host:container)

To change the host port, modify `docker-compose.yml`:
```yaml
ports:
  - "YOUR_PORT:8000"
```

## 🌐 AWS Deployment

For deploying on AWS (EC2, ECS, etc.), see [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs parkvision

# Check container status
docker ps -a

# Rebuild from scratch
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Model file not found

```bash
# Verify model files exist (they should be in the repository)
ls -lh npr/license_plate_best.pt psd1/yolov8n.pt

# If missing, ensure you've cloned the full repository
git pull origin main
```

### Port already in use

```bash
# Find process using port 8001
sudo lsof -i :8001

# Kill process or change port in docker-compose.yml
```

### Permission errors

```bash
# Ensure Docker has proper permissions
sudo usermod -aG docker $USER
# Log out and log back in
```

## 📊 Monitoring

### View Logs

```bash
# Follow logs in real-time
docker compose logs -f parkvision

# View last 100 lines
docker compose logs --tail=100 parkvision
```

### Resource Usage

```bash
# Check container resource usage
docker stats parkvision
```

## 🔄 Updates

To update the application:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose down
docker compose up --build -d
```

## 📝 Notes

- Both model files (`npr/license_plate_best.pt` and `psd1/yolov8n.pt`) are included in the repository
- Models are copied into the Docker image during build
- All detection logs are stored in `results/` directory
- Annotations are saved in `uploads/` directory
- Data persists across container restarts due to volume mounts

## 🆘 Support

For issues or questions:
- Check logs: `docker compose logs parkvision`
- GitHub Issues: https://github.com/SatwikThakur07/parkvision/issues
- See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for cloud deployment

