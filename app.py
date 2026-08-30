import os
import time
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from vision import autonomous_inventory_scan
from generator import generate_json_spec
from deterministic_renderer import generate_svg
from gcode_converter import compile_svg
from cnc_streamer import stream_gcode

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("WebAppMaster")

# State variables
app_state = {
    "telemetry": None,
    "json_spec": None,
    "output_dir": "test_outputs",
    "png_output": "test_outputs/inventory.jpg",
    "debug_png": "test_outputs/debug_inventory.jpg",
    "plot_svg": "test_outputs/plot.svg",
    "gcode_output": "test_outputs/plot.gcode",
    "serial_port": os.getenv("CNC_PORT", "/dev/ttyACM0"),
    "baudrate": int(os.getenv("CNC_BAUD", "115200")),
    "ipcam_url": os.getenv("IPCAM_URL", "http://10.136.106.51:4747/video"),
    "mock": False,
    "simulate": False
}

os.makedirs(app_state["output_dir"], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test_outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(app_state["output_dir"], filename)

@app.route('/api/config')
def get_config():
    return jsonify({
        "ipcam_url": app_state["ipcam_url"],
        "model": os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
    })

import cv2
from flask import Response

latest_frame = None

@app.route('/api/video_feed')
def video_feed():
    def generate_frames():
        global latest_frame
        cap = cv2.VideoCapture(app_state["ipcam_url"])
        if not cap.isOpened():
            logger.error("Failed to open camera for video_feed")
            return
            
        while True:
            success, frame = cap.read()
            if not success:
                break
            latest_frame = frame.copy()
            # Compress and resize slightly for smooth UI streaming
            disp_frame = cv2.resize(frame, (640, 360))
            ret, buffer = cv2.imencode('.jpg', disp_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                   
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key')
        model_name = data.get('model_name')
        
        logger.info("Starting Vision Scan (Interactive)...")
        # SENSE
        global latest_frame
        from vision import extract_vision_telemetry, create_synthetic_test_frame
        
        if app_state["mock"]:
            logger.info("Mock mode: using synthetic frame.")
            frame = create_synthetic_test_frame()
            cv2.imwrite(app_state["png_output"], frame)
            telemetry = extract_vision_telemetry(frame)
        else:
            if latest_frame is None:
                raise RuntimeError("Failed to open camera stream. Please ensure the live feed is visible.")
            cv2.imwrite(app_state["png_output"], latest_frame)
            telemetry = extract_vision_telemetry(latest_frame)
            
        app_state["telemetry"] = telemetry
        
        # THINK
        logger.info("Generating JSON Spec...")
        json_spec, metadata = generate_json_spec(telemetry, api_key=api_key, model_override=model_name)
        app_state["json_spec"] = json_spec
        
        # ACT (CAD)
        logger.info("Generating SVG...")
        generate_svg(json_spec, app_state["plot_svg"])
        
        with open(app_state["plot_svg"], 'r') as f:
            svg_content = f.read()
            
        return jsonify({
            "status": "success",
            "svg_content": svg_content,
            "inventory_url": "/test_outputs/debug_inventory.jpg",
            "metadata": metadata
        })
    except Exception as e:
        logger.error(f"Error in generation: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/regenerate', methods=['POST'])
def api_regenerate():
    if not app_state["telemetry"]:
        return jsonify({"status": "error", "message": "No telemetry found. Run generate first."})
        
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key')
        model_name = data.get('model_name')
        
        # THINK
        logger.info("Regenerating JSON Spec...")
        json_spec, metadata = generate_json_spec(app_state["telemetry"], api_key=api_key, model_override=model_name)
        app_state["json_spec"] = json_spec
        
        # ACT (CAD)
        logger.info("Generating SVG...")
        generate_svg(json_spec, app_state["plot_svg"])
        
        with open(app_state["plot_svg"], 'r') as f:
            svg_content = f.read()
            
        return jsonify({
            "status": "success",
            "svg_content": svg_content,
            "inventory_url": "/test_outputs/debug_inventory.jpg",
            "metadata": metadata
        })
    except Exception as e:
        logger.error(f"Error in regeneration: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/stream', methods=['POST'])
def api_stream():
    try:
        # ACT (G-CODE)
        logger.info("Compiling G-Code...")
        compile_svg(svg_path=app_state["plot_svg"], gcode_path=app_state["gcode_output"])
        
        # ACT (STREAM)
        logger.info("Streaming to CNC...")
        stream_gcode(
            gcode_path=app_state["gcode_output"],
            port=app_state["serial_port"],
            baudrate=app_state["baudrate"],
            simulate=app_state["simulate"]
        )
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error in streaming: {e}")
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
