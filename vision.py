import cv2
import numpy as np
import logging
import json
import time
from typing import Optional, Tuple
from config import SETTINGS
import os

logger = logging.getLogger("PookalamVision")

def create_synthetic_test_frame() -> np.ndarray:
    frame = np.ones((SETTINGS.frame_height, SETTINGS.frame_width, 3), dtype=np.uint8) * 200
    cv2.circle(frame, (200, 200), 100, (0, 255, 255), -1) # Yellow LARGE
    cv2.circle(frame, (400, 300), 50, (0, 0, 255), -1)   # Red MEDIUM
    cv2.circle(frame, (100, 400), 20, (147, 20, 255), -1) # Pink SMALL
    return frame

# Define HSV color ranges (Hue: 0-179, Saturation: 0-255, Value: 0-255)
COLOR_RANGES = {
    "Red": [
        ((0, 80, 50), (10, 255, 255)),
        ((170, 80, 50), (179, 255, 255))
    ],
    "Orange": [
        ((10, 80, 50), (22, 255, 255))
    ],
    "Golden Yellow": [
        ((20, 80, 70), (32, 255, 255))
    ],
    "Yellow": [
        ((32, 60, 70), (45, 255, 255))
    ],
    "Pink": [
        ((145, 15, 60), (179, 255, 255))
    ],
    "Green": [
        ((40, 40, 40), (90, 255, 255))
    ],
    "Blue": [
        ((90, 50, 40), (130, 255, 255))
    ],
    "Purple": [
        ((130, 40, 40), (160, 255, 255))
    ]
}

def extract_vision_telemetry(frame: np.ndarray) -> str:
    frame = cv2.resize(frame, (960, 540))

    x1, y1 = 100, 70
    x2, y2 = 860, 500

    roi = frame[y1:y2, x1:x2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    classified_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

    color_areas = {}

    for colour, ranges in COLOR_RANGES.items():
        colour_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

        for lower, upper in ranges:
            lower = np.array(lower)
            upper = np.array(upper)
            temp = cv2.inRange(hsv, lower, upper)
            colour_mask = cv2.bitwise_or(colour_mask, temp)

        colour_mask[classified_mask > 0] = 0

        kernel = np.ones((5, 5), np.uint8)
        colour_mask = cv2.morphologyEx(colour_mask, cv2.MORPH_OPEN, kernel)
        colour_mask = cv2.morphologyEx(colour_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(colour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        colour_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:
                continue

            colour_area += area

            x, y, w, h = cv2.boundingRect(contour)
            cv2.drawContours(classified_mask, [contour], -1, 255, thickness=cv2.FILLED)
            cv2.rectangle(roi, (x, y), (x + w, y + h), (255, 255, 255), 2)
            cv2.putText(roi, colour, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if colour_area > 0:
            color_areas[colour] = colour_area

    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
    cv2.putText(frame, "FLOWER DETECTION AREA", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Save visualization to a debug file so you can view the detection results
    cv2.imwrite('test_outputs/debug_inventory.jpg', frame)

    if not color_areas:
        return json.dumps({"telemetry": "No distinct flowers detected."})

    largest_color = max(color_areas, key=color_areas.get)
    max_area = color_areas[largest_color]
    logger.info(f"Largest color identified: {largest_color} ({max_area} pixels)")

    total_flower_pixels = sum(color_areas.values())
    telemetry = {}
    for color, count in color_areas.items():
        pct = (count / total_flower_pixels) * 100
        if pct > 40:
            vol = "LARGE"
        elif pct > 15:
            vol = "MEDIUM"
        else:
            vol = "SMALL"
        telemetry[color] = {"percentage": round(pct, 1), "volume": vol}
        
    return json.dumps({"available_inventory": telemetry, "largest_color": largest_color})

def autonomous_inventory_scan(stream_url: Optional[str] = None, mock: bool = False, visualize: bool = False, output_path: str = 'test_outputs/inventory.jpg') -> Tuple[str, str]:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if mock:
        logger.info("[INFO] Operating in mock mode. Simulating stillness.")
        frame = create_synthetic_test_frame()
        cv2.imwrite(output_path, frame)
        return output_path, extract_vision_telemetry(frame)
        
    source = stream_url if stream_url else 0
    logger.info(f"==> SENSE: Initializing autonomous scanner at {source}")
    
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError("Failed to open camera stream.")
        
    logger.info("[VISION] Watching frame for motion. Place flowers now...")
    
    prev_gray = None
    still_start_time = None
    target_stillness = 3.0
    locked_frame = None
    
    # Motion detection threshold
    MIN_MOTION_AREA = 1000
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_gray is None:
                prev_gray = gray
                continue
                
            # Compute difference
            frame_diff = cv2.absdiff(prev_gray, gray)
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            motion_pixels = cv2.countNonZero(thresh)
            
            if motion_pixels > MIN_MOTION_AREA:
                if still_start_time is not None:
                    logger.info("[VISION] Motion detected. Timer reset.")
                still_start_time = None
                status = "Moving..."
                color = (0, 0, 255)
            else:
                if still_start_time is None:
                    still_start_time = time.time()
                    
                elapsed = time.time() - still_start_time
                status = f"Still: {elapsed:.1f}s / {target_stillness}s"
                color = (0, 255, 0)
                
                if elapsed >= target_stillness:
                    logger.info("[INFO] Inventory captured autonomously")
                    locked_frame = frame.copy()
                    break
                    
            if visualize:
                disp = frame.copy()
                cv2.putText(disp, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.imshow("Autonomous Scanner", disp)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            prev_gray = gray
    finally:
        cap.release()
        if visualize:
            cv2.destroyAllWindows()
            
    if locked_frame is None:
        raise ValueError("Failed to capture inventory.")
        
    cv2.imwrite(output_path, locked_frame)
    payload = extract_vision_telemetry(locked_frame)
    logger.info(f"[VISION] Sensed Payload: {payload}")
    return output_path, payload
