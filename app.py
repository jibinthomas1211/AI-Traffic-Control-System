from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import torch
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'  # Required for session

# Path to save the uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

# Stores vehicle counts for all roads (dynamic based on user selection)
vehicle_counts = {}
light_status = {}
light_timers = {}

# Global flag to start and stop the light cycling
start_lights_flag = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/setup', methods=['POST'])
def setup():
    num_lights = int(request.form.get('num_lights', 3))
    session['num_lights'] = num_lights
    
    # Initialize light status and timers for the selected number of lights
    # Do NOT reset vehicle_counts - they should persist from uploads
    global light_status, light_timers, vehicle_counts
    
    # Only initialize vehicle_counts if they don't exist yet
    if not vehicle_counts:
        vehicle_counts = {str(i): 0 for i in range(1, num_lights + 1)}
    
    light_status = {str(i): 'red' for i in range(1, num_lights + 1)}
    light_timers = {str(i): 0 for i in range(1, num_lights + 1)}
    
    print(f"Setup completed. Vehicle counts: {vehicle_counts}")  # Debug
    
    return redirect(url_for('traffic_monitor'))

@app.route('/monitor')
def traffic_monitor():
    num_lights = session.get('num_lights', 3)
    return render_template('traffic_light.html', num_lights=num_lights)


# Route to handle the file upload for each feed
@app.route('/upload', methods=['POST'])
def upload_file():
    feed_id = request.args.get('feed')  # Get feed number (1, 2, or 3)
    if 'file' not in request.files:
        return 'No file uploaded!', 400

    file = request.files['file']

    # Save the uploaded file
    filename = secure_filename(f"{feed_id}_{file.filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Run YOLO detection on the uploaded file
    vehicle_count = detect_vehicles(file_path)

    # Update the vehicle count for this feed
    vehicle_counts[feed_id] = vehicle_count
    
    print(f"Uploaded file for feed {feed_id}: {vehicle_count} vehicles detected")  # Debug
    print(f"Current vehicle counts: {vehicle_counts}")  # Debug

    return jsonify({'vehicle_count': vehicle_count, 'file_path': file_path})


# Function to run YOLOv5 model and detect vehicles
def detect_vehicles(file_path):
    # Read the image
    img = cv2.imread(file_path)

    # Run YOLOv5 model inference
    results = model(img)

    # Get the bounding boxes, labels, and confidence scores
    boxes = results.xyxy[0][:, :4].numpy()  # xyxy: [x1, y1, x2, y2]
    labels = results.xyxy[0][:, -1].numpy()  # classes
    confidences = results.xyxy[0][:, 4].numpy()  # confidence scores

    # Filter out vehicle classes (car, bus, truck)
    vehicle_classes = [2, 3, 5, 7]  # COCO classes for car, bus, truck
    vehicle_indices = np.isin(labels, vehicle_classes)

    # Keep only bounding boxes and labels for vehicles
    vehicle_boxes = boxes[vehicle_indices]
    vehicle_labels = labels[vehicle_indices]

    return len(vehicle_boxes)  # Return the count of detected vehicles


# Function to control the traffic lights based on vehicle density
def control_lights():
    global light_status, light_timers, start_lights_flag
    
    while start_lights_flag:
        # Sort roads based on vehicle count (descending - highest traffic first)
        sorted_roads = sorted(vehicle_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Process each road based on vehicle density
        for road_id, vehicle_count in sorted_roads:
            if not start_lights_flag:
                return
                
            if vehicle_count == 0:
                # No vehicles - keep red, skip this road
                light_status[road_id] = 'red'
                light_timers[road_id] = 0
                continue
            
            # Set all other lights to red
            for other_road_id in vehicle_counts.keys():
                if other_road_id != road_id:
                    light_status[other_road_id] = 'red'
                    light_timers[other_road_id] = 0
            
            # Calculate timer based on vehicle count
            # Base time: 10 seconds, add 2 seconds per vehicle (max 60 seconds)
            timer_duration = min(10 + (vehicle_count * 2), 60)
            
            # YELLOW LIGHT TRANSITION: Before turning GREEN (3 seconds)
            light_status[road_id] = 'yellow'
            light_timers[road_id] = 3
            for i in range(3, 0, -1):
                if not start_lights_flag:
                    for r_id in vehicle_counts.keys():
                        light_status[r_id] = 'red'
                        light_timers[r_id] = 0
                    return
                light_timers[road_id] = i
                time.sleep(1)
            
            # GREEN LIGHT: Main timer
            light_status[road_id] = 'green'
            light_timers[road_id] = timer_duration
            
            # Countdown timer (green light duration minus 5 seconds for yellow)
            green_duration = timer_duration - 5 if timer_duration > 5 else timer_duration
            for remaining in range(green_duration, 0, -1):
                if not start_lights_flag:
                    for r_id in vehicle_counts.keys():
                        light_status[r_id] = 'red'
                        light_timers[r_id] = 0
                    return
                light_timers[road_id] = remaining + 5  # Add 5 for yellow time
                time.sleep(1)
            
            # YELLOW LIGHT TRANSITION: Before turning RED (5 seconds)
            light_status[road_id] = 'yellow'
            light_timers[road_id] = 5
            for i in range(5, 0, -1):
                if not start_lights_flag:
                    for r_id in vehicle_counts.keys():
                        light_status[r_id] = 'red'
                        light_timers[r_id] = 0
                    return
                light_timers[road_id] = i
                time.sleep(1)
            
            # RED LIGHT: After yellow transition
            light_status[road_id] = 'red'
            light_timers[road_id] = 0
        
        # Small pause before next cycle
        time.sleep(1)

@app.route('/start_lights', methods=['POST'])
def start_lights():
    global start_lights_flag
    print(f"Starting lights with vehicle counts: {vehicle_counts}")  # Debug
    if not start_lights_flag:
        start_lights_flag = True
        threading.Thread(target=control_lights, daemon=True).start()
    return jsonify({"message": "Lights started", "vehicle_counts": vehicle_counts})

@app.route('/stop_lights', methods=['POST'])
def stop_lights():
    global start_lights_flag
    start_lights_flag = False
    return jsonify({"message": "Lights stopped"})


@app.route('/get_lights_status', methods=['GET'])
def get_lights_status():
    return jsonify({
        'status': light_status,
        'timers': light_timers,
        'counts': vehicle_counts
    })


if __name__ == '__main__':
    # Create uploads folder if not exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
