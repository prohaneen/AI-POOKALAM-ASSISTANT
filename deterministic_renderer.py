"""
Deterministic CAD Renderer for AI Pookalam Assistant.
Translates JSON design specifications into mathematically closed SVG curves (for CNC plotting)
and high-resolution OpenCV image previews.
"""

import os
import math
import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import cv2

from config import SETTINGS

logger = logging.getLogger("PookalamCAD")

Point = Tuple[float, float]

COLOR_BGR_MAP = {
    "Yellow": (30, 225, 250),
    "Golden Yellow": (20, 190, 255),
    "Red": (40, 40, 225),
    "Orange": (20, 130, 255),
    "Pink": (190, 110, 255),
    "Pink/Orchid": (215, 135, 225),
    "White": (245, 245, 245),
    "Green": (60, 185, 60),
    "Blue": (225, 120, 30),
    "Indigo": (165, 45, 55),
    "Purple": (180, 50, 140),
    "Violet": (180, 50, 140),
}

def _get_bgr_color(color_name: str) -> Tuple[int, int, int]:
    if not color_name:
        return (200, 200, 200)
    for key, val in COLOR_BGR_MAP.items():
        if key.lower() == color_name.lower() or key.lower() in color_name.lower():
            return val
    return (200, 200, 200)

def _point(cx: float, cy: float, r: float, a: float) -> Point:
    return (cx + r * math.cos(a), cy + r * math.sin(a))

def _sample_cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point, n: int = 16) -> List[Point]:
    pts = []
    for k in range(n + 1):
        t = k / n
        omt = 1.0 - t
        x = (omt**3)*p0[0] + 3*(omt**2)*t*p1[0] + 3*omt*(t**2)*p2[0] + (t**3)*p3[0]
        y = (omt**3)*p0[1] + 3*(omt**2)*t*p1[1] + 3*omt*(t**2)*p2[1] + (t**3)*p3[1]
        pts.append((x, y))
    return pts

def _curved_petal_points(cx: float, cy: float, inner: float, outer: float, angle: float, half_angle: float) -> List[Point]:
    """Generates sample points for a smooth closed petal."""
    start = _point(cx, cy, inner, angle - half_angle)
    tip = _point(cx, cy, outer, angle)
    end = _point(cx, cy, inner, angle + half_angle)

    c1 = _point(cx, cy, inner + (outer - inner) * 0.46, angle - half_angle * 0.82)
    c2 = _point(cx, cy, outer * 0.94, angle - half_angle * 0.18)
    c3 = _point(cx, cy, outer * 0.94, angle + half_angle * 0.18)
    c4 = _point(cx, cy, inner + (outer - inner) * 0.46, angle + half_angle * 0.82)

    # Base curve connecting back to start
    c5 = _point(cx, cy, inner * 0.85, angle + half_angle * 0.45)
    c6 = _point(cx, cy, inner * 0.85, angle - half_angle * 0.45)

    side1 = _sample_cubic_bezier(start, c1, c2, tip, 12)
    side2 = _sample_cubic_bezier(tip, c3, c4, end, 12)[1:]
    base = _sample_cubic_bezier(end, c5, c6, start, 8)[1:]

    return side1 + side2 + base

def _scallop_points(cx: float, cy: float, inner: float, outer: float, angle: float, half_angle: float) -> List[Point]:
    """Generates sample points for a rounded scallop arch."""
    start = _point(cx, cy, inner, angle - half_angle)
    peak = _point(cx, cy, outer, angle)
    end = _point(cx, cy, inner, angle + half_angle)

    c1 = _point(cx, cy, outer * 0.98, angle - half_angle * 0.4)
    c2 = _point(cx, cy, outer * 0.98, angle + half_angle * 0.4)

    arc = _sample_cubic_bezier(start, c1, c2, end, 12)
    base = _sample_cubic_bezier(end, _point(cx, cy, inner * 0.9, angle), _point(cx, cy, inner * 0.9, angle), start, 6)[1:]
    return arc + base

