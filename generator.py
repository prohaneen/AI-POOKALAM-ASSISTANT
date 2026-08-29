"""Gemini produces a bounded JSON design decision; Python produces every vector."""
import json, os, time
from typing import Any, Dict, List, Union
from config import SETTINGS
from geometry import fallback_spec, generate_svg, validate_spec

def build_pookalam_prompt(colors: List[str]) -> str:
    return ("Return JSON only: canvas_size_mm, symmetry_order, outer_boundary and layers. "
      "Allowed layer types: pointed_petals, scallop_ring, central_star. All radii <=30 mm. "
      f"Use this observed palette: {', '.join(colors)}. Do not return SVG.")
def _colors(value):
    if isinstance(value,dict): return value.get('dominant_colors') or [x['color'] for x in value.get('spatial_regions',value.get('bands',[]))]
    return list(value)
def request_design_spec(colors:List[str], api_key=None)->Dict[str,Any]:
    key=api_key or os.environ.get('GEMINI_API_KEY')
    if not key:return fallback_spec(colors)
    try:
        from google import genai
        from google.genai import types
        client=genai.Client(api_key=key)
        for attempt in range(3):
            try:
                response=client.models.generate_content(model=SETTINGS.gemini_model,contents=build_pookalam_prompt(colors),config=types.GenerateContentConfig(response_mime_type='application/json'))
                return validate_spec(json.loads(response.text))
            except Exception:
                if attempt==2: raise
                time.sleep(.5*(2**attempt))
    except Exception:return fallback_spec(colors)
def generate_pookalam_design(colors_or_observation:Union[List[str],Dict[str,Any]],output_path='pookalam.svg',model=None,api_key=None)->str:
    colors=_colors(colors_or_observation);spec=request_design_spec(colors,api_key)
    if not output_path.lower().endswith('.svg'): output_path=os.path.splitext(output_path)[0]+'.svg'
    with open(output_path,'w',encoding='utf8') as f:f.write(generate_svg(spec))
    with open(os.path.splitext(output_path)[0]+'.spec.json','w',encoding='utf8') as f:json.dump(spec,f,indent=2)
    return output_path
