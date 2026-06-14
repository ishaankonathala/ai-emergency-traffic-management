from flask import Blueprint, Response
import time

stream_bp = Blueprint('stream', __name__)

def generate_frames():
    from utils.shared_state import shared_state
    while True:
        frame_bytes = shared_state.latest_frame
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)  # Add sleep to prevent tight looping
        else:
            time.sleep(0.1)

@stream_bp.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
