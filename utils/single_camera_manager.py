import cv2
import time
from pathlib import Path
from utils.shared_state import shared_state
from utils.density_analyzer import DensityAnalyzer
from utils.route_manager import EmergencyRouteManager
from utils.signal_controller import SignalController
from utils.obstruction_detector import ObstructionDetector
from utils.route_predictor import RoutePredictor
from utils.database import log_detection
EMERGENCY_LABELS = {"ambulance", "police_car", "fire_truck"}
CLASS_COLORS = {
    "ambulance": (0, 0, 255),
    "police_car": (255, 0, 0),
    "fire_truck": (0, 165, 255),
    "car": (0, 255, 0),
    "bus": (0, 200, 255),
    "motorcycle": (255, 255, 0),
    "truck": (0, 140, 255),
}
#self.camera_source
class SingleCameraManager:
    def __init__(self, model):
        self.model = model
        self.camera_source = "videos/video 2.mp4"
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            
        self.analyzer = DensityAnalyzer(frame_width=1280)
        self.route_manager = EmergencyRouteManager(green_seconds=15, yellow_seconds=3)
        self.signal_controller = SignalController()
        
        # New modules
        self.obstruction_detector = ObstructionDetector(frame_width=1280, frame_height=720)
        self.route_predictor = RoutePredictor()

        self.last_corridor_tick = time.time()
        self.frame_id = 0
        self.fps_start = time.time()
        self.fps = 0

    def _extract_detections(self, result):
        detections = []
        if result.boxes is None:
            return detections
        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            label = self.model.names.get(cls_id, str(cls_id))
            
            # --- DEMO MODE MAPPING ---
            if label == "truck": label = "fire_truck"
            elif label == "bus": label = "ambulance"
                
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            detections.append({
                "label": label,
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2),
            })
        return detections

    def draw_overlays(self, frame, detections, obstructions=None, prediction=None):
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]
            conf = det["confidence"]
            color = CLASS_COLORS.get(label, (255, 255, 255))
            
            is_obs = False
            if obstructions:
                for obs in obstructions:
                    if obs["vehicle"] == det:
                        is_obs = True
                        break
            
            if is_obs:
                color = (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 4)
                cv2.putText(frame, "BLOCKED!", (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
            text = f"{label} {conf:.2f}"
            cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.putText(frame, "Single Camera Mode", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        if prediction and prediction["speed"] > 0:
            speed_text = f"Speed: {prediction['speed']:.1f} px/f"
            dir_text = f"Dir: {prediction['direction']}"
            cv2.putText(frame, speed_text, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, dir_text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    def run_loop_step(self):
        now = time.time()
        
        sim_vehicle = shared_state.data["simulate_request"]
        shared_state.data["simulate_request"] = None
        if shared_state.data["reset_request"]:
            self.route_manager.reset_corridor()
            self.route_predictor.reset()
            shared_state.data["reset_request"] = False

        corridor_status = self.route_manager._build_snapshot("ACTIVE")
        
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            
        frame = cv2.resize(frame, (1280, 720))
        
        result = self.model(frame, conf=0.4, verbose=False)[0]
        detections = self._extract_detections(result)
        
        emergency_detections = [d for d in detections if d["label"] in EMERGENCY_LABELS]
        
        if sim_vehicle:
            emergency_detections.append({"label": sim_vehicle, "confidence": 0.99, "bbox": (600, 500, 700, 600)})
            detections.append(emergency_detections[-1])

        obstructions = []
        prediction = None

        if emergency_detections:
            top_emergency = max(emergency_detections, key=lambda d: d["confidence"])
            
            prediction = self.route_predictor.update(top_emergency["bbox"])
            
            other_vehicles = [d for d in detections if d not in emergency_detections]
            obstructions = self.obstruction_detector.detect(top_emergency["bbox"], other_vehicles)
            
            if obstructions:
                shared_state.data["obstruction_alert"] = "Obstruction detected on Single Cam"
            else:
                shared_state.data["obstruction_alert"] = None

            if not corridor_status.corridor_active:
                corridor_status = self.route_manager.activate_corridor(start_junction_index=0, vehicle_type=top_emergency["label"])
                
            if prediction["speed"] < 2.0 and corridor_status.corridor_active:
                self.route_manager.green_seconds = 20
            else:
                self.route_manager.green_seconds = 15

        self.draw_overlays(frame, detections, obstructions, prediction)

        if corridor_status.corridor_active and now - self.last_corridor_tick >= 1.0:
            corridor_status = self.route_manager.update_corridor(dt_seconds=1)
            self.last_corridor_tick = now
        elif not corridor_status.corridor_active and not emergency_detections:
            corridor_status = self.route_manager.reset_corridor()

        if self.frame_id % 10 == 0:
            self.fps = round(10 / (time.time() - self.fps_start), 1)
            self.fps_start = time.time()
            
        self.frame_id += 1
        
        cv2.putText(frame, f"System FPS: {self.fps} | Mode: SINGLE", (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            shared_state.latest_frame = buffer.tobytes()

        shared_state.data["fps"] = self.fps
        shared_state.data["emergency_mode"] = corridor_status.corridor_active
        shared_state.data["corridor_active"] = corridor_status.corridor_active
        shared_state.data["current_junction"] = corridor_status.current_junction
        shared_state.data["junction_states"] = corridor_status.junction_states
        shared_state.data["junction_timers"] = corridor_status.junction_timers
        shared_state.data["emergency_type"] = corridor_status.emergency_vehicle_type
        shared_state.data["eta_seconds"] = corridor_status.eta_seconds
        shared_state.data["marker_progress"] = corridor_status.marker_progress
