#!/bin/bash
set -e

echo "🚀 Deploying ParkVision to EC2..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Cannot detect OS"
    exit 1
fi

# Update system
if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ]; then
    echo "📦 Updating system (Amazon Linux/RHEL)..."
    sudo yum update -y
    sudo yum install -y docker git
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    echo "📦 Updating system (Ubuntu/Debian)..."
    sudo apt-get update -y
    sudo apt-get install -y docker.io docker-compose-plugin git
fi

# Start and enable Docker
echo "🐳 Setting up Docker..."
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
if id "ec2-user" &>/dev/null; then
    sudo usermod -aG docker ec2-user
    USER="ec2-user"
elif id "ubuntu" &>/dev/null; then
    sudo usermod -aG docker ubuntu
    USER="ubuntu"
else
    sudo usermod -aG docker $USER
fi

# Install Docker Compose (if not using plugin)
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "📥 Installing Docker Compose..."
    if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ]; then
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
fi

# Clone or update repository
echo "📂 Setting up project..."
if [ -d "parkvision" ]; then
    echo "📥 Updating existing repository..."
    cd parkvision
    git pull || echo "⚠️  Git pull failed, continuing with existing files..."
else
    echo "📥 Cloning repository..."
    git clone https://github.com/SatwikThakur07/parkvision.git || {
        echo "❌ Failed to clone repository. Please ensure:"
        echo "   1. Repository is public or you have access"
        echo "   2. Git is installed"
        echo "   3. Network connectivity is available"
        exit 1
    }
    cd parkvision
fi

# Verify required files exist
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found!"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found!"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p results uploads
mkdir -p npr psd1

# Check for model file
if [ ! -f "npr/license_plate_best.pt" ]; then
    echo "⚠️  Warning: npr/license_plate_best.pt not found!"
    echo "   The application may not work without the model file."
    echo "   Please ensure the model file is present in the repository or upload it manually."
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Build and start containers
echo "🔨 Building and starting containers..."
docker compose up --build -d

# Wait for container to be ready
echo "⏳ Waiting for service to start..."
sleep 10

# Check container status
if docker ps | grep -q parkvision; then
    echo "✅ Container is running!"
else
    echo "❌ Container failed to start. Checking logs..."
    docker compose logs parkvision
    exit 1
fi

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Deployment complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🌐 Access ParkVision at:"
echo "   http://${PUBLIC_IP}:8001"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f parkvision"
echo ""
echo "🔄 Restart service:"
echo "   docker compose restart parkvision"
echo ""
echo "🛑 Stop service:"
echo "   docker compose down"
echo ""
echo "═══════════════════════════════════════════════════════════"

