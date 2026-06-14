from typing import List, Dict, Tuple

class ObstructionDetector:
    def __init__(self, frame_width: int, frame_height: int):
        self.frame_width = frame_width
        self.frame_height = frame_height

    def detect(self, emergency_bbox: Tuple[int, int, int, int], other_vehicles: List[dict]) -> List[dict]:
        """
        Detects if other vehicles are blocking the path of the emergency vehicle.
        Assumes the emergency vehicle is moving forward (up the y-axis for now).
        """
        ex1, ey1, ex2, ey2 = emergency_bbox
        e_width = ex2 - ex1
        
        # Define a path region directly in front of the emergency vehicle
        # We'll make it slightly wider than the vehicle itself
        path_x1 = max(0, ex1 - int(e_width * 0.2))
        path_x2 = min(self.frame_width, ex2 + int(e_width * 0.2))
        path_y1 = 0
        path_y2 = ey1 # Everything in front of it

        obstructions = []

        for vehicle in other_vehicles:
            vx1, vy1, vx2, vy2 = vehicle["bbox"]
            
            # Check if vehicle intersects with the path region
            x_overlap = max(0, min(path_x2, vx2) - max(path_x1, vx1))
            y_overlap = max(0, min(path_y2, vy2) - max(path_y1, vy1))

            if x_overlap > 0 and y_overlap > 0:
                # Calculate severity based on proximity
                distance = ey1 - vy2
                severity = "HIGH" if distance < 100 else "MEDIUM"
                
                obstructions.append({
                    "vehicle": vehicle,
                    "severity": severity,
                    "distance": distance
                })

        return obstructions
