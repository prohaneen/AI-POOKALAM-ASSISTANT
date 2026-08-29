from pathlib import Path
from gcode_converter import validate_gcode
def test_validator_rejects_unsafe_coordinates(tmp_path):
    p=tmp_path/'unsafe.gcode';p.write_text('G0 X-1 Y71\n')
    assert not validate_gcode(str(p))['valid']
