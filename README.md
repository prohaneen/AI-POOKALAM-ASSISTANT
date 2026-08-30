# AI Pookalam Assistant (Onam Edition 2026)

**A Resource-Aware Physical AI Creative Partner**

Most generative AI tools create digital images that exist only on a screen. This project bridges the gap to the physical world by acting as an intelligent, resource-aware CAD planner for the traditional Onam festival. 

<<<<<<< HEAD
It looks at your *actual* physical flower petal inventory through your smartphone's IP camera, intelligently designs a culturally authentic Pookalam (floral mandala) tailored perfectly to the colors and quantities you have available, and uses a custom Arduino CNC Z-Axis Pen Plotter to physically draw the guidelines on your floor.
=======
It looks at your *actual* physical flower petal inventory, intelligently designs a culturally authentic Pookalam (floral mandala) tailored perfectly to your constraints, and uses a custom Arduino CNC Z-Axis Pen Plotter to physically draw the guidelines on your floor.

## 🚀 The Volumetric JSON Architecture

This project utilizes a highly robust 4-stage pipeline designed specifically to overcome free-tier API quotas and ensure physical plotter safety:

1. **Stage 1: Local Vision Telemetry**
   Connects to an IP Webcam and uses local OpenCV HSV segmentation to calculate the exact percentage and volume of available flower colors (Yellow, Red, White, Orange) in your physical inventory.
2. **Stage 2: Generative JSON Planner**
   The telemetry is sent to Google's Gemini 3.6 Flash model. Gemini acts purely as a logical planner, designing a Pookalam configuration (mapping abundant colors to thick outer rings and scarce colors to inner petals). It strictly outputs the designs as raw JSON data.
   *(Note: Features a deterministic offline fallback if the API quota is exhausted).*
3. **Stage 3: Deterministic Python CAD Engine**
   A custom pure Python module parses the JSON design and uses rigorous Sine/Cosine trigonometry to mathematically draw the geometric vector outlines. It clamps all sizes to the 70x70mm plotter bounds and forces explicitly closed paths, guaranteeing perfect G-Code.
4. **Stage 4: CNC Streaming**
   The SVG is compiled into robotic instructions (G-Code) and streamed over USB Serial with standard ok-response handshaking to an Arduino GRBL Z-Axis plotter.
>>>>>>> 8d114c0637001f6ff293048f9e4f2e55af5fb3f3

---

## 🚀 The Volumetric JSON Architecture

This project utilizes a highly robust 4-stage pipeline designed specifically to overcome free-tier API quotas and ensure physical plotter safety. It strictly follows a **Sense -> Think -> Act** robotic architecture:

### 1. Stage 1: Local Vision Telemetry (SENSE)
The assistant autonomously connects to your smartphone's IP camera over Wi-Fi. The new Web UI provides a **Live Vision Feed** so you can align your flowers. When you initiate a scan, it uses advanced OpenCV HSV color segmentation with non-overlapping masking to detect up to 8 distinct flower colors (Red, Orange, Golden Yellow, Yellow, Pink, Green, Blue, Purple). It filters out noise and calculates the precise volume and percentage of your available inventory.

### 2. Stage 2: Generative JSON Planner & Smart Fallbacks (THINK)
The telemetry is sent to Google's Gemini models. Gemini acts purely as a logical planner, reasoning about how to best use your specific inventory (mapping abundant colors to thick outer rings and scarce colors to inner sparse details). It strictly outputs the designs as raw JSON data.

**Interactive Web Settings & Fallback System**: 
The web interface allows you to dynamically select your Gemini model (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, etc.) and securely input your API key. If your API key hits a `429 Quota Exhausted` limit, the UI will display a high-visibility warning. If all API requests fail, the system gracefully falls back to a mathematically guaranteed local deterministic generator—ensuring your physical robot always receives instructions.

### 3. Stage 3: Deterministic Python CAD Engine (ACT - CAD)
A custom pure Python module parses the JSON design and uses rigorous Sine/Cosine trigonometry to mathematically draw the geometric vector outlines. It clamps all sizes to a 70x70mm plotter bounds and forces explicitly closed paths, guaranteeing perfect robotic toolpaths (SVG). You can review and regenerate the design instantly in your browser before committing to it.

### 4. Stage 4: CNC Streaming (ACT - HARDWARE)
Once approved, the SVG is compiled into robotic instructions (G-Code) and streamed over USB Serial with standard `ok`-response handshaking to your CNC controller.

---

## 🛠️ How to Setup and Run

### Prerequisites
1. Ensure your Arduino CNC plotter is plugged into your PC via USB.
2. Install the required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set up an IP Camera app (like DroidCam or IP Webcam) on your phone. The default address is `http://10.136.106.51:4747/video` (can be changed in `.env` or `app.py`).

### Running the Web Assistant

The system has been upgraded to a modern, glassmorphic local web application.

Start the Flask web server:
```powershell
python app.py
```
<<<<<<< HEAD
Then, open your browser and navigate to:
`http://localhost:5000` (or your PC's local IP address if accessing from a phone on the same Wi-Fi). 
=======
1. Position your camera over your flower piles.
2. Press `[ENTER]` when the camera is in focus.
3. The AI will generate a logical designs. The interactive menu allows you to either select it for plotting or regenerate the design until a satisfactory one is obtained.
4. The system instantly compiles the math and streams it to the plotter.
>>>>>>> 8d114c0637001f6ff293048f9e4f2e55af5fb3f3

From the UI, you can view the live camera feed, adjust API settings, scan your inventory, review designs, and stream G-code directly to your plotter.

### 🤖 Hardware Note: Arduino Uno R4 & Mini CNC Alignment
This project can use the modern **Arduino Uno R4 WiFi** (or standard Uno/Nano) running standard GRBL firmware (like grblHAL) connected via USB. The PC maintains its connection to your home Wi-Fi for Gemini API access while streaming G-Code over USB.

**Alignment for Mini CNC Plotters (e.g. CD Drive Plotters):**
The generated G-Code automatically sets the physical origin using `G92 X0 Y0 Z0`. Because the design is plotted within a 70x70mm bounding box (centered at 35,35), all you need to do is **manually position your pen at the bottom-left corner** of your plotting area before clicking "Accept & Stream". The CNC will treat that exact spot as (0,0) and plot safely upwards and to the right.

### Alternative CLI Modes
*If you prefer the legacy terminal interface with live diagnostic heads-up display, use:*
```powershell
python main.py --visualize
```
* **Simulated CNC** (Test the camera and AI without the robot arm moving):
  - In Web App: Edit `app_state["simulate"] = True` in `app.py`
  - In CLI: `python main.py --simulate`
* **Custom IP Camera / Port in CLI**:
  ```powershell
  python main.py --ipcam http://YOUR_PHONE_IP:PORT/video --port COM3
  ```

---

## 📂 Output Artifacts
After a successful run, check the `test_outputs/` directory to review the AI's internal thought process:
- `inventory.jpg` - The exact frame captured for processing.
- `debug_inventory.jpg` - Visual representation of the AI's color bounding boxes.
- `plot.svg` - The mathematical CAD file generated from the JSON.
- `plot.gcode` - The raw robotic instructions sent to the CNC.
