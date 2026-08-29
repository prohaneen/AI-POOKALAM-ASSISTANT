# 🌸 Adaptive Pookalam

**Google Physical AI Hackathon  Onam Edition 2026**

Adaptive Pookalam is a Resource Aware Physical AI Creative Partner. Instead of forcing a pre-made digital design onto the physical world, our system looks at the actual floral resources available, uses generative AI to design a culturally authentic pattern tailored to that specific inventory, and physically plots the layout using a custom CNC machine. 

## Runbook

Install the declared dependencies in a Python environment supported by OpenCV, then use:

```powershell
py -m pip install -r requirements.txt pytest
py main.py --mock --visualize --simulate
py main.py --ipcam http://PHONE:8080/video --visualize --simulate
py main.py --ipcam http://PHONE:8080/video --port /dev/ttyACM0 --baud 115200
```

The production path is telemetry → JSON design specification → deterministic SVG →
normalized SVG → validated G-code. Raster vectorization is intentionally not used for
physical output: thresholding and tracing can delete thin outlines.

Each run writes all generated artifacts to `test_outputs/` by default: `pookalam.png`,
`pookalam.svg`, `pookalam.spec.json`, `plot.normalized.svg`, `plot.gcode`, and (when
requested) `vision_debug_overlay.png`. The `--output-png` and `--output-gcode` options
let you choose another folder. The PNG preview is rendered
from the same deterministic SVG used for G-code. It is for visual inspection; plotting
always uses the SVG/G-code path.

The built-in fallback uses a traditional Kerala Pookalam composition: a circular border,
an eight-petal outer flower, a dense scalloped petal ring, and a star-flower centre. It
was informed by real Pookalam photographs, while retaining deterministic geometry needed
for a pen plotter.

Run the test suite with `py -m pytest -q`. The benchmark fixture is
`tests/test_pookalam_benchmark.svg` and can be compiled directly with
`py -c "from gcode_converter import compile_svg; compile_svg('tests/test_pookalam_benchmark.svg', 'benchmark.gcode')"`.
