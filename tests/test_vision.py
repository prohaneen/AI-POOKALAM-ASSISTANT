import json
import unittest
from vision import create_synthetic_test_frame, extract_vision_telemetry

class TestVision(unittest.TestCase):
    def test_mock_palette_and_schema(self):
        frame = create_synthetic_test_frame()
        telemetry_str = extract_vision_telemetry(frame)
        report = json.loads(telemetry_str)
        self.assertIn("available_inventory", report)
        self.assertIn("largest_color", report)
        self.assertIn(report["largest_color"], ["Yellow", "Golden Yellow", "Red", "Pink"])
