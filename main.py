import os
import sys
import time
import argparse
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from vision import autonomous_inventory_scan
from generator import generate_json_spec
from deterministic_renderer import generate_svg
from ui_menu import review_pookalam_design
from gcode_converter import compile_svg
from cnc_streamer import stream_gcode

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("PookalamMaster")

def print_banner(*lines: str):
    width = 70
    print("\n" + "=" * width)
    for line in lines:
        print(line.center(width))
    print("=" * width + "\n")

def run_pipeline(
    ipcam_url: str = "",
    mock: bool = False,
    visualize: bool = False,
    serial_port: str = "/dev/ttyACM0",
    baudrate: int = 115200,
    simulate: bool = False,
    auto_accept: bool = False,
    png_output: str = "test_outputs/inventory.jpg",
    gcode_output: str = "test_outputs/plot.gcode"
):
    start_time = time.time()
    output_dir = os.path.dirname(png_output) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    from config import SETTINGS
    
    print_banner(
        "[AI POOKALAM ASSISTANT]",
        "Resource-Aware Physical AI Creative Partner | Onam Edition 2026",
        "** FULLY AUTONOMOUS 'SENSE -> THINK -> ACT' ARCHITECTURE **"
    )

    # SENSE
    print("\n" + "="*50)
    print(">>> [STAGE 1] AUTONOMOUS VISION SENSE")
    print("="*50)
    try:
        inventory_img_path, telemetry = autonomous_inventory_scan(
            stream_url=ipcam_url,
            mock=mock,
            visualize=visualize,
            output_path=os.path.join(output_dir, "inventory.jpg")
        )
    except Exception as e:
        logger.error(f"[ERROR] Vision stage failed: {e}")
        return False

    # THINK & REVIEW LOOP
    iteration = 1
    plot_svg = os.path.join(output_dir, "plot.svg")

    while True:
        print("\n" + "="*50)
        print(f">>> [STAGE 2] AI LOGICAL REASONING (Variant #{iteration})")
        print("="*50)
        try:
            json_spec = generate_json_spec(telemetry)
            logger.info(f"[THINK] Generated JSON Specification:\n{json_spec}")
        except Exception as e:
            logger.error(f"[ERROR] Logic stage failed: {e}")
            return False

        # ACT (CAD)
        print("\n" + "="*50)
        print(">>> [STAGE 3] DETERMINISTIC CAD RENDERER")
        print("="*50)
        try:
            generate_svg(json_spec, plot_svg)
        except Exception as e:
            logger.error(f"[ERROR] CAD Generation failed: {e}")
            return False

        # USER INTERFACE MENU REVIEW
        print("\n" + "="*50)
        print(">>> [UI REVIEW] USER DESIGN APPROVAL MENU")
        print("="*50)
        user_choice = review_pookalam_design(
            json_spec=json_spec,
            iteration=iteration,
            auto_accept=auto_accept
        )

        if user_choice == "accept":
            logger.info("[UI REVIEW] Design accepted! Proceeding to G-Code compilation.")
            break
        elif user_choice == "regenerate":
            logger.info(f"[UI REVIEW] Regeneration requested. Generating variant #{iteration + 1}...")
            iteration += 1
            continue
        elif user_choice == "cancel":
            logger.info("[UI REVIEW] Design cancelled by user. Exiting pipeline.")
            return False
        else:
            logger.info("[UI REVIEW] Defaulting to accept.")
            break

    # ACT (G-CODE)
    print("\n" + "="*50)
    print(">>> [STAGE 4] G-CODE COMPILATION")
    print("="*50)
    try:
        compile_svg(svg_path=plot_svg, gcode_path=gcode_output)
        logger.info(f"[ACT] Successfully compiled G-Code to {gcode_output}")
    except Exception as e:
        logger.error(f"[ERROR] G-Code Compilation failed: {e}")
        return False

    # ACT (STREAM)
    print("\n" + "="*50)
    print(">>> [STAGE 5] STREAMING TO CNC PLOTTER")
    print("="*50)
    try:
        stream_gcode(
            gcode_path=gcode_output,
            port=serial_port,
            baudrate=baudrate,
            simulate=simulate
        )
    except Exception as e:
        logger.error(f"\n[ERROR] CNC Streaming failed: {e}")
        return False
        
    print("\n" + "=" * 70)
    print("                 [PIPELINE EXECUTION COMPLETE]                ")
    print(f"            Total End-to-End Execution Time: {time.time() - start_time:.2f}s  ")
    print("=" * 70)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive Pookalam Physical AI Assistant - Master Pipeline")
    parser.add_argument("--ipcam", type=str, default="http://10.136.106.51:4747/video", help="IP Webcam video feed URL")
    parser.add_argument("--mock", action="store_true", help="Run in synthetic benchmark evaluation mode")
    parser.add_argument("--visualize", action="store_true", help="Save diagnostic HUD visualization overlay")
    parser.add_argument("--port", type=str, default="/dev/ttyACM0", help="Serial port for CNC")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate")
    parser.add_argument("--simulate", action="store_true", help="Simulate CNC plotting in terminal")
    parser.add_argument("--auto-accept", action="store_true", help="Automatically accept design without blocking on UI prompt")
    parser.add_argument("--output-png", type=str, default="test_outputs/inventory.jpg", help="Destination path for inventory JPG")
    parser.add_argument("--output-gcode", type=str, default="test_outputs/plot.gcode", help="Destination path for compiled G-Code")
    parser.add_argument("--list-models", action="store_true", help="List available Gemini models")

    args = parser.parse_args()

    try:
        run_pipeline(
            ipcam_url=args.ipcam,
            mock=args.mock,
            visualize=args.visualize,
            serial_port=args.port,
            baudrate=args.baud,
            simulate=args.simulate,
            auto_accept=args.auto_accept,
            png_output=args.output_png,
            gcode_output=args.output_gcode
        )
    except KeyboardInterrupt:
        print("\n[INFO] Exiting pipeline.")
        sys.exit(1)