def _star_points(cx: float, cy: float, inner: float, outer: float, count: int) -> List[Point]:
    pts = []
    for i in range(count * 2):
        r = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / count
        pts.append(_point(cx, cy, r, angle))
    pts.append(pts[0])  # Explicitly close
    return pts

def parse_spec_layers(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Standardizes JSON specs from Gemini or fallback into normalized layer definitions."""
    raw_layers = spec.get("layers", [])
    if not raw_layers and "outer_boundary" in spec:
        layers = [{"radius_mm": spec["outer_boundary"].get("radius_mm", 30), "pattern": "circle", "element_count": 1, "color": spec["outer_boundary"].get("color", "Golden Yellow")}]
        for ly in spec.get("layers", []):
            pt = "petals" if "petal" in ly.get("type", "") else ("scallop" if "scallop" in ly.get("type", "") else "star")
            layers.append({
                "radius_mm": ly.get("outer_radius_mm", ly.get("radius_mm", 20)),
                "inner_radius_mm": ly.get("inner_radius_mm", 10),
                "pattern": pt,
                "element_count": ly.get("count", ly.get("points", 8)),
                "color": ly.get("color", "Red")
            })
        return layers

    normalized = []
    for idx, ly in enumerate(raw_layers):
        r = float(ly.get("radius_mm", max(5.0, 30.0 - idx * 7.0)))
        r = min(30.0, max(4.0, r))
        pattern = str(ly.get("pattern", ly.get("type", "circle"))).lower()
        if "petal" in pattern:
            pattern = "petals"
        elif "scallop" in pattern:
            pattern = "scallop"
        elif "star" in pattern:
            pattern = "star"
        else:
            pattern = "circle"

        count = int(ly.get("element_count", ly.get("count", ly.get("points", 8 if pattern != "circle" else 1))))
        count = max(3, min(24, count)) if pattern != "circle" else 1
        color = str(ly.get("color", "Yellow"))

        inner_r = float(ly.get("inner_radius_mm", r * 0.55))
        normalized.append({
            "radius_mm": r,
            "inner_radius_mm": inner_r,
            "pattern": pattern,
            "element_count": count,
            "color": color
        })

    # Sort descending by outer radius
    normalized.sort(key=lambda x: x["radius_mm"], reverse=True)
    return normalized

def generate_svg(json_spec: Dict[str, Any], output_path: str = None) -> str:
    """Generates standard SVG XML string from JSON design specification."""
    cx, cy = 35.0, 35.0  # Center of 70x70mm bed
    layers = parse_spec_layers(json_spec)

    svg_paths = []
    # Add outermost bounding ring
    max_r = max((ly["radius_mm"] for ly in layers), default=30.0)
    svg_paths.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{max_r:.2f}" fill="none" stroke="black" stroke-width="0.35"/>')

    for ly in layers:
        pattern = ly["pattern"]
        r = ly["radius_mm"]
        inner_r = ly["inner_radius_mm"]
        count = ly["element_count"]
        color = ly["color"]

        if pattern == "circle":
            svg_paths.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="{color}" stroke-width="0.35"/>')
        elif pattern == "petals":
            for i in range(count):
                angle = 2 * math.pi * i / count
                half_angle = math.pi / count * 0.7
                pts = _curved_petal_points(cx, cy, inner_r, r, angle, half_angle)
                d = "M " + " L ".join(f"{x:.3f} {y:.3f}" for x, y in pts) + " Z"
                svg_paths.append(f'<path d="{d}" fill="{color}" fill-opacity="0.75" stroke="{color}" stroke-width="0.35"/>')
        elif pattern == "scallop":
            for i in range(count):
                angle = 2 * math.pi * i / count
                half_angle = math.pi / count
                pts = _scallop_points(cx, cy, inner_r, r, angle, half_angle)
                d = "M " + " L ".join(f"{x:.3f} {y:.3f}" for x, y in pts) + " Z"
                svg_paths.append(f'<path d="{d}" fill="{color}" fill-opacity="0.75" stroke="{color}" stroke-width="0.35"/>')
        elif pattern == "star":
            pts = _star_points(cx, cy, inner_r * 0.6, r, count)
            d = "M " + " L ".join(f"{x:.3f} {y:.3f}" for x, y in pts) + " Z"
            svg_paths.append(f'<path d="{d}" fill="{color}" fill-opacity="0.85" stroke="{color}" stroke-width="0.35"/>')

    svg_content = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="70mm" height="70mm" viewBox="0 0 70 70">\n'
        + "\n".join(svg_paths)
        + "\n</svg>"
    )

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        logger.info(f"[CAD] Successfully generated SVG: {output_path}")

    return svg_content

def render_pookalam_image(json_spec: Dict[str, Any], size: int = 600) -> np.ndarray:
    """Renders the mathematical Pookalam geometry into an OpenCV BGR image for UI preview."""
    canvas = np.full((size, size, 3), 28, dtype=np.uint8)  # Deep dark slate background
    cx = size / 2.0
    cy = size / 2.0
    scale = (size * 0.42) / 30.0  # Scale 30mm to fit nicely with padding

    layers = parse_spec_layers(json_spec)

    # Draw faint circular alignment grid lines
    for grid_r in [10, 20, 30]:
        cv2.circle(canvas, (int(cx), int(cy)), int(grid_r * scale), (45, 45, 45), 1, cv2.LINE_AA)

    # Render each layer (outermost to innermost)
    for ly in layers:
        pattern = ly["pattern"]
        r = ly["radius_mm"]
        inner_r = ly["inner_radius_mm"]
        count = ly["element_count"]
        bgr = _get_bgr_color(ly["color"])

        if pattern == "circle":
            cv2.circle(canvas, (int(cx), int(cy)), int(r * scale), bgr, 2, cv2.LINE_AA)
        elif pattern == "petals":
            for i in range(count):
                angle = 2 * math.pi * i / count
                half_angle = math.pi / count * 0.7
                pts = _curved_petal_points(0, 0, inner_r * scale, r * scale, angle, half_angle)
                pts_int = np.array([[int(cx + x), int(cy + y)] for x, y in pts], dtype=np.int32)
                overlay = canvas.copy()
                cv2.fillPoly(overlay, [pts_int], bgr, lineType=cv2.LINE_AA)
                cv2.addWeighted(overlay, 0.75, canvas, 0.25, 0, canvas)
                cv2.polylines(canvas, [pts_int], True, (255, 255, 255), 1, cv2.LINE_AA)
        elif pattern == "scallop":
            for i in range(count):
                angle = 2 * math.pi * i / count
                half_angle = math.pi / count
                pts = _scallop_points(0, 0, inner_r * scale, r * scale, angle, half_angle)
                pts_int = np.array([[int(cx + x), int(cy + y)] for x, y in pts], dtype=np.int32)
                overlay = canvas.copy()
                cv2.fillPoly(overlay, [pts_int], bgr, lineType=cv2.LINE_AA)
                cv2.addWeighted(overlay, 0.75, canvas, 0.25, 0, canvas)
                cv2.polylines(canvas, [pts_int], True, (255, 255, 255), 1, cv2.LINE_AA)
        elif pattern == "star":
            pts = _star_points(0, 0, inner_r * 0.6 * scale, r * scale, count)
            pts_int = np.array([[int(cx + x), int(cy + y)] for x, y in pts], dtype=np.int32)
            overlay = canvas.copy()
            cv2.fillPoly(overlay, [pts_int], bgr, lineType=cv2.LINE_AA)
            cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
            cv2.polylines(canvas, [pts_int], True, (255, 255, 255), 1, cv2.LINE_AA)

    # Draw center dot
    cv2.circle(canvas, (int(cx), int(cy)), 3, (255, 255, 255), -1, cv2.LINE_AA)
    return canvas

