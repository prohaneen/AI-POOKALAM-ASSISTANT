"""
AI Pookalam Assistant - Vision Module (Adaptive Color & Spatial Detection)
Handles IP webcam streaming, synthetic evaluation frames, HSV segmentation,
spatial horizontal band analysis, and structured JSON telemetry.
"""

import json
import logging
import argparse
from typing import Dict, List, Any, Tuple, Optional
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("PookalamVision")

# -------------------------------------------------------------------------
# Calibrated HSV Color Ranges (Hue: 0-180, Saturation: 0-255, Value: 0-255)
# Includes tolerances for paper reflections, shadows, and white balance
# -------------------------------------------------------------------------
COLOR_RANGES: Dict[str, List[Tuple[np.ndarray, np.ndarray]]] = {
    "Indigo": [
        (np.array([115, 80, 40]), np.array([135, 255, 200]))
    ],
    "Blue": [
        (np.array([98, 90, 50]), np.array([115, 255, 255]))
    ],
    "Pink/Orchid": [
        (np.array([140, 50, 110]), np.array([170, 255, 255]))
    ],
    "Golden Yellow": [
        (np.array([18, 120, 130]), np.array([28, 255, 255]))
    ],
    "Yellow": [
        (np.array([28, 80, 150]), np.array([38, 255, 255]))
    ],
    "Orange": [
        (np.array([10, 120, 130]), np.array([18, 255, 255]))
    ],
    "Red": [
        (np.array([0, 100, 70]), np.array([9, 255, 255])),
        (np.array([170, 100, 70]), np.array([180, 255, 255]))
    ],
    "Violet": [
        (np.array([128, 50, 50]), np.array([142, 255, 210]))
    ],
    "White": [
        (np.array([0, 0, 180]), np.array([180, 45, 255]))
    ]
}


def create_synthetic_test_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """
    Generates a synthetic 3-band horizontal paper evaluation frame:
      - Top Band:    Indigo / Dark Blue (RGB: 55, 45, 165)
      - Middle Band: Pink / Orchid       (RGB: 225, 135, 215)
      - Bottom Band: Golden Yellow       (RGB: 225, 190, 55)
    Note: OpenCV uses BGR ordering.
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    band_height = height // 3

    # Top Band: Indigo (BGR: 165, 45, 55)
    frame[0:band_height, :] = [165, 45, 55]

    # Middle Band: Pink/Orchid (BGR: 215, 135, 225)
    frame[band_height:2 * band_height, :] = [215, 135, 225]

    # Bottom Band: Golden Yellow (BGR: 55, 190, 225)
    frame[2 * band_height:height, :] = [55, 190, 225]

    return frame


def capture_frame(stream_url: Optional[str] = None, mock: bool = False) -> np.ndarray:
    """
    Captures a frame from an IP Webcam stream, local camera index, or returns a synthetic frame.
    """
    if mock or not stream_url:
        logger.info("[INFO] Operating in synthetic mock mode.")
        return create_synthetic_test_frame()

    logger.info(f"[INFO] Connecting to camera stream at {stream_url}...")
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        logger.warning("[WARNING] Unable to open video stream. Falling back to mock frame.")
        return create_synthetic_test_frame()

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        logger.warning("[WARNING] Failed to grab frame from stream. Falling back to mock frame.")
        return create_synthetic_test_frame()

    return frame


def segment_color(hsv_img: np.ndarray, color_name: str) -> np.ndarray:
    """
    Generates a cleaned binary mask for a specified color range using morphological operations.
    """
    ranges = COLOR_RANGES.get(color_name, [])
    full_mask = np.zeros(hsv_img.shape[:2], dtype=np.uint8)

    for lower, upper in ranges:
        mask = cv2.inRange(hsv_img, lower, upper)
        full_mask = cv2.bitwise_or(full_mask, mask)

    # Clean salt-and-pepper noise and bridge minor paper gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cleaned_mask = cv2.morphologyEx(full_mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    return cleaned_mask


def calculate_color_percentages(frame: np.ndarray) -> Dict[str, float]:
    """
    Calculates overall frame percentage for all supported colors.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    total_pixels = frame.shape[0] * frame.shape[1]
    percentages = {}

    for color_name in COLOR_RANGES.keys():
        mask = segment_color(hsv, color_name)
        count = cv2.countNonZero(mask)
        pct = round((count / total_pixels) * 100.0, 2)
        percentages[color_name] = pct

    return percentages


