from vision import create_synthetic_test_frame, analyze_scene
def test_mock_palette_and_schema():
    report=analyze_scene(create_synthetic_test_frame())
    assert set(['Indigo','Pink/Orchid','Golden Yellow']).issubset(report['dominant_colors'])
    assert len(report['spatial_regions'])==3
    assert all(0 <= x['confidence'] <= 1 for x in report['spatial_regions'])
