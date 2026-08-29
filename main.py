"""
AI Pookalam Assistant - Master Pipeline Orchestrator
Physical AI Creative Partner for Arduino UNO Q (Debian Linux)
Executes end-to-end workflow:
  [1] Computer Vision (IP Webcam / Mock Evaluation)
  [2] Generative AI Design (Gemini 2.5 / Imagen)
  [3] G-Code Vectorization & Bed Scaling (70x70 mm)
  [4] CNC Streamer & GRBL Handshake (Arduino UNO Q / GRBL)
"""

import os
import sys
import time
import argparse
import logging
from typing import Dict, Any

from vision import capture_frame, analyze_scene, print_diagnostic_output, draw_debug_visualization
from generator import generate_pookalam_design
from gcode_converter import compile_svg, validate_gcode, design_quality
from svg_normalizer import normalize_svg
from geometry import render_svg_preview
from cnc_streamer import stream_gcode

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("PookalamMain")


def print_banner(title: str, subtitle: str = "") -> None:
    """Prints a bold, visually striking console banner for live demo presentation."""
    width = 70
    logger.info("\n" + "=" * width)
    logger.info(f"  {title}".center(width))
    if subtitle:
        logger.info(f"  {subtitle}".center(width))
    logger.info("=" * width + "\n")


