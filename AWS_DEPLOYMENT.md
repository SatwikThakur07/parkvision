# AWS Deployment Guide for ParkVision

This guide covers deploying the ParkVision container on AWS using multiple methods.

## 🚀 Method 1: EC2 Instance with Docker (Recommended for Single Server)

### Prerequisites
- AWS Account
- AWS CLI installed and configured
- SSH key pair for EC2 access

### Step 1: Launch EC2 Instance

1. **Go to EC2 Console** → Launch Instance
2. **Choose Instance Type**: 
   - Minimum: `t3.medium` (2 vCPU, 4 GB RAM)
   - Recommended: `t3.large` or `t3.xlarge` for better performance
   - For GPU support: `g4dn.xlarge` or higher
3. **Configure Instance**:
   - **AMI**: Amazon Linux 2023 or Ubuntu 22.04 LTS
   - **Instance Type**: t3.medium or higher
   - **Key Pair**: Select or create a new key pair
   - **Network Settings**: 
     - Create/select a security group
     - Add inbound rules:
       - **SSH (22)**: Your IP
       - **HTTP (80)**: 0.0.0.0/0 (or specific IPs)
       - **HTTPS (443)**: 0.0.0.0/0 (if using SSL)
       - **Custom TCP (8001)**: 0.0.0.0/0 (ParkVision port)
4. **Storage**: Minimum 20 GB (30+ GB recommended for logs/models)
5. **Launch Instance**

### Step 2: Connect to EC2 Instance

```bash
# Replace with your key file and instance IP
ssh -i your-key.pem ec2-user@your-ec2-ip
# For Ubuntu, use: ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Step 3: Install Docker and Docker Compose

**For Amazon Linux 2023:**
```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**For Ubuntu 22.04:**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

**Log out and log back in** for group changes to take effect.

### Step 4: Transfer Project Files to EC2

**Option A: Using Git (Recommended)**
```bash
# On EC2 instance
cd ~
git clone https://github.com/SatwikThakur07/parkvision.git
cd parkvision
```

**Option B: Using SCP**
```bash
# On your local machine
scp -i your-key.pem -r /Users/user/Downloads/npr_and_psd ec2-user@your-ec2-ip:~/
```

**Option C: Using AWS CodeCommit/CodeDeploy** (for CI/CD)

### Step 5: Build and Run Container

```bash
cd ~/parkvision  # or ~/npr_and_psd
docker compose up --build -d
```

### Step 6: Verify Deployment

```bash
# Check container status
docker ps

# Check logs
docker compose logs -f parkvision

# Test API
curl http://localhost:8001/api/realtime/dashboard
```

### Step 7: Access Application

- **Public IP**: `http://your-ec2-public-ip:8001`
- **Domain** (if configured): `http://your-domain.com:8001`

### Step 8: Set Up Auto-Start on Reboot

Create a systemd service:

```bash
sudo nano /etc/systemd/system/parkvision.service
```

Add:
```ini
[Unit]
Description=ParkVision Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/parkvision
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable parkvision.service
sudo systemctl start parkvision.service
```

---

## 🌐 Method 2: ECS (Elastic Container Service) - For Production

### Step 1: Push Image to ECR (Elastic Container Registry)

```bash
# Install AWS CLI if not already installed
# Configure AWS credentials
aws configure

# Create ECR repository
aws ecr create-repository --repository-name parkvision --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
cd ~/parkvision
docker build -t parkvision .
docker tag parkvision:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/parkvision:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/parkvision:latest
```

### Step 2: Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "parkvision",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "parkvision",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/parkvision:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PYTHONUNBUFFERED",
          "value": "1"
        },
        {
          "name": "GPU_ENABLED",
          "value": "false"
        },
        {
          "name": "OCR_GPU_ENABLED",
          "value": "false"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/parkvision",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "mountPoints": [
        {
          "sourceVolume": "results",
          "containerPath": "/app/results"
        },
        {
          "sourceVolume": "uploads",
          "containerPath": "/app/uploads"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "results",
      "efsVolumeConfiguration": {
        "fileSystemId": "YOUR_EFS_ID",
        "rootDirectory": "/results"
      }
    },
    {
      "name": "uploads",
      "efsVolumeConfiguration": {
        "fileSystemId": "YOUR_EFS_ID",
        "rootDirectory": "/uploads"
      }
    }
  ]
}
```

### Step 3: Register Task Definition

```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

