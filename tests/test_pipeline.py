"""
Unit tests for AI Pookalam Assistant pipeline components.
"""

import os
import json
import tempfile
import unittest
import numpy as np

from vision import create_synthetic_test_frame, extract_vision_telemetry
from generator import fallback_designs, generate_json_spec
from deterministic_renderer import generate_svg, render_pookalam_image, parse_spec_layers
from gcode_converter import compile_svg, validate_gcode
from ui_menu import review_pookalam_design, PookalamReviewMenu
from main import run_pipeline


class TestPookalamPipeline(unittest.TestCase):

    def test_vision_telemetry(self):
        frame = create_synthetic_test_frame()
        telemetry_str = extract_vision_telemetry(frame)
        data = json.loads(telemetry_str)
        self.assertIn("available_inventory", data)
        self.assertIn("largest_color", data)

    def test_generator_fallback(self):
        telemetry_str = json.dumps({"available_inventory": {"Yellow": 5000, "Red": 2000, "Pink": 500}})
        spec = fallback_designs(telemetry_str)
        self.assertIn("layers", spec)
        self.assertGreaterEqual(len(spec["layers"]), 3)

    def test_cad_rendering(self):
        spec = {
            "layers": [
                {"radius_mm": 30, "pattern": "circle", "element_count": 1, "color": "Yellow"},
                {"radius_mm": 20, "pattern": "petals", "element_count": 8, "color": "Red"},
                {"radius_mm": 15, "pattern": "scallop", "element_count": 12, "color": "Pink"},
                {"radius_mm": 10, "pattern": "star", "element_count": 6, "color": "Orange"}
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = os.path.join(tmpdir, "test.svg")
            svg_content = generate_svg(spec, svg_path)
            self.assertTrue(os.path.exists(svg_path))
            self.assertIn("<svg", svg_content)
            self.assertIn("viewBox=\"0 0 70 70\"", svg_content)

            # Test OpenCV image rendering
            img = render_pookalam_image(spec, size=500)
            self.assertEqual(img.shape, (500, 500, 3))
            self.assertEqual(img.dtype, np.uint8)

    def test_gcode_compilation_and_validation(self):
        spec = {
            "layers": [
                {"radius_mm": 28, "pattern": "circle", "element_count": 1, "color": "Yellow"},
                {"radius_mm": 20, "pattern": "petals", "element_count": 8, "color": "Red"},
                {"radius_mm": 10, "pattern": "star", "element_count": 8, "color": "Pink"}
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = os.path.join(tmpdir, "plot.svg")
            gcode_path = os.path.join(tmpdir, "plot.gcode")
            generate_svg(spec, svg_path)
            compile_svg(svg_path, gcode_path)
            self.assertTrue(os.path.exists(gcode_path))

            report = validate_gcode(gcode_path)
            self.assertTrue(report["valid"], f"G-code validation errors: {report['errors']}")
            self.assertGreater(report["total_lines"], 50)
            self.assertGreater(report["draw_distance_mm"], 50)

    def test_ui_menu_hud_builder_and_auto_accept(self):
        spec = {
            "layers": [
                {"radius_mm": 28, "pattern": "circle", "element_count": 1, "color": "Yellow"},
                {"radius_mm": 18, "pattern": "petals", "element_count": 8, "color": "Red"}
            ]
        }
        menu = PookalamReviewMenu()
        frame = menu.build_hud_frame(spec, iteration=1)
        self.assertEqual(frame.shape, (600, 1080, 3))

        # Test auto_accept path
        choice = review_pookalam_design(spec, iteration=1, auto_accept=True)
        self.assertEqual(choice, "accept")

    def test_end_to_end_mock_simulation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inv_path = os.path.join(tmpdir, "inventory.jpg")
            gcode_path = os.path.join(tmpdir, "plot.gcode")
            success = run_pipeline(
                mock=True,
                simulate=True,
                auto_accept=True,
                png_output=inv_path,
                gcode_output=gcode_path
            )
            self.assertTrue(success)
            self.assertTrue(os.path.exists(gcode_path))


if __name__ == "__main__":
    unittest.main()

