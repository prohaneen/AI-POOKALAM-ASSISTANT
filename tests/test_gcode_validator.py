import unittest
import tempfile
import os
from gcode_converter import validate_gcode

class TestGcodeValidator(unittest.TestCase):
    def test_validator_rejects_unsafe_coordinates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = os.path.join(tmpdir, "unsafe.gcode")
            with open(p, "w", encoding="utf-8") as f:
                f.write("G0 X-1 Y71\n")
            self.assertFalse(validate_gcode(p)["valid"])