def run_pipeline(
    ipcam_url: str = None,
    mock: bool = False,
    visualize: bool = False,
    serial_port: str = "/dev/ttyACM0",
    baudrate: int = 115200,
    simulate_cnc: bool = False,
    png_output: str = "test_outputs/pookalam.png",
    gcode_output: str = "test_outputs/plot.gcode"
) -> bool:
    """
    Executes the linear 4-stage Physical AI Pookalam Assistant pipeline.
    """
    start_time = time.time()
    output_dir = os.path.dirname(png_output) or "."
    os.makedirs(output_dir, exist_ok=True)

    print_banner(
        "[AI POOKALAM ASSISTANT]",
        "Resource-Aware Physical AI Creative Partner | Onam Edition 2026"
    )

    # -------------------------------------------------------------------------
    # STAGE 1: COMPUTER VISION & SPATIAL COLOR DETECTION
    # -------------------------------------------------------------------------
    logger.info(">>> [STAGE 1/4] ACQUIRING FLORAL INVENTORY & SPATIAL LAYERS...")
    time.sleep(0.5)

    try:
        raw_frame = capture_frame(stream_url=ipcam_url, mock=mock)
        telemetry: Dict[str, Any] = analyze_scene(raw_frame)
        print_diagnostic_output(telemetry)

        if visualize:
            import cv2
            overlay_file = os.path.join(output_dir, "vision_debug_overlay.png")
            debug_img = draw_debug_visualization(raw_frame, telemetry)
            cv2.imwrite(overlay_file, debug_img)
            logger.info(f"[STAGE 1 SUCCESS] Diagnostic HUD overlay saved to '{overlay_file}'.")

        dominant_colors = telemetry.get("dominant_colors", [])
        if not dominant_colors:
            logger.warning("[WARNING] No distinct dominant colors identified. Using default palette.")
            dominant_colors = ["Golden Yellow", "Indigo", "Pink/Orchid"]

    except Exception as err:
        logger.error(f"[STAGE 1 FAILURE] Computer Vision pipeline error: {err}")
        return False

    # -------------------------------------------------------------------------
    # STAGE 2: GENERATIVE AI DESIGN SYNTHESIS (GEMINI)
    # -------------------------------------------------------------------------
    logger.info("\n>>> [STAGE 2/4] SYNTHESIZING ADAPTIVE 2D MANDALA DESIGN WITH GEMINI...")
    time.sleep(0.5)

    try:
        generated_svg = generate_pookalam_design(
            colors_or_observation=telemetry,
            output_path=os.path.splitext(png_output)[0] + ".svg"
        )
        preview_png = png_output if png_output.lower().endswith(".png") else os.path.splitext(png_output)[0] + ".png"
        render_svg_preview(generated_svg, preview_png)
        logger.info(f"[STAGE 2 SUCCESS] Deterministic geometry source saved to '{generated_svg}'.")
        logger.info(f"[STAGE 2 SUCCESS] PNG preview saved to '{preview_png}'.")
    except Exception as err:
        logger.error(f"[STAGE 2 FAILURE] Generative AI design synthesis error: {err}")
        return False

    # -------------------------------------------------------------------------
    # STAGE 3: VECTOR TRACING & G-CODE COMPILATION (70x70mm BED)
    # -------------------------------------------------------------------------
    logger.info("\n>>> [STAGE 3/4] VECTORIZING SVG & COMPILING SERVO G-CODE...")
    time.sleep(0.5)

    try:
        compiled_gcode = compile_svg(generated_svg, gcode_output)
        logger.info(f"[DESIGN QUALITY] {design_quality(normalize_svg(generated_svg))}")
        logger.info(f"[G-CODE PRE-FLIGHT] {validate_gcode(compiled_gcode)}")
        logger.info(f"[STAGE 3 SUCCESS] G-Code generated and scaled strictly to 70x70mm: '{compiled_gcode}'.")
    except Exception as err:
        logger.error(f"[STAGE 3 FAILURE] G-Code compilation error: {err}")
        return False

    # -------------------------------------------------------------------------
    # STAGE 4: CNC STREAMER & PHYSICAL PLOTTER EXECUTION
    # -------------------------------------------------------------------------
    logger.info("\n>>> [STAGE 4/4] STREAMING G-CODE TO ARDUINO CNC PLOTTER...")
    time.sleep(0.5)

    try:
        success = stream_gcode(
            gcode_path=compiled_gcode,
            port=serial_port,
            baudrate=baudrate,
            simulate=simulate_cnc
        )
        if not success:
            logger.error("[STAGE 4 FAILURE] CNC streaming encountered an issue.")
            return False
    except Exception as err:
        logger.error(f"[STAGE 4 FAILURE] Serial CNC Streamer error: {err}")
        return False

    # -------------------------------------------------------------------------
    # PIPELINE COMPLETE
    # -------------------------------------------------------------------------
    elapsed = round(time.time() - start_time, 2)
    print_banner(
        "[PIPELINE EXECUTION COMPLETE]",
        f"Total End-to-End Execution Time: {elapsed}s"
    )
    logger.info("Artifacts Generated:")
    logger.info(f"  * Vision Overlay : {os.path.join(output_dir, 'vision_debug_overlay.png') if visualize else 'Skipped (--visualize to enable)'}")
    logger.info(f"  * Pookalam Preview: {preview_png}")
    logger.info(f"  * Vector SVG     : {os.path.splitext(png_output)[0] + '.svg'}")
    logger.info(f"  * Plotter G-Code : {gcode_output} (70x70 mm bounded)")
    logger.info("\n" + "=" * 70 + "\n")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Adaptive Pookalam Physical AI Assistant - Master Pipeline"
    )
    parser.add_argument(
        "--ipcam",
        type=str,
        default=None,
        help="IP Webcam video feed URL (e.g. http://192.168.1.50:8080/video)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in synthetic benchmark evaluation mode without physical camera"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Save diagnostic HUD visualization overlay (vision_debug_overlay.png)"
    )
    parser.add_argument(
        "--port",
        type=str,
        default="/dev/ttyACM0",
        help="Serial port for Arduino UNO Q / GRBL controller (default: /dev/ttyACM0)"
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Serial baudrate (default: 115200)"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Simulate CNC plotting in terminal without hardware connection"
    )
    parser.add_argument(
        "--output-png",
        type=str,
        default="test_outputs/pookalam.png",
        help="Destination path for generated Pookalam PNG preview"
    )
    parser.add_argument(
        "--output-gcode",
        type=str,
        default="test_outputs/plot.gcode",
        help="Destination path for compiled G-Code"
    )
    args = parser.parse_args()

    # Default to mock if neither live stream nor mock flag was explicitly specified
    is_mock = args.mock or (args.ipcam is None)

    run_pipeline(
        ipcam_url=args.ipcam,
        mock=is_mock,
        visualize=args.visualize,
        serial_port=args.port,
        baudrate=args.baud,
        simulate_cnc=args.simulate,
        png_output=args.output_png,
        gcode_output=args.output_gcode
    )
