"""Deterministic design-spec validation and plotter-safe SVG generation."""
import math
from typing import Any, Dict, Iterable, List, Tuple
from config import SETTINGS

Point = Tuple[float, float]

def fallback_spec(colors: Iterable[str]) -> Dict[str, Any]:
    """Traditional Pookalam grammar: floral border, alternating petals, centre star.
    The composition is informed by real Kerala Onam Pookalam photographs, but this
    function remains fully geometric so every petal is reproducible and plot-safe.
    """
    palette = list(dict.fromkeys(colors)) or ["Indigo", "Pink/Orchid", "Golden Yellow"]
    palette = (palette + ["Indigo", "Pink/Orchid", "Golden Yellow"])[:3]
    return {"canvas_size_mm": 70, "symmetry_order": 8,
      "outer_boundary": {"type":"circle", "radius_mm":30, "color":palette[0]},
      "layers":[
        {"layer_index":1,"type":"pointed_petals","count":8,"inner_radius_mm":18,"outer_radius_mm":28,"color":palette[0]},
        {"layer_index":2,"type":"scallop_ring","count":16,"inner_radius_mm":11,"outer_radius_mm":17,"color":palette[1]},
        {"layer_index":3,"type":"central_star","points":8,"radius_mm":10,"color":palette[2]}]}

def validate_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(spec, dict) or not isinstance(spec.get("layers"), list): raise ValueError("Design spec requires layers")
    order = int(spec.get("symmetry_order", 8))
    if order < 3 or order > 24: raise ValueError("symmetry_order must be 3..24")
    outer = spec.get("outer_boundary", {})
    radius = float(outer.get("radius_mm", 30))
    if not 5 <= radius <= 30: raise ValueError("outer radius is outside active workspace")
    for layer in spec["layers"]:
        if layer.get("type") not in {"pointed_petals", "scallop_ring", "central_star"}: raise ValueError("unsupported layer type")
        for key in ("inner_radius_mm", "outer_radius_mm", "radius_mm"):
            if key in layer and not 0 < float(layer[key]) <= 30: raise ValueError("invalid radius")
    return spec

def _point(cx: float, cy: float, r: float, a: float) -> Point:
    return cx + r * math.cos(a), cy + r * math.sin(a)

def _poly(points: List[Point], color: str) -> str:
    return '<path d="M ' + ' L '.join(f'{x:.3f} {y:.3f}' for x,y in points) + ' Z" fill="none" stroke="' + color + '" stroke-width="0.35"/>'

def _curved_petal(cx: float, cy: float, inner: float, outer: float, angle: float, half_angle: float, color: str) -> str:
    """A closed, smooth flower petal made solely from cubic Bézier curves."""
    start = _point(cx, cy, inner, angle - half_angle)
    tip = _point(cx, cy, outer, angle)
    end = _point(cx, cy, inner, angle + half_angle)
    c1 = _point(cx, cy, inner + (outer - inner) * .46, angle - half_angle * .82)
    c2 = _point(cx, cy, outer * .94, angle - half_angle * .18)
    c3 = _point(cx, cy, outer * .94, angle + half_angle * .18)
    c4 = _point(cx, cy, inner + (outer - inner) * .46, angle + half_angle * .82)
    # Concave base curve: this returns to the exact start point without a straight Z edge.
    c5 = _point(cx, cy, inner * .83, angle + half_angle * .45)
    c6 = _point(cx, cy, inner * .83, angle - half_angle * .45)
    return (f'<path d="M {start[0]:.3f} {start[1]:.3f} '
            f'C {c1[0]:.3f} {c1[1]:.3f} {c2[0]:.3f} {c2[1]:.3f} {tip[0]:.3f} {tip[1]:.3f} '
            f'C {c3[0]:.3f} {c3[1]:.3f} {c4[0]:.3f} {c4[1]:.3f} {end[0]:.3f} {end[1]:.3f} '
            f'C {c5[0]:.3f} {c5[1]:.3f} {c6[0]:.3f} {c6[1]:.3f} {start[0]:.3f} {start[1]:.3f}" '
            f'fill="{color}" fill-opacity="0.82" stroke="{color}" stroke-width="0.35"/>')

def generate_svg(spec: Dict[str, Any]) -> str:
    validate_spec(spec); cx=cy=35.0; paths=[]
    outer=spec["outer_boundary"]; r=float(outer.get("radius_mm",30))
    paths.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{outer.get("color","Indigo")}" stroke-width="0.45"/>')
    for layer in spec["layers"]:
        kind=layer["type"]; color=layer.get("color","black")
        if kind == "pointed_petals":
            count=int(layer.get("count",spec["symmetry_order"])); ri=float(layer["inner_radius_mm"]); ro=float(layer["outer_radius_mm"])
            for i in range(count):
                a=2*math.pi*i/count; da=math.pi/count*.65
                paths.append(_curved_petal(cx, cy, ri, ro, a, da, color))
        elif kind == "scallop_ring":
            count=int(layer.get("count",16)); ri=float(layer["inner_radius_mm"]); ro=float(layer["outer_radius_mm"])
            for i in range(count):
                a=2*math.pi*i/count; da=math.pi/count
                paths.append(_curved_petal(cx, cy, ri, ro, a, da, color))
        else:
            n=int(layer.get("points",spec["symmetry_order"])); r=float(layer["radius_mm"]); pts=[]
            for i in range(n*2): pts.append(_point(cx,cy,r if i%2==0 else r*.45, -math.pi/2+i*math.pi/n))
            paths.append(_poly(pts,color))
    return '<svg xmlns="http://www.w3.org/2000/svg" width="70mm" height="70mm" viewBox="0 0 70 70">' + ''.join(paths) + '</svg>'

def render_svg_preview(svg_path: str, png_path: str, pixels: int = 700) -> str:
    """Render a colour-filled preview from the same SVG geometry sent to the plotter."""
    import cv2
    import numpy as np
    import xml.etree.ElementTree as ET
    from svg_normalizer import parse_path, _circle, fit_paths
    colour_bgr = {
        "Indigo": (165, 45, 55), "Blue": (220, 100, 30),
        "Pink/Orchid": (215, 135, 225), "Golden Yellow": (55, 190, 225),
        "Yellow": (40, 220, 240), "Orange": (30, 140, 240),
        "Red": (40, 40, 220), "Violet": (180, 50, 130), "White": (245, 245, 245),
    }
    source_paths, colours, closed = [], [], []
    for element in ET.parse(svg_path).getroot().iter():
        tag = element.tag.rsplit("}", 1)[-1]
        paths = parse_path(element.get("d", "")) if tag == "path" else (_circle(element) if tag == "circle" else [])
        for path in paths:
            source_paths.append(path)
            colours.append(colour_bgr.get(element.get("stroke", ""), (45, 45, 45)))
            closed.append(tag == "path" and len(path) > 2 and path[0] == path[-1])
    paths = fit_paths(source_paths)
    canvas = np.full((pixels, pixels, 3), 255, dtype=np.uint8)
    scale = pixels / 70.0
    for path, colour, is_closed in zip(paths, colours, closed):
        points = np.array([[round(x * scale), round(y * scale)] for x, y in path], dtype=np.int32)
        # Closed petals and centre stars receive flower colour; circular borders remain rings.
        if is_closed:
            cv2.fillPoly(canvas, [points], colour, lineType=cv2.LINE_AA)
        cv2.polylines(canvas, [points], True, (35, 35, 35), 2, cv2.LINE_AA)
    if not cv2.imwrite(png_path, canvas):
        raise IOError(f"Could not write PNG preview: {png_path}")
    return png_path
