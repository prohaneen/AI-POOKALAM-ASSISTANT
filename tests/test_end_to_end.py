from main import run_pipeline
def test_mock_simulated_pipeline(tmp_path):
    assert run_pipeline(mock=True,simulate_cnc=True,png_output=str(tmp_path/'design.svg'),gcode_output=str(tmp_path/'plot.gcode'))
