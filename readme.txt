https://claude.ai/share/56b305bf-6bfb-4a40-901e-5a5c5b1f2b7d


What problem are you solving?
Emergency vehicles in Indian cities lose precious minutes stuck at red lights or blocked by traffic. A delay of even 2–3 minutes can cost lives. Your system solves this by giving emergency vehicles an automatic "Green Corridor" — a chain of green lights along their route — without any human operator needing to intervene.
Full system architecture & workflow
As the diagram shows, the system flows through four layers:
Step 1 — Input. A CCTV camera feeds live video into OpenCV, which captures each frame (30 fps), resizes it, and normalises it for the AI model.
Step 2 — AI Core. The frame is passed into YOLOv8, which runs in real time on every frame. It draws bounding boxes around every detected vehicle and classifies them (car, bus, motorcycle, ambulance, fire truck, police car) with a confidence score. Simultaneously, two other modules run in parallel — the RoutePredictor tracks the bounding box coordinates across multiple frames, calculates the velocity vector to estimate speed and direction (straight, left, right); and the ObstructionDetector projects a zone directly in front of the emergency vehicle and checks if any civilian vehicle bounding boxes intersect that zone.
Step 3 — Control. All this data flows into the EmergencyRouteManager, which is the brain of the system. It knows the positions of all junctions (A → B → C → D) and decides which signal to override. When a vehicle is detected, it triggers the Green Corridor: current junction goes green for 15 seconds, next junction enters "Prepare Green" state. If obstruction is detected, it extends the green phase to 20 seconds automatically.
Step 4 — Output. Flask serves the web dashboard. Flask-SocketIO pushes live telemetry (junction states, FPS, ETAs, alerts) to the browser via WebSockets — no page refresh needed. Traffic signal hardware is controlled directly by the route manager.
Technology stack explained simply
Tech	What it actually does
YOLOv8	The AI vision brain — analyses video frames in milliseconds
PyTorch	The engine underneath YOLOv8 that runs the neural network
OpenCV	Handles raw video — frame grabbing, resizing, drawing boxes
Python 3	Ties everything together
Flask	A web server that hosts your dashboard and API
Flask-SocketIO	Pushes real-time data to the browser without polling
HTML/CSS/JS + Bootstrap	The dashboard interface — dark mode command centre UI
How you'd integrate this with real-world CCTV
This is a great question for your presentation. Here's the practical integration path:
Most city intersections in India already have PTZ cameras (Pan-Tilt-Zoom) or fixed IP cameras connected to a central traffic management centre (TMC). Your system would plug in as follows:
The existing CCTV cameras stream RTSP (Real-Time Streaming Protocol) video over the city's fibre or LTE network to your server. OpenCV's cv2.VideoCapture("rtsp://...") can directly ingest these streams — you just replace the local video file path with the RTSP URL. No new cameras needed in theory.
For the signal control side, modern traffic light controllers in India (Siemens, Econolite) support SCATS or SCOOT protocols, which expose APIs for external override. Your EmergencyRouteManager would send a command to the intersection's controller box via this API to force a green phase. In newer smart city projects (like Surat, Pune, Hyderabad smart city deployments), this integration layer already exists and is documented.
For places without smart signals, a physical relay or IoT gateway (like a Raspberry Pi connected to the signal control cabinet) can serve as the bridge — your system sends an HTTP request to the Pi, which flips the relay.
How you handle real-world Indian traffic conditions
This is the most important part — interviewers will definitely ask this.
Problem 1: Chaotic multi-vehicle detection. Indian roads have a high density mix — autos, bikes, tempos, cows, and pedestrians all at once. YOLOv8's confidence threshold and NMS (Non-Maximum Suppression) settings become critical. You tune the model to flag ambulances/fire trucks only above a 0.75+ confidence score to reduce false positives from a white van or a bus. For the demo mode, you use the bus → ambulance mapping as a workaround.
Problem 2: Vehicles not following the red light. Your obstruction detection already handles this partly — it detects blocking civilian vehicles and extends the green phase. You can also add an alert to the operator dashboard saying "Obstruction at Junction B — manual PA system recommended" so a human can intervene (broadcast over the junction speaker).
Problem 3: Road quality and lane discipline don't exist. Because you're using bounding box centroid tracking for trajectory, you don't rely on lanes at all. The RoutePredictor uses raw pixel movement vectors, so it works even if the ambulance is weaving through traffic or cutting across lanes. You track where it IS, not where it's supposed to be.
Problem 4: Wrong-side driving or U-turns. The trajectory module classifies movement as straight/left/right based on the angle of the velocity vector. If an ambulance does a U-turn or reverses, the system detects the direction change and re-predicts the next junction. You can add a confidence window (e.g., direction is only committed after 3 consecutive frames pointing the same way) to avoid reacting to momentary swerves.
Problem 5: Low light, rain, dust (Indian weather). OpenCV preprocessing can apply histogram equalisation and denoising before the frame goes to YOLOv8. The YOLO model itself can be fine-tuned on Indian road datasets (like IDD — Indian Driving Dataset, published by IIIT Hyderabad) which include night, rain, and fog conditions specifically.
Problem 6: Multiple emergency vehicles simultaneously. The EmergencyRouteManager maintains a priority queue — first vehicle detected gets first priority corridor, others wait or are routed to alternate junctions.
For your presentation — key talking points
The single most impressive thing you can say is this: the system is reactive and predictive at the same time. It doesn't just see the ambulance at Junction A and turn it green — it's already preparing Junction B before the ambulance gets there, so the vehicle never decelerates. That's the Green Corridor concept and it's the core innovation worth emphasising.
Also highlight that the system is infrastructure-light — it works with existing cameras and can communicate with existing signal controllers, meaning deployment doesn't require rebuilding the city.

