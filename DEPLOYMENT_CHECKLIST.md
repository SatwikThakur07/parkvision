# Deployment Checklist

Use this checklist to verify all required files are present for deployment.

## ✅ Essential Files

- [x] `Dockerfile` - Container image definition
- [x] `docker-compose.yml` - Development Docker Compose config
- [x] `docker-compose.prod.yml` - Production Docker Compose config
- [x] `.dockerignore` - Build optimization
- [x] `requirements_integrated.txt` - Python dependencies
- [x] `run_integrated.py` - Application entry point
- [x] `integrated_api.py` - Main FastAPI application
- [x] `static/index.html` - Frontend UI

## ✅ Directory Structure

- [x] `results/` - Logs directory (with .gitkeep)
- [x] `uploads/` - Uploads directory (with .gitkeep)
- [x] `npr/` - License plate recognition module
- [x] `psd1/` - Parking space detection module

## ✅ Documentation

- [x] `README.md` - Main project documentation
- [x] `DEPLOYMENT.md` - Docker deployment guide
- [x] `AWS_DEPLOYMENT.md` - AWS deployment guide
- [x] `deploy-ec2.sh` - Automated EC2 deployment script

## ⚠️ Required but Not in Repository

- [ ] `npr/license_plate_best.pt` - License plate detection model (too large for git)
  - **Action**: Must be provided separately or downloaded
  - **Note**: Docker Compose mounts this from host, so it must exist locally

## 🚀 Quick Verification

Run these commands to verify deployment readiness:

```bash
# Check Docker files exist
ls -la Dockerfile docker-compose.yml docker-compose.prod.yml .dockerignore

# Check required directories exist
ls -d results/ uploads/ npr/ psd1/

# Check Python files exist
ls -la run_integrated.py integrated_api.py requirements_integrated.txt

# Verify model file (must exist locally, not in git)
ls -lh npr/license_plate_best.pt || echo "⚠️  Model file not found - required for deployment"
```

## 📦 Deployment Commands

```bash
# Build and run
docker compose up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f parkvision

# Stop
docker compose down
```

