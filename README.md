# AI Pookalam Assistant (Onam Edition 2026)

**A Resource-Aware Physical AI Creative Partner**

Most generative AI tools create digital images that exist only on a screen. This project bridges the gap to the physical world by acting as an intelligent, resource-aware CAD planner for the traditional Onam festival. 

It looks at your *actual* physical flower petal inventory, intelligently designs a culturally authentic Pookalam (floral mandala) tailored perfectly to your constraints, and uses a custom Arduino CNC Z-Axis Pen Plotter to physically draw the guidelines on your floor.

## 🚀 The Volumetric JSON Architecture

This project utilizes a highly robust 4-stage pipeline designed specifically to overcome free-tier API quotas and ensure physical plotter safety:

1. **Stage 1: Local Vision Telemetry**
   Connects to an IP Webcam and uses local OpenCV HSV segmentation to calculate the exact percentage and volume of available flower colors (Yellow, Red, White, Orange) in your physical inventory.
2. **Stage 2: Generative JSON Planner**
   The telemetry is sent to Google's Gemini 3.6 Flash model. Gemini acts purely as a logical planner, designing 3 Pookalam configurations (mapping abundant colors to thick outer rings and scarce colors to inner petals). It strictly outputs the designs as raw JSON data.
   *(Note: Features a deterministic offline fallback if the API quota is exhausted).*
3. **Stage 3: Deterministic Python CAD Engine**
   A custom pure Python module parses the JSON design and uses rigorous Sine/Cosine trigonometry to mathematically draw the geometric vector outlines. It clamps all sizes to the 70x70mm plotter bounds and forces explicitly closed paths, guaranteeing perfect G-Code.
4. **Stage 4: CNC Streaming**
   The SVG is compiled into robotic instructions (G-Code) and streamed over USB Serial with standard ok-response handshaking to an Arduino GRBL Z-Axis plotter.

---

## 🛠️ How to Run the Software

Make sure you have your dependencies installed:
`pip install -r requirements.txt`

You have three ways to run the Assistant depending on your demo needs:

### Option 1: The Full Hardware Demo
*Requires a live IP camera stream and the Arduino CNC plugged in via USB.*
```powershell
python main.py --ipcam http://YOUR_PHONE_IP:8080/video --port COM3 --baud 115200
```
1. Position your camera over your flower piles.
2. Press `[ENTER]` when the camera is in focus.
3. The AI will generate 3 text-based logical designs. Enter `1`, `2`, or `3` to pick your favorite.
4. The system instantly compiles the math and streams it to the plotter.

### Option 2: Live Camera + Simulated CNC
*Use this to test the camera and AI with real flowers without moving the robotic arm.*
```powershell
python main.py --ipcam http://YOUR_PHONE_IP:8080/video --simulate
```

### Option 3: Full Mock Mode (Fastest for quick demos)
*Runs instantly without needing a camera or the physical robot. Uses a synthetic color image.*
```powershell
python main.py --mock --simulate
```
