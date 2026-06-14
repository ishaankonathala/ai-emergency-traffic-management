class SharedState:
    def __init__(self):
        self.latest_frame = None
        self.data = {
            "status": "INITIALIZING",
            "fps": 0,
            "emergency_mode": False,
            "corridor_active": False,
            "current_junction": None,
            "density_level": "Unknown",
            "junction_states": {},
            "junction_timers": {},
            "simulate_request": None,
            "reset_request": False,
            "stats": {
                "car": 0, "bus": 0, "motorcycle": 0, "truck": 0, "emergency": 0
            },
            "emergency_type": None,
            "eta_seconds": 0,
            "marker_progress": 0.0,
            "signal_state": "NORMAL",
            "signal_time_left": 0
        }

shared_state = SharedState()
