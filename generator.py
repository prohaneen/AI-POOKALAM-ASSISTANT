"""
AI Pookalam Assistant - Design Generator Module
Uses Google GenAI SDK to generate a minimalist, strictly 2D, line-art geometric
Pookalam (floral mandala) using the exact dominant colors detected by the vision system.
"""

import os
import sys
import argparse
import logging
from typing import List, Union, Dict, Any
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("PookalamGenerator")


def build_pookalam_prompt(colors: List[str]) -> str:
    """
    Constructs an optimized prompt for generating a strictly 2D geometric mandala.
    """
    color_str = ", ".join(colors)
    primary_color = colors[0] if len(colors) > 0 else "Golden Yellow"
    secondary_color = colors[1] if len(colors) > 1 else "Indigo"
    accent_color = colors[2] if len(colors) > 2 else "Pink/Orchid"

    prompt = (
        f"A strictly 2D, flat vector-style, line-art geometric Pookalam (Indian Onam floral mandala) design. "
        f"The design MUST ONLY use these exact three colors: {color_str}. "
        f"Arrangement: Outermost concentric border is {primary_color}, "
        f"middle floral petal ring is {secondary_color}, "
        f"and the inner central circular core is {accent_color}. "
        f"Minimalist, low-complexity, symmetrical 8-fold radial symmetry, "
        f"top-down orthogonal perspective, solid clean white background. "
        f"CRITICAL: Draw with ULTRA-THIN, crisp, high-contrast geometric lines without anti-aliasing. "
        f"NO 3D effects, NO shadows, NO gradients, NO realistic textures, NO perspective tilt."
    )
    return prompt


def generate_pookalam_design(
    colors_or_observation: Union[List[str], Dict[str, Any]],
    output_path: str = "pookalam.png",
    model: str = "imagen-3.0-generate-002",
    api_key: str = None
) -> str:
    """
    Prompts the GenAI model to generate a strictly 2D geometric Pookalam mandala
    using only the exact specified colors and saves it locally as a PNG image.

    :param colors_or_observation: List of 3 dominant color strings, or observation dict from vision.py.
    :param output_path: Destination path for the saved image (default: 'pookalam.png').
    :param model: Image generation model name (default: 'imagen-3.0-generate-002').
    :param api_key: Optional Gemini API key (otherwise reads GEMINI_API_KEY / GOOGLE_API_KEY env vars).
    :return: Path to the saved image file.
    """
    # Extract color list if observation dict was provided
    if isinstance(colors_or_observation, dict):
        colors = colors_or_observation.get("dominant_colors", [])
        if not colors:
            # Fallback to bands if present
            bands = colors_or_observation.get("bands", [])
            colors = [b["color"] for b in bands if "color" in b]
    else:
        colors = list(colors_or_observation)

    # Ensure we have at least 3 colors
    if len(colors) < 3:
        default_palette = ["Golden Yellow", "Indigo", "Pink/Orchid"]
        for c in default_palette:
            if c not in colors:
                colors.append(c)
            if len(colors) >= 3:
                break
    colors = colors[:3]

    prompt = build_pookalam_prompt(colors)
    logger.info("=" * 60)
    logger.info("[Adaptive Pookalam] - Design Generation Pipeline")
    logger.info("=" * 60)
    logger.info(f"Target Palette: {colors}")
    logger.info(f"Prompt: {prompt}")

    # Resolve API Key
    effective_api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not effective_api_key:
        logger.warning(
            "[WARNING] No GEMINI_API_KEY or GOOGLE_API_KEY found in environment.\n"
            "To generate live images with Gemini, set GEMINI_API_KEY in your environment.\n"
            "Generating synthetic fallback 2D vector mandala for offline testing..."
        )
        return _generate_fallback_image(colors, output_path)

    try:
        client = genai.Client(api_key=effective_api_key)
        logger.info(f"[INFO] Requesting image generation with model: {model}...")

        response = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/png"
            )
        )

        image_saved = False
        for generated_image in response.generated_images:
            with open(output_path, "wb") as f:
                f.write(generated_image.image.image_bytes)
            image_saved = True
            logger.info(f"[SUCCESS] Pookalam design successfully saved to: {output_path}")
            break

        if not image_saved:
            raise RuntimeError("No image returned by the Gemini API response.")

        return output_path

    except Exception as e:
        logger.error(f"[ERROR] Gemini Generation failed: {e}")
        logger.info("[FALLBACK] Generating fallback offline mandala pattern...")
        return _generate_fallback_image(colors, output_path)


