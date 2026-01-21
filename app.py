from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import torch
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import os
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

vehicle_counts = {}
light_status = {}
light_timers = {}

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
    
    global light_status, light_timers, vehicle_counts
    
    if not vehicle_counts:
        vehicle_counts = {str(i): 0 for i in range(1, num_lights + 1)}
    
    light_status = {str(i): 'red' for i in range(1, num_lights + 1)}
    light_timers = {str(i): 0 for i in range(1, num_lights + 1)}
    
    return redirect(url_for('traffic_monitor'))

@app.route('/monitor')
def traffic_monitor():
    num_lights = session.get('num_lights', 3)
    return render_template('traffic_light.html', num_lights=num_lights)


@app.route('/upload', methods=['POST'])
def upload_file():
    feed_id = request.args.get('feed')
    if 'file' not in request.files:
        return 'No file uploaded!', 400

    file = request.files['file']

    filename = secure_filename(f"{feed_id}_{file.filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    vehicle_count = detect_vehicles(file_path)
    vehicle_counts[feed_id] = vehicle_count

    return jsonify({'vehicle_count': vehicle_count, 'file_path': file_path})


# Function to run YOLOv5 model and detect vehicles
def detect_vehicles(file_path):
    img = cv2.imread(file_path)
    results = model(img)

    boxes = results.xyxy[0][:, :4].numpy()
    labels = results.xyxy[0][:, -1].numpy()
    confidences = results.xyxy[0][:, 4].numpy()

    vehicle_classes = [2, 3, 5, 7]
    vehicle_indices = np.isin(labels, vehicle_classes)

    vehicle_boxes = boxes[vehicle_indices]
    vehicle_labels = labels[vehicle_indices]

    return len(vehicle_boxes)


# Function to control the traffic lights based on vehicle density
def control_lights():
    global light_status, light_timers, start_lights_flag
    
    while start_lights_flag:
        sorted_roads = sorted(vehicle_counts.items(), key=lambda x: x[1], reverse=True)
        
        for road_id, vehicle_count in sorted_roads:
            if not start_lights_flag:
                return
                
            if vehicle_count == 0:
                light_status[road_id] = 'red'
                light_timers[road_id] = 0
                continue
            
            for other_road_id in vehicle_counts.keys():
                if other_road_id != road_id:
                    light_status[other_road_id] = 'red'
                    light_timers[other_road_id] = 0
            
            timer_duration = min(10 + (vehicle_count * 2), 60)
            
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
            
            light_status[road_id] = 'green'
            light_timers[road_id] = timer_duration
            
            green_duration = timer_duration - 5 if timer_duration > 5 else timer_duration
            for remaining in range(green_duration, 0, -1):
                if not start_lights_flag:
                    for r_id in vehicle_counts.keys():
                        light_status[r_id] = 'red'
                        light_timers[r_id] = 0
                    return
                light_timers[road_id] = remaining + 5
                time.sleep(1)
            
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
            
            light_status[road_id] = 'red'
            light_timers[road_id] = 0
        
        time.sleep(1)

@app.route('/start_lights', methods=['POST'])
def start_lights():
    global start_lights_flag
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
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)
