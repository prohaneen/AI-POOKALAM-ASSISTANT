import unittest
import tempfile
import os
from deterministic_renderer import generate_svg
from generator import fallback_designs
from gcode_converter import compile_svg, validate_gcode

class TestGeometryAndSVG(unittest.TestCase):
    def test_geometry_orders(self):
        for n in (6, 8, 12):
            s = {
                "layers": [
                    {"radius_mm": 28, "pattern": "petals", "element_count": n, "color": "Indigo"},
                    {"radius_mm": 18, "pattern": "scallop", "element_count": 16, "color": "Pink/Orchid"},
                    {"radius_mm": 10, "pattern": "star", "element_count": n, "color": "Golden Yellow"}
                ]
            }
            with tempfile.TemporaryDirectory() as tmpdir:
                svg_path = os.path.join(tmpdir, f"{n}.svg")
                gcode_path = os.path.join(tmpdir, f"{n}.gcode")
                generate_svg(s, svg_path)
                compile_svg(svg_path, gcode_path)
                r = validate_gcode(gcode_path)
                self.assertTrue(r["valid"])