KEY TECHNICAL DETAILS
YOLO = You Only Look Once. Unlike older detection methods that scan an image multiple times, YOLO looks at the entire image in a single forward pass through the neural network — making it fast enough for real-time video.
Bounding boxes are rectangular overlays drawn around each detected vehicle. Each box stores: (x, y) top-left coordinate, width, height, class label, and confidence score (0 to 1).
NMS (Non-Maximum Suppression) prevents the model from drawing multiple overlapping boxes on the same vehicle — it keeps only the highest-confidence box per detected object.
Demo mode mapping: Since standard YOLO is trained on general datasets, a bus detection gets remapped to "ambulance" in demo mode to simulate emergency vehicle detection when a real emergency dataset isn't available.
PyTorch runs underneath YOLOv8 as the deep learning framework — it handles all the matrix multiplications and GPU acceleration for the neural network.

ROUTE ORCHESTRATION (JUNCTION A → B → C → D)
EmergencyRouteManager is the central controller. It holds a map of all junctions in the city grid and their physical positions relative to each other.
When an emergency vehicle is detected at Junction A, it sets A to GREEN and simultaneously puts Junction B into "Prepare Green" state — B begins clearing its cross traffic before the ambulance even reaches it.
This look-ahead mechanism is what makes the corridor smooth. The vehicle never decelerates because the next signal is already green before it arrives.
As the vehicle leaves Junction A and enters B, A resets to normal cycle. B goes fully green. C begins prepare phase. The corridor rolls forward like a wave.
If an obstruction is detected (see Feature D), the green phase at the current junction is extended from 15s to 20s, giving civilian vehicles time to clear the path.


CORRIDOR STATES (A → B → C → D)
The system transitions each junction through three states:
1. ACTIVE (Green): Main flow for emergency vehicle.
2. PREPARE_GREEN (Yellow pulse): Cross-traffic clears, preparing for next wave.
3. RESTORE_CYCLE (Red): Normal traffic resumes.
Timeline example (ambulance path):
0–15s: Junction AACTIVE, Junction B PREPARE_GREEN, Junction C RESTORE_CYCLE
15–30s: Junction A RESTORE_CYCLE, Junction B ACTIVE, Junction C PREPARE_GREEN
30–45s: Junction A RESTORE_CYCLE, Junction B RESTORE_CYCLE, Junction C ACTIVE
Vehicle never stops — it maintains momentum through the entire corridor.