### Step 4: Create ECS Cluster and Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name parkvision-cluster

# Create service
aws ecs create-service \
  --cluster parkvision-cluster \
  --service-name parkvision-service \
  --task-definition parkvision \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...:targetgroup/...,containerName=parkvision,containerPort=8000"
```

---

## 🔒 Security Best Practices

### 1. Use Security Groups Properly
- Restrict port 8001 to specific IPs or use a load balancer
- Only allow SSH from trusted IPs

### 2. Set Up SSL/TLS (HTTPS)
Use **AWS Application Load Balancer** with ACM certificate:

```bash
# Install certbot for Let's Encrypt (on EC2)
sudo yum install -y certbot python3-certbot-nginx
# Or use AWS Certificate Manager with ALB
```

### 3. Use IAM Roles
- Attach IAM role to EC2 instance instead of storing credentials
- Use ECS task roles for container permissions

### 4. Enable CloudWatch Logs
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm
```

### 5. Regular Backups
- Backup `results/` and `uploads/` directories to S3
- Use AWS Backup or create scheduled snapshots

---

## 📊 Monitoring and Logging

### CloudWatch Dashboard
1. Go to CloudWatch → Dashboards
2. Create dashboard for:
   - Container CPU/Memory usage
   - API request counts
   - Error rates

### Set Up Alarms
```bash
# CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name parkvision-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

---

## 🔄 Auto-Scaling (ECS)

Create auto-scaling configuration:

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/parkvision-cluster/parkvision-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 5
```

---

## 💾 Persistent Storage

### Option 1: EFS (Elastic File System) - For ECS
```bash
# Create EFS file system
aws efs create-file-system --creation-token parkvision-storage

# Create mount targets in your VPC subnets
aws efs create-mount-target \
  --file-system-id fs-xxx \
  --subnet-id subnet-xxx \
  --security-groups sg-xxx
```

### Option 2: EBS Volume - For EC2
```bash
# Create EBS volume
aws ec2 create-volume --size 50 --availability-zone us-east-1a

# Attach to instance
aws ec2 attach-volume --volume-id vol-xxx --instance-id i-xxx --device /dev/sdf

# Mount in EC2
sudo mkfs -t xfs /dev/xvdf
sudo mkdir /mnt/parkvision-data
sudo mount /dev/xvdf /mnt/parkvision-data
```

---

## 🚀 Quick Deploy Script

Save as `deploy-ec2.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying ParkVision to EC2..."

# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone or update repository
if [ -d "parkvision" ]; then
  cd parkvision
  git pull
else
  git clone https://github.com/SatwikThakur07/parkvision.git
  cd parkvision
fi

# Build and start containers
docker compose down || true
docker compose up --build -d

echo "✅ Deployment complete!"
echo "🌐 Access at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8001"
```

Make executable and run:
```bash
chmod +x deploy-ec2.sh
./deploy-ec2.sh
```

---

## 📝 Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs parkvision

# Check container status
docker ps -a

# Restart container
docker compose restart parkvision
```

### Port already in use
```bash
# Find process using port
sudo lsof -i :8001

# Kill process or change port in docker-compose.yml
```

### Out of memory
- Upgrade instance type
- Add swap space:
```bash
sudo dd if=/dev/zero of=/swapfile bs=1G count=4
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Model files missing
```bash
# Verify model file exists
ls -lh npr/license_plate_best.pt

# Check volume mounts in docker-compose.yml
```

---

## 🔗 Useful Commands

```bash
# View logs
docker compose logs -f parkvision

# Restart service
docker compose restart parkvision

# Update and redeploy
git pull && docker compose up --build -d

# Stop service
docker compose down

# Check resource usage
docker stats parkvision

# Access container shell
docker compose exec parkvision bash
```

---

## 📞 Support

For issues or questions:
- Check logs: `docker compose logs parkvision`
- GitHub Issues: https://github.com/SatwikThakur07/parkvision/issues
- AWS Support: https://aws.amazon.com/support/

---

**Next Steps:**
1. Set up domain name and DNS
2. Configure SSL certificate
3. Set up automated backups
4. Configure monitoring alerts
5. Set up CI/CD pipeline (optional)

