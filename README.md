# AI Traffic Control System

Modern multi-page Flask app that uses YOLOv5 to detect vehicle density and dynamically control intersection lights (green/yellow/red) with adaptive timers.

## Description
This project is an end-to-end smart traffic signal system. Each approach uploads an image or video feed that is analyzed with YOLOv5 to count vehicles. The controller prioritizes the busiest approach, assigns a dynamic green time based on density, and enforces realistic yellow transitions both before granting right-of-way and before returning to red. A live dashboard shows per-approach status, timers, and vehicle counts, and the entire flow (landing → configuration → monitor) runs inside a simple Flask application.

## Screenshots

### 1. Landing Page
The landing page introduces the AI Traffic Control System with an overview of features and project description. Users can click "Get Started" to begin configuration.

![Landing Page](Screenshots/landing%20page.png)

### 2. Configuration Page
Configure the number of traffic lights (2-6) and upload image/video sources for each intersection approach. The system analyzes each upload using YOLOv5 to count vehicles before starting the traffic control system.

![Configuration Page](Screenshots/Config%20page.png)

### 3. Traffic Light Monitor
Real-time traffic light monitoring dashboard showing live status (Red/Yellow/Green), countdown timers, and vehicle counts for each intersection. The system automatically cycles through lights based on traffic density with proper yellow light transitions.

![Traffic Light Monitor](Screenshots/traffic%20light.png)

## Features
- Multi-page flow: landing → configuration → live monitor
- Upload image/video per approach, auto vehicle counting via YOLOv5s
- Adaptive timing: base 10s + 2s per vehicle, capped at 60s
- Full signal cycle with yellow transitions (3s before green, 5s before red)
- One-green-at-a-time priority based on current vehicle counts; zero-vehicle approaches stay red
- Live dashboard with status, timers, and vehicle counts per light

## Tech Stack
- Python, Flask
- PyTorch, YOLOv5s (torch.hub)
- OpenCV, NumPy
- Werkzeug for uploads

## Quick Start
1. **Create venv (recommended)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. **Install deps** (already installed in `.venv` if using the provided setup):
   ```bash
   pip install flask torch torchvision opencv-python werkzeug numpy ultralytics pandas tqdm matplotlib pillow pyyaml seaborn scipy
   ```
3. **Run the app**
   ```bash
   python app.py
   ```
4. Open http://127.0.0.1:5000

## App Flow
- **Landing**: project intro and CTA to configure
- **Configuration** (`/config`): pick number of lights (2–6), upload feeds per light, run “Analyze Traffic” to count vehicles, then “Start Traffic Lights”
- **Monitor** (`/monitor`): auto-starts the controller, shows live lights, timers, and counts. Stop button halts the cycle.

## API Endpoints
- `POST /upload?feed=<id>`: upload image/video, returns `vehicle_count`
- `POST /start_lights`: start controller
- `POST /stop_lights`: stop controller
- `GET /get_lights_status`: live statuses `{status, timers, counts}`

## Files & Structure
- `app.py` – Flask app, YOLO detection, light controller
- `templates/index.html` – landing
- `templates/config.html` – setup/upload
- `templates/traffic_light.html` – live monitor
- `uploads/` – stored uploads
- `images/` – sample assets (optional)

## Notes
- First run downloads YOLOv5 weights via `torch.hub` (needs internet once)
- Runs on CPU by default; GPU requires CUDA-enabled PyTorch build
- Keep `.venv` activated when running/testing