def _generate_fallback_image(colors: List[str], output_path: str) -> str:
    """
    Creates an offline 2D line-art geometric Pookalam pattern matching the 3 colors
    using OpenCV drawing primitives when API credentials are unavailable or offline.
    """
    import cv2
    import numpy as np

    size = 640
    canvas = np.ones((size, size, 3), dtype=np.uint8) * 255
    center = (size // 2, size // 2)

    # Color map to BGR approximations
    COLOR_MAP_BGR = {
        "Indigo": (130, 40, 50),
        "Blue": (220, 100, 30),
        "Pink/Orchid": (210, 130, 220),
        "Golden Yellow": (50, 190, 230),
        "Yellow": (40, 220, 240),
        "Orange": (30, 140, 240),
        "Red": (40, 40, 220),
        "Violet": (180, 50, 130),
        "White": (240, 240, 240)
    }

    c1 = COLOR_MAP_BGR.get(colors[0], (50, 190, 230))
    c2 = COLOR_MAP_BGR.get(colors[1], (130, 40, 50))
    c3 = COLOR_MAP_BGR.get(colors[2], (210, 130, 220))

    # 1. Outermost Ring (Color 1)
    cv2.circle(canvas, center, 260, c1, 4)
    cv2.circle(canvas, center, 240, c1, 2)

    # 2. Outer 8-point geometric star petals (Color 1 & 2)
    for i in range(8):
        angle = i * (np.pi / 4)
        x = int(center[0] + 190 * np.cos(angle))
        y = int(center[1] + 190 * np.sin(angle))
        cv2.circle(canvas, (x, y), 50, c2, 3)

    # 3. Middle Floral Petal Ring (Color 2)
    cv2.circle(canvas, center, 140, c2, 4)
    cv2.circle(canvas, center, 120, (50, 50, 50), 2)

    # 4. Inner Central Core (Color 3)
    for i in range(6):
        angle = i * (np.pi / 3)
        x = int(center[0] + 50 * np.cos(angle))
        y = int(center[1] + 50 * np.sin(angle))
        cv2.circle(canvas, (x, y), 28, c3, -1)
        cv2.circle(canvas, (x, y), 28, (40, 40, 40), 2)

    cv2.circle(canvas, center, 35, c3, -1)
    cv2.circle(canvas, center, 35, (40, 40, 40), 3)

    cv2.imwrite(output_path, canvas)
    logger.info(f"[SUCCESS] Synthetic 2D geometric mandala written to: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive Pookalam Gemini Design Generator")
    parser.add_argument(
        "--colors",
        nargs="+",
        default=None,
        help="List of 3 exact colors (e.g., --colors 'Indigo' 'Pink/Orchid' 'Golden Yellow')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="pookalam.png",
        help="Output image path (default: pookalam.png)"
    )
    parser.add_argument(
        "--from-vision",
        action="store_true",
        help="Run vision.py mock analysis to extract dominant colors directly"
    )
    args = parser.parse_args()

    selected_colors = args.colors

    if args.from_vision or not selected_colors:
        try:
            from vision import capture_frame, analyze_scene
            frame = capture_frame(mock=True)
            scene = analyze_scene(frame)
            selected_colors = scene.get("dominant_colors", [])
            logger.info(f"[INFO] Extracted dominant colors from vision module: {selected_colors}")
        except Exception as err:
            logger.warning(f"[WARNING] Could not import vision module: {err}")
            selected_colors = ["Golden Yellow", "Indigo", "Pink/Orchid"]

    generate_pookalam_design(colors_or_observation=selected_colors, output_path=args.output)
