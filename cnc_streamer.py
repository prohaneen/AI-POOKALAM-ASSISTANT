"""
AI Pookalam Assistant - CNC Streamer Module
Streams compiled G-Code to an Arduino/GRBL CNC pen-plotter over USB Serial
with standard ok-response handshaking and interactive terminal simulation support.
"""

import os
import sys
import time
import argparse
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("PookalamStreamer")


def clean_gcode_line(line: str) -> str:
    """
    Strips comments and leading/trailing whitespace from a G-Code command line.
    """
    line = line.strip()
    if ";" in line:
        line = line.split(";", 1)[0].strip()
    if "(" in line and ")" in line:
        # Strip parenthesized inline comments
        import re
        line = re.sub(r"\(.*?\)", "", line).strip()
    return line


def stream_gcode(
    gcode_path: str = "plot.gcode",
    port: str = "/dev/ttyACM0",
    baudrate: int = 115200,
    simulate: bool = False
) -> bool:
    """
    Streams G-Code commands to an Arduino GRBL CNC controller.

    :param gcode_path: Path to the .gcode file to stream.
    :param port: Serial port (default: '/dev/ttyACM0').
    :param baudrate: Serial baudrate (default: 115200).
    :param simulate: If True, prints commands to terminal with 0.02s delay without hardware serial.
    :return: True if streaming succeeded, False otherwise.
    """
    if not os.path.exists(gcode_path):
        logger.error(f"[ERROR] G-Code file not found: {gcode_path}")
        return False

    with open(gcode_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    commands = [clean_gcode_line(line) for line in raw_lines]
    commands = [cmd for cmd in commands if cmd]  # Remove blank lines

    total_cmds = len(commands)

    logger.info("=" * 60)
    logger.info("[Adaptive Pookalam] - CNC Plotter Streamer")
    logger.info("=" * 60)
    logger.info(f"Target File : {gcode_path} ({total_cmds} executable commands)")
    logger.info(f"Serial Port : {port} @ {baudrate} baud")
    logger.info(f"Mode        : {'[SIMULATION]' if simulate else '[HARDWARE SERIAL]'}")
    logger.info("=" * 60)

    # ---------------------------------------------------------
    # 1. Simulation Mode (Terminal visualization with 0.02s delay)
    # ---------------------------------------------------------
    if simulate:
        logger.info("\n[INFO] Initializing virtual GRBL simulator...")
        time.sleep(0.5)
        logger.info("[SIM] GRBL 1.1h ['$' for help] -> READY\n")

        for idx, cmd in enumerate(commands, 1):
            # Print G-code stream line
            print(f"[{idx:>4}/{total_cmds}] STREAM -> {cmd:<35} | RX <- ok")
            time.sleep(0.02)  # 20ms simulation delay per instruction

        logger.info("\n" + "=" * 60)
        logger.info("[SUCCESS] Simulated plotting run completed successfully!")
        logger.info("=" * 60)
        return True

    # ---------------------------------------------------------
    # 2. Hardware Serial Mode (PySerial with GRBL Handshake)
    # ---------------------------------------------------------
    try:
        import serial
    except ImportError:
        logger.error("[ERROR] pyserial is not installed. Run 'pip install pyserial'.")
        return False

    logger.info(f"[INFO] Connecting to Arduino CNC controller on {port}...")
    try:
        ser = serial.Serial(port, baudrate, timeout=2.0)
    except Exception as err:
        logger.error(f"[ERROR] Failed to connect to serial port '{port}': {err}")
        logger.info("[TIP] Use '--simulate' to run without physical hardware connected.")
        return False

    try:
        # Wake up GRBL: send newlines and wait for initialization banner
        logger.info("[INFO] Initializing GRBL handshake...")
        ser.write(b"\r\n\r\n")
        time.sleep(2.0)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        logger.info("[SUCCESS] GRBL controller initialized. Starting G-Code stream...\n")

        for idx, cmd in enumerate(commands, 1):
            cmd_payload = (cmd + "\n").encode("utf-8")
            ser.write(cmd_payload)

            # Wait for 'ok' acknowledgement from GRBL
            while True:
                response = ser.readline().decode("utf-8", errors="ignore").strip()
                if not response:
                    continue
                if response == "ok":
                    if idx % 25 == 0 or idx == total_cmds:
                        pct = (idx / total_cmds) * 100.0
                        logger.info(f"[{pct:>5.1f}%] Plotted {idx}/{total_cmds} instructions | Last: {cmd}")
                    break
                elif "error" in response.lower() or "alarm" in response.lower():
                    logger.warning(f"[WARNING] GRBL Alert on command '{cmd}': {response}")
                    break

        logger.info("\n" + "=" * 60)
        logger.info("[SUCCESS] CNC Plotting job complete!")
        logger.info("=" * 60)
        return True

    except KeyboardInterrupt:
        logger.warning("[ABORT] Raising pen and parking plotter.")
        try:
            ser.write(b"M3 S0\nG0 X0 Y0 F2000\n")
        except Exception:
            pass
        return False
    except Exception as err:
        logger.error(f"[ERROR] Communication error during streaming: {err}")
        return False

    finally:
        if ser and ser.is_open:
            ser.close()
            logger.info("[INFO] Serial connection closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pookalam CNC G-Code Serial Streamer")
    parser.add_argument("--input", type=str, default="plot.gcode", help="G-Code file to stream")
    parser.add_argument("--port", type=str, default="/dev/ttyACM0", help="Serial port (default: /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate (default: 115200)")
    parser.add_argument("--simulate", action="store_true", help="Simulate plotting in terminal without hardware")
    args = parser.parse_args()

    stream_gcode(
        gcode_path=args.input,
        port=args.port,
        baudrate=args.baud,
        simulate=args.simulate
    )