TRAJECTORY TRACKING & SPEED ESTIMATION
Uses bounding box centroid tracking across consecutive frames.
Calculates velocity vector (displacement / time).
Speed (pixels/frame) is converted to real-world speed using a pre-calculated distance scale (distance between two known reference points in the frame).
Classifies direction as straight/left/right based on angle of velocity vector (requires calibration for each camera's perspective).
Trajectory stored in SharedState for visualization (history of dots) and prediction (next junction).

OBSTRUCTION DETECTION
When emergency vehicle detected, ObstructionDetector creates a "safety box" projected in front of it.
Safety box dimensions scale with emergency vehicle size and speed.
Any civilian vehicle (car, bus, motorcycle, etc.) whose bounding box overlaps the safety box is flagged as an obstruction.
Obstructions extend current green phase by 5 seconds (from 15s to 20s).
Also triggers visual alert on dashboard and logs event to database.
If multiple obstructions, extends green further (e.g., 25s) to clear entire intersection.

PREDICTIVE ROUTING
At each junction, RoutePredictor estimates time until next junction based on current speed and remaining distance.
Provides ETA for each upcoming junction in corridor.
If vehicle deviates from predicted path (e.g., slows unexpectedly), predictor recalculates remaining ETAs.
Used to adjust Prepare Green timings so next junction is ready exactly when vehicle arrives.

DATABASE INTEGRATION (SQLITE)
Database tables:
emergency_events: logs every detection with timestamp, type, confidence, bbox
corridor_logs: records green corridor activations and durations
obstruction_events: tracks blocking vehicles and phase extensions
Example queries:
SELECT * FROM emergency_events WHERE timestamp > datetime('now', '-1 hour')
SELECT SUM(duration_seconds) FROM corridor_logs WHERE vehicle_type = 'ambulance'
SCHEDULED TRIGGER (CRON ALTERNATIVE)
runs_per_second = 30 (frame rate)
schedule_interval = 15.0 seconds
corridor_timeout = 60.0 seconds (auto-reset if no emergency detected for 1 min)
System ticks every frame, but only builds snapshot every 15 seconds to reduce overhead.

REAL-TIME DASHBOARD (FLASK + SOCKETIO)
WebSockets push live data to browser without page refresh:
Junction states (ACTIVE / PREPARE_GREEN / RESTORE_CYCLE)
Vehicle trajectory history (green dots)
Obstruction alerts with bounding boxes
Speed estimates (pixels/frame)
ETA for next junctions

Centroid tracking: The center point of the bounding box (x_center = x + width/2, y_center = y + height/2) is extracted each frame. This gives us a 2D position over time.
Velocity vector: Subtracting the previous centroid from the current one gives a directional vector. Its angle (using arctan of Δy/Δx) determines which way the vehicle is heading.
No lane dependency: Because the system tracks raw pixel movement — not lane markers — it works perfectly on Indian roads where lane discipline doesn't exist. The vehicle can weave, cut across, or drive on the wrong side and the tracker still follows it.
3-frame confirmation window: The direction is only committed as "Left Turn" or "Right Turn" after 3 consecutive frames pointing the same way. This prevents a single swerve or pothole bump from incorrectly triggering a junction switch.
Junction prediction: Once direction is confirmed, the RoutePredictor maps that direction to the next physical junction in the grid. Straight → next junction ahead. Right → right-branch junction. This tells the EmergencyRouteManager which junction to prepare next.

Velocity vector: Subtracting the previous centroid from the current one gives a directional vector. Its angle (using arctan of Δy/Δx) determines which way the vehicle is heading.
No lane dependency: Because the system tracks raw pixel movement — not lane markers — it works perfectly on Indian roads where lane discipline doesn't exist. The vehicle can weave, cut across, or drive on the wrong side and the tracker still follows it.
3-frame confirmation window: The direction is only committed as "Left Turn" or "Right Turn" after 3 consecutive frames pointing the same way. This prevents a single swerve or pothole bump from incorrectly triggering a junction switch.
Junction prediction: Once direction is confirmed, the RoutePredictor maps that direction to the next physical junction in the grid. Straight → next junction ahead. Right → right-branch junction. This tells the EmergencyRouteManager which junction to prepare next.

Velocity vector: Subtracting the previous centroid from the current one gives a directional vector. Its angle (using arctan of Δy/Δx) determines which way the vehicle is heading.
No lane dependency: Because the system tracks raw pixel movement — not lane markers — it works perfectly on Indian roads where lane discipline doesn't exist. The vehicle can weave, cut across, or drive on the wrong side and the tracker still follows it.
3-frame confirmation window: The direction is only committed as "Left Turn" or "Right Turn" after 3 consecutive frames pointing the same way. This prevents a single swerve or pothole bump from incorrectly triggering a junction switch.
Junction prediction: Once direction is confirmed, the RoutePredictor maps that direction to the next physical junction in the grid. Straight → next junction ahead. Right → right-branch junction. This tells the EmergencyRouteManager which junction to prepare next.


Vehicle tracking: It maintains a history of bounding box positions for each detected vehicle across multiple frames. By tracking where the centroid (center point) of the box moves over time, the system can calculate the vehicle's exact position, speed, and direction.
Intersection locations: The RoutePredictor has a predefined map of all traffic junctions (junction_A, junction_B, junction_C, junction_D) and their coordinates in the video frame. It knows which pixel coordinates correspond to which physical junction.
Prediction logic: When the tracking module detects movement toward a known junction coordinate, the RoutePredictor predicts that the vehicle will arrive at that junction next. It uses the speed and remaining distance to calculate a time estimate for arrival.
Route following: Based on the predicted next junction, the EmergencyRouteManager updates the system state. For example, if a vehicle is moving straight from Junction A to Junction B, the manager sets Junction A to ACTIVE, Junction B to PREPARE_GREEN, and Junction C to RESTORE_CYCLE, creating a green corridor along that path.


Speed estimation: It uses the distance between two consecutive bounding box positions (from frame N and N+1) and divides it by the time difference (1/30th of a second) to calculate speed in pixels per frame. This is then converted to a more intuitive speed in pixels per second.
Trajectory visualization: The system stores the last 20 positions of the emergency vehicle as coordinates. These coordinates are drawn as small green dots or a continuous line on the video feed, creating a visual trail that shows where the vehicle has traveled.
Adaptive green light: The standard green light duration is 15 seconds. However, if the speed estimation shows the vehicle is moving slowly (less than 2 pixels per frame, indicating a jam or obstruction), the system automatically extends the green light to 20 seconds to help clear the path.

Why WebSockets, not HTTP polling? Traditional dashboards repeatedly ask the server "anything new?" (polling). WebSockets keep a persistent connection open — the server pushes data the instant something changes. This means junction state changes appear in under 50ms on the dashboard.
OpenCV overlays on video feed: Before the video frame is sent to the browser, OpenCV draws directly onto the frame — bounding box rectangles (cv2.rectangle), vehicle class labels (cv2.putText), confidence percentages, and the projected obstruction zone rectangle. The annotated frame is then JPEG-encoded and streamed.
Bootstrap dark mode UI: The command centre uses Bootstrap's dark theme for the "mission control" aesthetic. Junction status cards change CSS classes (green-card, red-card, prepare-card) in real time based on data received via WebSocket.
FPS counter: The dashboard shows live frames-per-second of the AI pipeline — if GPU processing slows down, operators can see it immediately as the FPS drops.
No page refresh architecture: The entire dashboard updates via JavaScript DOM manipulation. No full page reloads ever happen during operation — the UI feels like a native desktop app


Real-time obstacle detection and routing for emergency vehicles:
- Detects emergency vehicles (ambulance, police, fire truck) using YOLOv8.
- Tracks vehicle position, speed, and direction using OpenCV.
- Predicts vehicle's next junction and trajectory.
- Adjusts traffic light timing to create a green corridor.
- Provides WebSocket-based real-time dashboard with video feed, junction status, and alerts.
- Compatible with Roboflow and Kaggle datasets.
