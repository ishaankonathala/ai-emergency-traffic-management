from flask import Blueprint, jsonify, request
from utils.database import get_recent_logs, get_analytics_summary
from utils.shared_state import shared_state

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_global_state():
    return shared_state.data

@api_bp.route('/status', methods=['GET'])
def status():
    state = get_global_state()
    return jsonify({
        "status": "ACTIVE",
        "fps": state.get("fps", 0),
        "emergency_mode": state.get("emergency_mode", False),
        "corridor_active": state.get("corridor_active", False),
        "current_junction": state.get("current_junction", None),
        "density_level": state.get("density_level", "Unknown")
    })

@api_bp.route('/logs', methods=['GET'])
def logs():
    return jsonify(get_recent_logs(limit=100))

@api_bp.route('/analytics', methods=['GET'])
def analytics():
    return jsonify(get_analytics_summary())

@api_bp.route('/simulate', methods=['POST'])
def simulate():
    data = request.json or {}
    vehicle = data.get("vehicle", "ambulance")
    
    state = get_global_state()
    state["simulate_request"] = vehicle
    
    return jsonify({"status": "Simulation triggered", "vehicle": vehicle})

@api_bp.route('/reset', methods=['POST'])
def reset():
    state = get_global_state()
    state["reset_request"] = True
    return jsonify({"status": "Reset triggered"})
