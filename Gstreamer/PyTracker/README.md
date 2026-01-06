# Docker Setup Guide for YOLO Video Tracking

## Project Structure
```
project/
├── Dockerfile              # CPU version
├── Dockerfile.gpu          # GPU version
├── docker-compose.yml      # Compose configuration
├── yolo_tracker.py         # Main Python script
├── videos/                 # Place your video files here
│   └── video.mp4
└── output/                 # Output files saved here
```

## Prerequisites

### 1. Install Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Install Docker Compose
```bash
sudo apt-get install docker-compose
```

### 3. For GPU Support (Optional)
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## Quick Start

### Option 1: Using Docker Compose (Recommended)

#### CPU Version:
```bash
# Allow X11 access for display
xhost +local:docker

# Create directories
mkdir -p videos output

# Place your video file
cp /path/to/your/video.mp4 videos/

# Build and run
docker-compose up yolo-tracker-cpu

# Stop
docker-compose down
```

#### GPU Version:
```bash
# Allow X11 access
xhost +local:docker

# Build and run
docker-compose up yolo-tracker-gpu

# Stop
docker-compose down
```

#### Headless Version (No Display):
```bash
# Process video and save output
docker-compose up yolo-tracker-headless
```

### Option 2: Using Docker Directly

#### Build:
```bash
# CPU version
docker build -t yolo-tracker:cpu -f Dockerfile .

# GPU version
docker build -t yolo-tracker:gpu -f Dockerfile.gpu .
```

#### Run:
```bash
# CPU version with display
xhost +local:docker
docker run -it --rm \
    -v $(pwd)/videos:/app/videos \
    -v $(pwd)/output:/app/output \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    --network host \
    yolo-tracker:cpu python yolo_tracker.py /app/videos/video.mp4

# GPU version
docker run -it --rm \
    --gpus all \
    -v $(pwd)/videos:/app/videos \
    -v $(pwd)/output:/app/output \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    --network host \
    yolo-tracker:gpu python yolo_tracker.py /app/videos/video.mp4
```

## Configuration

### Custom Video File
Edit `docker-compose.yml` and change the command:
```yaml
command: python yolo_tracker.py /app/videos/your_video.mp4
```

Or run directly:
```bash
docker-compose run yolo-tracker-cpu python yolo_tracker.py /app/videos/your_video.mp4
```

### Use Different YOLO Model
```bash
docker-compose run yolo-tracker-cpu python yolo_tracker.py /app/videos/video.mp4 --model yolov8m.pt
```

Available models: `yolov8n.pt`, `yolov8s.pt`, `yolov8m.pt`, `yolov8l.pt`, `yolov8x.pt`

## Troubleshooting

### Display Issues
```bash
# If you get "cannot open display" error
xhost +local:docker
export DISPLAY=:0

# Check X11 socket
ls -la /tmp/.X11-unix
```

### Permission Issues
```bash
# Fix video directory permissions
sudo chmod -R 755 videos output
```

### GPU Not Detected
```bash
# Verify GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Container Fails to Start
```bash
# Check logs
docker-compose logs yolo-tracker-cpu

# Run in interactive mode
docker-compose run --rm yolo-tracker-cpu bash
```

## Performance Tips

1. **Use GPU version** for faster processing (5-10x speedup)
2. **Use smaller YOLO models** (yolov8n.pt) for real-time performance
3. **Adjust video resolution** if processing is slow
4. **Use headless mode** for batch processing without display

## Saving Output

Add video writer to your Python script to save processed video:
```python
# In yolo_tracker.py, add:
out = cv2.VideoWriter('/app/output/output.mp4', 
                      cv2.VideoWriter_fourcc(*'mp4v'),
                      30, (frame_width, frame_height))
# Write each frame
out.write(annotated_frame)
# Release at the end
out.release()
```

## Resource Limits

Add resource limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```