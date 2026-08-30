import unittest
import tempfile
import os
from main import run_pipeline

class TestEndToEnd(unittest.TestCase):
    def test_mock_simulated_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inv = os.path.join(tmpdir, "inventory.jpg")
            gcode = os.path.join(tmpdir, "plot.gcode")
            self.assertTrue(run_pipeline(
                mock=True,
                simulate=True,
                auto_accept=True,
                png_output=inv,
                gcode_output=gcode
            ))
