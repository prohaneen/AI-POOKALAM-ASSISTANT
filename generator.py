import os
import json
import logging
from config import SETTINGS

logger = logging.getLogger("PookalamGenerator")

def fallback_designs(telemetry_str: str) -> dict:
    """Fallback JSON array if API fails."""
    logger.info("[FALLBACK] API quota exhausted. Using local deterministic fallback.")
    colors = ["Yellow", "Red", "Pink", "White"]
    try:
        data = json.loads(telemetry_str)
        if "available_inventory" in data:
            colors = list(data["available_inventory"].keys())
    except:
        pass
        
    c1 = colors[0] if len(colors) > 0 else "Yellow"
    c2 = colors[1 % len(colors)] if len(colors) > 1 else "Red"
    c3 = colors[2 % len(colors)] if len(colors) > 2 else "Pink"
    
    return {
        "layers": [
            {"radius_mm": 30, "pattern": "circle", "element_count": 1, "color": c1},
            {"radius_mm": 20, "pattern": "petals", "element_count": 12, "color": c2},
            {"radius_mm": 10, "pattern": "star", "element_count": 8, "color": c3}
        ]
    }

def generate_json_spec(telemetry_str: str, api_key: str = None, model_override: str = None) -> tuple[dict, dict]:
    key = api_key or os.environ.get('GEMINI_API_KEY')
    metadata = {"fallback_used": False, "exhausted": False, "messages": []}
    
    if not key:
        metadata["fallback_used"] = True
        metadata["messages"].append("No API key provided. Using deterministic fallback.")
        return fallback_designs(telemetry_str), metadata
        
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=key)
    
    prompt = f"""You are an expert Onam Pookalam CNC planner constrained by strict physical inventory. Map flowers with LARGE volume to the outer concentric rings (which require the most area). Map flowers with SMALL volume to the inner rings or sparse petal details. Output a single JSON design specification containing an array of 'layers'. Each layer must specify: 'radius_mm' (max 30mm), 'pattern' (choose from: circle, petals, scallop, star), 'element_count', and 'color'.

Inventory Payload: {telemetry_str}"""

    # Build sequential list starting with primary model
    models_to_try = [model_override] if model_override else [SETTINGS.gemini_model]
    
    # Array of robust fallbacks
    fallbacks = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-2.5-flash-lite"
    ]
    
    for f in fallbacks:
        if f not in models_to_try:
            models_to_try.append(f)
            
    for model_name in models_to_try:
        logger.info(f"==> THINK: Requesting JSON from {model_name}...")
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            specs = json.loads(response.text)
            if "layers" not in specs:
                raise ValueError("Response missing 'layers' array.")
                
            logger.info(f"[THINK] Successfully reasoned JSON design using {model_name}.")
            metadata["model_used"] = model_name
            return specs, metadata
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "Quota" in str(e):
                logger.warning(f"[WARNING] Quota Exhausted on {model_name}. Trying next...")
                metadata["exhausted"] = True
                metadata["messages"].append(f"Quota exhausted on {model_name}.")
            else:
                logger.warning(f"[WARNING] Generation failed on {model_name} ({e}). Trying next...")
                metadata["messages"].append(f"Error on {model_name}: {e}")
                
    logger.error("[ERROR] All Gemini models failed or hit quota limits. Falling back to local deterministic designs.")
    metadata["fallback_used"] = True
    return fallback_designs(telemetry_str), metadata