def get_dominant_colors(percentages: Dict[str, float], top_n: int = 3) -> List[str]:
    """
    Returns the top N dominant detected colors that have a coverage > 1.0%.
    """
    filtered = {k: v for k, v in percentages.items() if v > 1.0}
    sorted_colors = sorted(filtered.items(), key=lambda item: item[1], reverse=True)
    return [color for color, _ in sorted_colors[:top_n]]


def detect_spatial_bands(frame: np.ndarray) -> List[Dict[str, Any]]:
    """
    Performs horizontal spatial band analysis (Top, Middle, Bottom).
    Calculates the primary color and confidence metric for each slice.
    """
    h, w, _ = frame.shape
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    band_defs = [
        ("top", 0, int(h * 0.33)),
        ("middle", int(h * 0.33), int(h * 0.66)),
        ("bottom", int(h * 0.66), h)
    ]

    detected_bands = []

    for position_name, y_start, y_end in band_defs:
        band_hsv = hsv[y_start:y_end, :]
        band_pixels = band_hsv.shape[0] * band_hsv.shape[1]

        best_color = "Unknown"
        max_coverage = 0

        for color_name in COLOR_RANGES.keys():
            mask = segment_color(band_hsv, color_name)
            count = cv2.countNonZero(mask)
            if count > max_coverage:
                max_coverage = count
                best_color = color_name

        confidence = round(max_coverage / band_pixels, 2) if band_pixels > 0 else 0.0

        if confidence >= 0.15:  # Minimum 15% band occupancy
            detected_bands.append({
                "position": position_name,
                "color": best_color,
                "confidence": confidence
            })

    return detected_bands


def analyze_scene(frame: np.ndarray) -> Dict[str, Any]:
    """
    Main vision analysis pipeline. Returns a structured observation payload.
    """
    percentages = calculate_color_percentages(frame)
    dominant = get_dominant_colors(percentages, top_n=3)
    bands = detect_spatial_bands(frame)

    return {
        "dominant_colors": dominant,
        "color_percentages": percentages,
        "bands": bands
    }


def draw_debug_visualization(frame: np.ndarray, analysis: Dict[str, Any]) -> np.ndarray:
    """
    Renders diagnostic HUD overlay showing horizontal bands, labels, and confidence.
    """
    vis = frame.copy()
    h, w, _ = frame.shape

    cv2.line(vis, (0, int(h * 0.33)), (w, int(h * 0.33)), (255, 255, 255), 2)
    cv2.line(vis, (0, int(h * 0.66)), (w, int(h * 0.66)), (255, 255, 255), 2)

    positions = {
        "top": int(h * 0.18),
        "middle": int(h * 0.50),
        "bottom": int(h * 0.83)
    }

    for band in analysis.get("bands", []):
        pos = band["position"]
        color = band["color"]
        conf = band["confidence"]
        y_pos = positions.get(pos, int(h * 0.5))

        label = f"{pos.upper()}: {color} ({int(conf * 100)}%)"
        cv2.rectangle(vis, (20, y_pos - 25), (340, y_pos + 10), (0, 0, 0), -1)
        cv2.putText(vis, label, (30, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    return vis


def print_diagnostic_output(analysis: Dict[str, Any]) -> None:
    """
    Outputs structured diagnostic logging to standard output.
    """
    print("\n" + "=" * 60)
    print("[Adaptive Pookalam] - Vision Color Detection System")
    print("=" * 60)
    print("\n[INFO] Running evaluation-paper detection...\n")

    print("--- Color Distribution ---")
    for color, pct in analysis["color_percentages"].items():
        print(f"{color:<15}: {pct:>6.2f}%")

    print("\n--- Spatial Analysis ---")
    for band in analysis["bands"]:
        print(f"{band['position'].upper():<8} -> {band['color']} (Conf: {band['confidence'] * 100:.0f}%)")

    print("\n--- Dominant Colors ---")
    for idx, color in enumerate(analysis["dominant_colors"], 1):
        print(f"{idx}. {color}")

    print("\n--- Structured Observation (JSON) ---")
    print(json.dumps(analysis, indent=4))
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive Pookalam Vision Module")
    parser.add_argument("--ipcam", type=str, default=None, help="IP Webcam stream URL")
    parser.add_argument("--mock", action="store_true", help="Use synthetic evaluation test frame")
    parser.add_argument("--visualize", action="store_true", help="Save debug visualization image")
    args = parser.parse_args()

    test_frame = capture_frame(stream_url=args.ipcam, mock=args.mock)
    observation = analyze_scene(test_frame)
    print_diagnostic_output(observation)

    if args.visualize:
        debug_img = draw_debug_visualization(test_frame, observation)
        cv2.imwrite("vision_debug_overlay.png", debug_img)
        print("[INFO] Debug visualization saved to 'vision_debug_overlay.png'")