"""
AI Pookalam Assistant - G-Code Converter Module
Converts PNG mandala designs into vector SVG using vtracer and compiles
G-Code for a 70x70mm CNC pen-plotter bed with micro-servo Z-axis control.
"""

import os
import sys
import argparse
import logging
import cv2
import numpy as np
from typing import List, Tuple
import vtracer
from svg_to_gcode.compiler import Compiler, interfaces
from svg_to_gcode.svg_parser import parse_file

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("PookalamConverter")


class ServoInterface(interfaces.Gcode):
    """
    Custom G-Code interface for Arduino/GRBL CNC pen-plotters.
    Overrides laser/spindle power commands to control a Z-axis micro-servo:
      - M3 S0:  Pen UP   (Servo at 0 degrees / lifted)
      - M3 S90: Pen DOWN (Servo at 90 degrees / drawing contact)
    """

    def laser_off(self) -> str:
        """Pen UP position (servo 0 degrees)."""
        return "M3 S0"

    def set_laser_power(self, power: float) -> str:
        """Pen DOWN position (servo 90 degrees)."""
        return "M3 S90"


def scale_curves_to_bed(
    curves: List[any],
    target_width: float = 70.0,
    target_height: float = 70.0,
    margin: float = 2.0
) -> Tuple[float, float, float, float]:
    """
    Calculates the bounding box across all parsed geometric curves,
    scales them uniformly to fit strictly within target dimensions (e.g. 70x70mm),
    and centers them with a specified margin.
    """
    all_vectors = []
    for curve in curves:
        for attr in ("start", "end", "control1", "control2"):
            if hasattr(curve, attr):
                v = getattr(curve, attr)
                if v is not None:
                    all_vectors.append(v)

    if not all_vectors:
        return 0.0, 0.0, 0.0, 0.0

    min_x = min(v.x for v in all_vectors)
    max_x = max(v.x for v in all_vectors)
    min_y = min(v.y for v in all_vectors)
    max_y = max(v.y for v in all_vectors)

    orig_width = max_x - min_x
    orig_height = max_y - min_y

    # Usable plotting boundary after margin
    usable_w = max(target_width - (2 * margin), 1.0)
    usable_h = max(target_height - (2 * margin), 1.0)

    # Uniform scale factor preserving aspect ratio
    scale = min(usable_w / max(orig_width, 1e-5), usable_h / max(orig_height, 1e-5))

    scaled_w = orig_width * scale
    scaled_h = orig_height * scale

    # Centering offsets
    offset_x = margin + (usable_w - scaled_w) / 2.0
    offset_y = margin + (usable_h - scaled_h) / 2.0

    for v in all_vectors:
        v.x = (v.x - min_x) * scale + offset_x
        v.y = (v.y - min_y) * scale + offset_y

    new_min_x = min(v.x for v in all_vectors)
    new_max_x = max(v.x for v in all_vectors)
    new_min_y = min(v.y for v in all_vectors)
    new_max_y = max(v.y for v in all_vectors)

    return new_min_x, new_max_x, new_min_y, new_max_y


def convert_to_gcode(
    png_path: str = "pookalam.png",
    gcode_path: str = "plot.gcode",
    target_width: float = 70.0,
    target_height: float = 70.0,
    feedrate_travel: int = 1200,
    feedrate_draw: int = 800
) -> str:
    """
    Traces a PNG image to SVG using vtracer and compiles it into scaled G-Code
    configured for 70x70 mm plotting with micro-servo pen commands.

    :param png_path: Input PNG image filepath.
    :param gcode_path: Output G-Code filepath (default: 'plot.gcode').
    :param target_width: Maximum X dimension in mm (default: 70.0).
    :param target_height: Maximum Y dimension in mm (default: 70.0).
    :param feedrate_travel: Rapid travel speed (mm/min).
    :param feedrate_draw: Drawing speed (mm/min).
    :return: Absolute or relative path to the generated G-Code file.
    """
    if not os.path.exists(png_path):
        raise FileNotFoundError(f"Input image not found: {png_path}")

    svg_temp_path = os.path.splitext(png_path)[0] + ".svg"
    processed_png_path = os.path.splitext(png_path)[0] + "_processed.png"
    
    logger.info("=" * 60)
    logger.info("[Adaptive Pookalam] - G-Code Vectorization & Compilation")
    logger.info("=" * 60)
    
    # 1. Preprocess image for crisp boundaries (Otsu Thresholding)
    logger.info(f"[INFO] Preprocessing '{png_path}' for clean geometric outlines...")
    try:
        img = cv2.imread(png_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to load image for preprocessing: {png_path}")
        _, thresh_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        cv2.imwrite(processed_png_path, thresh_img)
    except Exception as e:
        logger.warning(f"[WARNING] OpenCV preprocessing failed ({e}). Falling back to original image.")
        processed_png_path = png_path

    logger.info(f"[INFO] Tracing raster image to vector SVG (polygon mode)...")

    # 2. Trace processed PNG to SVG with vtracer (binary colormode, polygon mode)
    vtracer.convert_image_to_svg_py(
        processed_png_path,
        svg_temp_path,
        colormode="binary",
        mode="polygon",
        filter_speckle=2,
        corner_threshold=30,
        length_threshold=2.0,
        max_iterations=10,
        splice_threshold=20
    )
    logger.info(f"[SUCCESS] Vector SVG generated: {svg_temp_path}")

    # 2. Parse SVG curves
    logger.info("[INFO] Parsing SVG geometry and scaling to 70x70 mm CNC bed...")
    curves = parse_file(svg_temp_path, transform_origin=True)
    if not curves:
        raise ValueError(f"No drawable curves found in '{svg_temp_path}'.")

    # 3. Scale curves strictly within 70x70 mm bed
    min_x, max_x, min_y, max_y = scale_curves_to_bed(
        curves,
        target_width=target_width,
        target_height=target_height,
        margin=2.0
    )
    logger.info(f"[INFO] Scaled Bounding Box: X=[{min_x:.2f}mm, {max_x:.2f}mm], Y=[{min_y:.2f}mm, {max_y:.2f}mm]")

    # 4. Compile with custom ServoInterface
    logger.info("[INFO] Compiling G-Code with Z-axis micro-servo commands (M3 S0/S90)...")
    compiler = Compiler(
        ServoInterface,
        movement_speed=feedrate_travel,
        cutting_speed=feedrate_draw,
        pass_depth=0,
        dwell_time=150,
        custom_header=["G21 ; Millimeter units", "G90 ; Absolute coordinates", "M3 S0 ; Pen UP initial"],
        custom_footer=["M3 S0 ; Pen UP final", "G0 X0 Y0 F1200 ; Return home"]
    )
    compiler.append_curves(curves)
    gcode_content = compiler.compile(passes=1)

    # 5. Write to output file
    with open(gcode_path, "w", encoding="utf-8") as f:
        f.write(gcode_content)

    line_count = len(gcode_content.splitlines())
    logger.info(f"[SUCCESS] Generated '{gcode_path}' ({line_count} G-Code instructions)")
    logger.info("=" * 60)
    return gcode_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pookalam PNG to G-Code Converter")
    parser.add_argument("--input", type=str, default="pookalam.png", help="Input PNG image path")
    parser.add_argument("--output", type=str, default="plot.gcode", help="Output G-Code file path")
    parser.add_argument("--width", type=float, default=70.0, help="Target bed width in mm")
    parser.add_argument("--height", type=float, default=70.0, help="Target bed height in mm")
    args = parser.parse_args()

    convert_to_gcode(
        png_path=args.input,
        gcode_path=args.output,
        target_width=args.width,
        target_height=args.height
    )
