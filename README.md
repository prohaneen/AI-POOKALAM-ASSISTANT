# AI Pookalam Assistant (Onam Edition)

**A Resource-Aware Physical AI Creative Partner**

Most generative AI tools create digital images that exist only on a screen. This project bridges the gap to the physical world by acting as an intelligent, resource-aware CAD planner for the traditional Onam festival. 

It looks at your actual physical flower petal inventory through your smartphone's IP camera, intelligently designs a culturally authentic Pookalam (floral mandala) tailored perfectly to the colors and quantities you have available, and uses a custom Arduino CNC Z-Axis Pen Plotter to physically draw the guidelines on your floor.

---

## 🚀 The Volumetric JSON Architecture

This project utilizes a highly robust 4-stage pipeline designed specifically to overcome free-tier API quotas and ensure physical plotter safety. It strictly follows a **Sense -> Think -> Act** robotic architecture:

### 1. Stage 1: Local Vision Telemetry (SENSE)
The assistant autonomously connects to your smartphone's IP camera over Wi-Fi. The Web UI provides a **Live Vision Feed** so you can align your flowers perfectly. When you initiate a scan, it uses advanced OpenCV HSV color segmentation with non-overlapping masking to detect distinct flower colors. It filters out visual noise and calculates the precise volume and percentage of your available inventory.

### 2. Stage 2: Generative JSON Planner & Smart Fallbacks (THINK)
The telemetry is sent to Google's Gemini models. Gemini acts purely as a logical planner, reasoning about how to best use your specific inventory—mapping abundant colors to thick outer rings and scarce colors to inner sparse details. It strictly outputs the designs as raw JSON data.

**Interactive Web Settings & Fallback System**: 
The web interface allows you to dynamically select your preferred Gemini model (e.g., `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`) and securely input your API key. If your API key hits a quota exhaustion limit (HTTP 429), the UI will display a high-visibility warning. If all API requests fail, the system gracefully falls back to a mathematically guaranteed local deterministic generator, ensuring your physical robot always receives executable instructions.

### 3. Stage 3: Deterministic Python CAD Engine (ACT - CAD)
A custom, pure Python module parses the JSON design and uses rigorous trigonometric functions to mathematically draw the geometric vector outlines. It clamps all sizes to a predefined 70x70mm plotter boundary and forces explicitly closed paths, guaranteeing perfect robotic toolpaths (SVG). You can review and regenerate the design instantly in your browser before committing to it.

### 4. Stage 4: CNC Streaming (ACT - HARDWARE)
Once approved, the SVG is compiled into robotic instructions (G-Code) and streamed over USB Serial with standard `ok`-response handshaking to your CNC controller.

---

## 🛠️ Setup and Execution

### Prerequisites
1. Ensure your Arduino CNC plotter is plugged into your PC via USB.
2. Install the required Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set up an IP Camera app (like DroidCam or IP Webcam) on your smartphone. The default address is `http://10.136.106.51:4747/video` (this can be configured in `.env` or `app.py`).

### Running the Web Assistant
The system operates entirely through a modern, responsive local web application.

1. Start the Flask web server:
   ```powershell
   python app.py
   ```
2. Open your web browser and navigate to:
   `http://localhost:5000` (or your PC's local IP address if accessing from a phone on the same Wi-Fi network). 

From the UI, you can view the live camera feed, adjust API settings, scan your inventory, review AI-generated designs, and stream the finalized G-code directly to your plotter.

### 🤖 Hardware Note: Arduino & Mini CNC Alignment
This project is fully compatible with modern **Arduino Uno R4 WiFi** (or standard Uno/Nano) controllers running standard GRBL firmware (like grblHAL) connected via USB. The host PC maintains its connection to your home Wi-Fi for Gemini API access while simultaneously streaming G-Code over USB.

**Alignment for Mini CNC Plotters (e.g., CD Drive Plotters):**
The generated G-Code automatically sets the physical origin using `G92 X0 Y0 Z0`. Because the design is plotted within a 70x70mm bounding box (centered at 35,35), all you need to do is **manually position your pen at the bottom-left corner** of your plotting area before clicking "Accept & Stream". The CNC will treat that exact physical spot as `(0,0)` and plot safely upwards and to the right.

### Alternative CLI Modes
*If you prefer the legacy terminal interface with live diagnostic heads-up display, use:*
```powershell
python main.py --visualize
```
* **Simulated CNC** (Test the camera and AI without moving the physical robot arm):
  - In Web App: Set `app_state["simulate"] = True` inside `app.py`
  - In CLI: Run `python main.py --simulate`
* **Custom IP Camera / Port in CLI**:
  ```powershell
  python main.py --ipcam http://YOUR_PHONE_IP:PORT/video --port COM3
  ```

---

## 📂 Output Artifacts
After a successful run, review the `test_outputs/` directory to inspect the AI's internal thought process and intermediate files:
- `inventory.jpg` - The exact source frame captured for processing.
- `debug_inventory.jpg` - A visual representation of the AI's color bounding boxes.
- `plot.svg` - The mathematically generated CAD file.
- `plot.gcode` - The raw, compiled robotic instructions sent to the CNC.
