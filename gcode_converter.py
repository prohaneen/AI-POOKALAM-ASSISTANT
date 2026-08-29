"""SVG-to-G-code compiler. Raster tracing is intentionally optional and never the main path."""
import math, os, re
from config import SETTINGS
from svg_normalizer import normalize_svg

def _dist(a,b): return math.hypot(b[0]-a[0],b[1]-a[1])
def design_quality(paths):
    closed=sum(1 for p in paths if _dist(p[0],p[-1]) <= .02)
    draw=sum(_dist(a,b) for p in paths for a,b in zip(p,p[1:]))
    travel=sum(_dist(a[-1],b[0]) for a,b in zip(paths,paths[1:]))
    pts=[q for p in paths for q in p]; w=max(x for x,y in pts)-min(x for x,y in pts);h=max(y for x,y in pts)-min(y for x,y in pts)
    report={'total_path_count':len(paths),'closed_loop_count':closed,'total_stroke_length_mm':round(draw,3),'bounding_box_dimensions':(round(w,3),round(h,3)),'travel_to_draw_ratio':round(travel/max(draw,.001),3)}
    report['valid']=len(paths)>=4 and closed>0 and 150<=draw<=2500 and 30<=w<=65 and 30<=h<=65 and report['travel_to_draw_ratio']<=1.5
    return report
def compile_svg(svg_path:str,gcode_path:str='plot.gcode')->str:
    paths=normalize_svg(svg_path, os.path.splitext(gcode_path)[0]+'.normalized.svg')
    quality=design_quality(paths)
    if not quality['valid']: raise ValueError('Design quality gate failed: '+str(quality))
    lines=['G21','G90','G92 X0 Y0 Z0',SETTINGS.pen_up_cmd,'G4 P0.15']; current=(0.,0.)
    for path in paths:
        start=path[0];lines += [f'G0 X{start[0]:.3f} Y{start[1]:.3f} F{SETTINGS.travel_feedrate}',SETTINGS.pen_down_cmd,'G4 P0.15']
        for p in path[1:]: lines.append(f'G1 X{p[0]:.3f} Y{p[1]:.3f} F{SETTINGS.draw_feedrate}')
        lines += [SETTINGS.pen_up_cmd,'G4 P0.15'];current=path[-1]
    lines += [SETTINGS.pen_up_cmd,f'G0 X0 Y0 F{SETTINGS.travel_feedrate}']
    with open(gcode_path,'w',encoding='utf8') as f:f.write('\n'.join(lines)+'\n')
    report=validate_gcode(gcode_path)
    if not report['valid']: raise ValueError('Unsafe G-code: '+ '; '.join(report['errors']))
    return gcode_path
def convert_to_gcode(png_path='pookalam.png',gcode_path='plot.gcode',**kwargs):
    """Compatibility API: compile an SVG path; raster inputs are rejected to prevent silent loss."""
    if png_path.lower().endswith('.svg'): return compile_svg(png_path,gcode_path)
    sibling=os.path.splitext(png_path)[0]+'.svg'
    if os.path.exists(sibling): return compile_svg(sibling,gcode_path)
    raise ValueError('Raster vectorization is disabled for plot safety; provide a deterministic SVG.')
def validate_gcode(path:str):
    x=y=0.; xmin=ymin=float('inf');xmax=ymax=float('-inf');draw=travel=0.; lifts=0; down=False;errors=[];lines=0
    for raw in open(path,encoding='utf8'):
        line=raw.split(';')[0].strip();lines+=bool(line)
        if line.startswith('M3 S90'): down=True
        if line.startswith('M3 S0'): lifts+=1;down=False
        if line.startswith(('G0','G1')):
            nx=float(re.search(r'X([-+0-9.]+)',line).group(1)) if re.search(r'X([-+0-9.]+)',line) else x;ny=float(re.search(r'Y([-+0-9.]+)',line).group(1)) if re.search(r'Y([-+0-9.]+)',line) else y
            if not all(math.isfinite(v) for v in (nx,ny)):errors.append('NaN/Inf coordinate')
            if not (0<=nx<=70 and 0<=ny<=70):errors.append('coordinate outside 70 mm bed')
            d=_dist((x,y),(nx,ny)); draw+=d if down and line.startswith('G1') else 0;travel+=d if not(down and line.startswith('G1')) else 0;x,y=nx,ny;xmin=min(xmin,x);xmax=max(xmax,x);ymin=min(ymin,y);ymax=max(ymax,y)
    return {'valid':not errors,'errors':errors,'total_lines':lines,'draw_distance_mm':round(draw,3),'travel_distance_mm':round(travel,3),'pen_lifts_count':lifts,'bbox':(xmin,xmax,ymin,ymax)}
