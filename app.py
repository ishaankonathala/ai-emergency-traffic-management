"""Main Flask app for smart traffic and emergency prioritization."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Dict, List

import cv2
from flask import Flask
from flask_socketio import SocketIO
from ultralytics import YOLO

from utils.database import create_database, log_detection
from utils.density_analyzer import DensityAnalyzer
from utils.route_manager import CorridorSnapshot, EmergencyRouteManager
from utils.signal_controller import SignalController

from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.stream import stream_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart_city_secret'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)
app.register_blueprint(stream_bp)

from utils.shared_state import shared_state

system_state = shared_state.data

EMERGENCY_LABELS = {"ambulance", "police_car", "fire_truck"}
CLASS_COLORS: Dict[str, tuple] = {
    "ambulance": (0, 0, 255),
    "police_car": (255, 0, 0),
    "fire_truck": (0, 165, 255),
    "car": (0, 255, 0),
    "bus": (0, 200, 255),
    "motorcycle": (255, 255, 0),
    "truck": (0, 140, 255),
}
JUNCTION_ORDER = ["Junction A", "Junction B", "Junction C", "Junction D"]


def extract_detections(result, names: Dict[int, str]) -> List[dict]:
    detections = []
    if result.boxes is None:
        return detections

    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        label = names.get(cls_id, str(cls_id))
        
        # --- DEMO MODE MAPPING ---
        # The base YOLOv8 model only knows standard vehicles. 
        # For the demo, we map standard large vehicles to emergency ones 
        # so the automatic detection and corridor simulation works.
        if label == "truck":
            label = "fire_truck"
        elif label == "bus":
            label = "ambulance"
            
        confidence = float(box.conf[0].item())
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        detections.append(
            {
                "label": label,
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2),
            }
        )
    return detections


def draw_detection_boxes(frame, detections: List[dict]) -> None:
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = det["label"]
        conf = det["confidence"]
        color = CLASS_COLORS.get(label, (255, 255, 255))
        text = f"{label} {conf:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (x1, max(y1 - th - 8, 0)), (x1 + tw + 8, y1), color, -1)
        cv2.putText(frame, text, (x1 + 4, max(y1 - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

def get_state_color(state: str) -> tuple:
    if state == "GREEN": return (0, 255, 0)
    if state == "YELLOW": return (0, 255, 255)
    if state == "PREPARE GREEN": return (0, 190, 255)
    if state == "RED": return (0, 0, 255)
    return (180, 180, 180)


def draw_corridor_map(frame, route_status: CorridorSnapshot, blink_on: bool) -> None:
    # Top center panel
    panel_w, panel_h = 500, 100
    x = (frame.shape[1] - panel_w) // 2
    y = 10
    
    # Draw transparent panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + panel_w, y + panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.rectangle(frame, (x, y), (x + panel_w, y + panel_h), (180, 180, 180), 1)

    y_map = y + 50
    left_pad = x + 40
    right_pad = 40
    available = panel_w - left_pad - right_pad + x
    step = max(1, (panel_w - 80) // (len(JUNCTION_ORDER) - 1))
    points = [(x + 40 + i * step, y_map) for i in range(len(JUNCTION_ORDER))]

    # Draw paths
    for i in range(len(points) - 1):
        next_color = (120, 120, 120)
        if route_status.corridor_active and route_status.current_junction:
            current_idx = JUNCTION_ORDER.index(route_status.current_junction)
            if i <= current_idx:
                next_color = (0, 255, 0)
            elif i == current_idx + 1:
                next_color = (0, 190, 255)
        cv2.arrowedLine(frame, points[i], points[i + 1], next_color, 2, tipLength=0.08)

    # Marker point
    marker_point = None
    if route_status.corridor_active and route_status.current_junction:
        idx = JUNCTION_ORDER.index(route_status.current_junction)
        if idx < len(points) - 1:
            x1, y1 = points[idx]
            x2, _ = points[idx + 1]
            marker_x = int(x1 + (x2 - x1) * route_status.marker_progress)
            marker_point = (marker_x, y1)
        else:
            marker_point = points[idx]

    # Junctions
    for i, junction in enumerate(JUNCTION_ORDER):
        state = route_status.junction_states.get(junction, "NORMAL")
        color = get_state_color(state)
        cv2.circle(frame, points[i], 12, color, -1)
        cv2.circle(frame, points[i], 12, (20, 20, 20), 2)
        cv2.putText(frame, junction.split()[-1], (points[i][0] - 5, points[i][1] + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Emergency Marker
    if marker_point and blink_on:
        cv2.circle(frame, marker_point, 8, (0, 80, 255), -1)


def run_system_loop():
    from utils.single_camera_manager import SingleCameraManager
    from ultralytics import YOLO
    import time
    
    model = YOLO("model/yolov8n.pt")
    single_manager = SingleCameraManager(model=model)
    
    while True:
        loop_start = time.time()
        
        single_manager.run_loop_step()
        
        # Broadcast state
        socketio.emit('state_update', system_state)
        
        # Cap processing speed slightly to avoid CPU pinning
        elapsed = time.time() - loop_start
        if elapsed < 0.05:
            socketio.sleep(0.05 - elapsed)
        else:
            socketio.sleep(0.001)

if __name__ == '__main__':
    # Start inference loop in background
    socketio.start_background_task(run_system_loop)
    print("Starting Flask server on http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)
