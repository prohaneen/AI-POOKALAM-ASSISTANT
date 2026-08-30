"""Central configuration for the 70 mm Adaptive Pookalam plotter."""
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    webcam_url: str = ""
    frame_width: int = 640
    frame_height: int = 480
    camera_timeout: float = 5.0
    min_contour_area: int = 120
    bed_size_x_mm: float = 70.0
    bed_size_y_mm: float = 70.0
    margin_mm: float = 5.0
    draw_feedrate: int = 1000
    travel_feedrate: int = 2000
    pen_up_cmd: str = "M3 S0"
    pen_down_cmd: str = "M3 S90"
    default_port: str = "/dev/ttyACM0"
    default_baud: int = 115200
    gemini_model: str = os.environ.get("GEMINI_MODEL_NAME", "gemini-3.6-flash")

SETTINGS = Settings()
