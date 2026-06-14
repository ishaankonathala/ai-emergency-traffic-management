import collections
import math
from typing import Tuple, Optional

class RoutePredictor:
    def __init__(self, history_size: int = 10):
        self.history = collections.deque(maxlen=history_size)
        self.current_speed = 0.0 # pixels per frame
        self.direction = "STRAIGHT"

    def update(self, emergency_bbox: Tuple[int, int, int, int]) -> dict:
        x1, y1, x2, y2 = emergency_bbox
        center_x = (x1 + x2) / 2.0
        center_y = (y1 + y2) / 2.0
        
        self.history.append((center_x, center_y))
        
        if len(self.history) >= 2:
            prev_x, prev_y = self.history[0]
            dx = center_x - prev_x
            dy = center_y - prev_y
            
            self.current_speed = math.sqrt(dx**2 + dy**2) / len(self.history)
            
            # Estimate direction
            angle = math.degrees(math.atan2(dy, dx))
            # Typically y is inverted in images (0 at top)
            # Up is -90 degrees
            if -135 < angle < -45:
                self.direction = "STRAIGHT"
            elif angle >= -45 or angle < 45:
                self.direction = "RIGHT_TURN"
            elif angle <= -135 or angle > 135:
                self.direction = "LEFT_TURN"
            else:
                self.direction = "STRAIGHT"

        # Predict next junction based on direction (Simulated)
        next_junction = "Junction B" if self.direction == "STRAIGHT" else ("Junction C" if self.direction == "LEFT_TURN" else "Junction D")

        return {
            "speed": self.current_speed,
            "direction": self.direction,
            "predicted_junction": next_junction
        }

    def reset(self):
        self.history.clear()
        self.current_speed = 0.0
        self.direction = "STRAIGHT"
