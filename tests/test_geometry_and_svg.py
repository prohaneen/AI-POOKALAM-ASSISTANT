from pathlib import Path
from geometry import fallback_spec, generate_svg
from gcode_converter import compile_svg, validate_gcode
def test_geometry_orders(tmp_path):
    for n in (6,8,12):
        s=fallback_spec(['Indigo','Pink/Orchid','Golden Yellow']);s['symmetry_order']=n;s['layers'][0]['count']=n
        p=tmp_path/f'{n}.svg';p.write_text(generate_svg(s));compile_svg(str(p),str(tmp_path/f'{n}.gcode'))
def test_benchmark_compiles(tmp_path):
    src=Path(__file__).with_name('test_pookalam_benchmark.svg');out=tmp_path/'benchmark.gcode';compile_svg(str(src),str(out));r=validate_gcode(str(out))
    assert r['valid'] and r['draw_distance_mm'] > 150 and r['pen_lifts_count'] >= 4
