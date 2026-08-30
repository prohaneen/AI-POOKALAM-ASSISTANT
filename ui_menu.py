"""
AI Pookalam Assistant - Interactive OpenCV HUD Menu (Widescreen Rectangular Dashboard)
Displays the AI-generated Pookalam design preview alongside detailed layer metadata
and interactive controls (Accept & Plot, Regenerate, Cancel) via both GUI mouse clicks
and keyboard shortcuts in a clean widescreen 16:9 layout.
"""

import os
import sys
import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import cv2

from deterministic_renderer import render_pookalam_image, parse_spec_layers, _get_bgr_color

logger = logging.getLogger("PookalamUI")

class PookalamReviewMenu:
    def __init__(self, window_name: str = "AI Pookalam Assistant - Design Review"):
        self.window_name = window_name
        self.action = None
        self.buttons = {}
        self.hovered_button = None

    def _draw_button(
        self,
        img: np.ndarray,
        btn_id: str,
        label: str,
        sublabel: str,
        rect: Tuple[int, int, int, int],
        bg_color: Tuple[int, int, int],
        hover_color: Tuple[int, int, int],
        text_color: Tuple[int, int, int] = (255, 255, 255)
    ):
        x1, y1, x2, y2 = rect
        self.buttons[btn_id] = rect
        
        is_hover = (self.hovered_button == btn_id)
        color = hover_color if is_hover else bg_color

        # Button background with subtle bevel border
        cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (240, 240, 240) if is_hover else (80, 80, 85), 2)

        font = cv2.FONT_HERSHEY_SIMPLEX
        if sublabel:
            # Two-line button text
            (tw, th), _ = cv2.getTextSize(label, font, 0.60, 2)
            tx = x1 + (x2 - x1 - tw) // 2
            ty = y1 + (y2 - y1) // 2 - 2
            cv2.putText(img, label, (tx, ty), font, 0.60, text_color, 2, cv2.LINE_AA)

            (stw, sth), _ = cv2.getTextSize(sublabel, font, 0.38, 1)
            stx = x1 + (x2 - x1 - stw) // 2
            sty = ty + 18
            cv2.putText(img, sublabel, (stx, sty), font, 0.38, (220, 220, 220), 1, cv2.LINE_AA)
        else:
            # Single-line button text centered
            (tw, th), _ = cv2.getTextSize(label, font, 0.55, 2)
            tx = x1 + (x2 - x1 - tw) // 2
            ty = y1 + (y2 - y1 + th) // 2
            cv2.putText(img, label, (tx, ty), font, 0.55, text_color, 2, cv2.LINE_AA)

    def _on_mouse(self, event, x, y, flags, param):
        self.hovered_button = None
        for btn_id, (x1, y1, x2, y2) in self.buttons.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.hovered_button = btn_id
                if event == cv2.EVENT_LBUTTONDOWN or event == cv2.EVENT_LBUTTONUP:
                    self.action = btn_id
                break

    def build_hud_frame(self, json_spec: Dict[str, Any], iteration: int = 1) -> np.ndarray:
        # Widescreen 16:9 Aspect Ratio Dashboard
        W, H = 1080, 600
        frame = np.full((H, W, 3), 20, dtype=np.uint8)  # Deep sleek graphite

        # Top Header Bar
        cv2.rectangle(frame, (0, 0), (W, 60), (32, 32, 36), -1)
        cv2.line(frame, (0, 60), (W, 60), (55, 55, 62), 2)
        cv2.putText(frame, "AI POOKALAM ASSISTANT", (28, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Autonomous CAD Planner & Physical Quality Gate  |  Design Variant #{iteration}", (400, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 205, 255), 1, cv2.LINE_AA)

        # ----------------- LEFT COLUMN: MANDALA PREVIEW -----------------
        preview_size = 480
        mandala_img = render_pookalam_image(json_spec, size=preview_size)
        px1 = 30
        py1 = 80
        px2 = px1 + preview_size
        py2 = py1 + preview_size

        # Shadow & Frame Border
        cv2.rectangle(frame, (px1 - 4, py1 - 4), (px2 + 4, py2 + 4), (40, 40, 45), -1)
        cv2.rectangle(frame, (px1 - 2, py1 - 2), (px2 + 2, py2 + 2), (70, 70, 78), 2)
        frame[py1:py2, px1:px2] = mandala_img

        # ----------------- RIGHT COLUMN: SPEC & CONTROLS -----------------
        rx1 = 540
        rx2 = W - 30
        
        # --- Card 1: Design Specification & Layer Breakdown ---
        card1_y1 = 80
        card1_y2 = 295
        cv2.rectangle(frame, (rx1, card1_y1), (rx2, card1_y2), (28, 28, 33), -1)
        cv2.rectangle(frame, (rx1, card1_y1), (rx2, card1_y2), (50, 50, 58), 1)

        # Card 1 Header
        cv2.rectangle(frame, (rx1, card1_y1), (rx2, card1_y1 + 32), (38, 38, 44), -1)
        cv2.putText(frame, "DESIGN & INVENTORY SPECIFICATION", (rx1 + 15, card1_y1 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (240, 240, 240), 1, cv2.LINE_AA)

        layers = parse_spec_layers(json_spec)
        max_r = max((ly["radius_mm"] for ly in layers), default=30.0)

        # Summary line
        cv2.putText(frame, f"Total Layers: {len(layers)}", (rx1 + 18, card1_y1 + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 215, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Max Radius: {max_r:.1f} mm", (rx1 + 180, card1_y1 + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 215, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "Bed Envelope: 70 x 70 mm", (rx1 + 330, card1_y1 + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 215, 255), 1, cv2.LINE_AA)

        cv2.line(frame, (rx1 + 15, card1_y1 + 75), (rx2 - 15, card1_y1 + 75), (45, 45, 52), 1)

        # Layer Rows
        row_y = card1_y1 + 105
        for idx, ly in enumerate(layers[:5]):
            color_name = ly["color"]
            pattern = ly["pattern"].capitalize()
            r_val = ly["radius_mm"]
            count = ly["element_count"]
            bgr = _get_bgr_color(color_name)

            # Swatch circle
            cv2.circle(frame, (rx1 + 25, row_y - 4), 7, bgr, -1, cv2.LINE_AA)
            cv2.circle(frame, (rx1 + 25, row_y - 4), 7, (230, 230, 230), 1, cv2.LINE_AA)

            # Layer text details
            layer_txt = f"Layer {idx + 1}: {pattern:<8} (r={r_val:.0f}mm, count={count})"
            cv2.putText(frame, layer_txt, (rx1 + 42, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv2.LINE_AA)
            
            # Assigned flower color tag
            cv2.putText(frame, f"[{color_name}]", (rx1 + 370, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 230, 180), 1, cv2.LINE_AA)

            row_y += 32

        # --- Card 2: Interactive Actions & Controls ---
        card2_y1 = 315
        card2_y2 = 560
        cv2.rectangle(frame, (rx1, card2_y1), (rx2, card2_y2), (28, 28, 33), -1)
        cv2.rectangle(frame, (rx1, card2_y1), (rx2, card2_y2), (50, 50, 58), 1)

        # Card 2 Header
        cv2.rectangle(frame, (rx1, card2_y1), (rx2, card2_y1 + 30), (38, 38, 44), -1)
        cv2.putText(frame, "OPERATOR ACTIONS & QUALITY GATE", (rx1 + 15, card2_y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (240, 240, 240), 1, cv2.LINE_AA)

        # Action Buttons (Side by Side & Stacked Layout)
        btn_w = rx2 - rx1 - 30

        # Button 1: Accept & Plot (Large Prominent Green)
        self._draw_button(
            frame,
            btn_id="accept",
            label="[ ✓ ACCEPT & PLOT DESIGN ]",
            sublabel="Press ENTER or A  —  Compile G-Code and stream to CNC",
            rect=(rx1 + 15, card2_y1 + 45, rx2 - 15, card2_y1 + 105),
            bg_color=(32, 130, 48),
            hover_color=(42, 175, 65)
        )

        # Button 2: Regenerate Design (Cyan / Blue)
        self._draw_button(
            frame,
            btn_id="regenerate",
            label="[ 🔄 REGENERATE DESIGN ]",
            sublabel="Press R or SPACE  —  Request a new AI variation",
            rect=(rx1 + 15, card2_y1 + 115, rx1 + 15 + int(btn_w * 0.62), card2_y1 + 175),
            bg_color=(175, 95, 20),
            hover_color=(220, 125, 25)
        )

        # Button 3: Cancel (Dark Crimson)
        self._draw_button(
            frame,
            btn_id="cancel",
            label="[ ✕ CANCEL ]",
            sublabel="Press ESC or Q",
            rect=(rx1 + 25 + int(btn_w * 0.62), card2_y1 + 115, rx2 - 15, card2_y1 + 175),
            bg_color=(45, 45, 130),
            hover_color=(60, 60, 175)
        )

        # Bottom Shortcut hint bar
        cv2.putText(
            frame,
            "Tip: Click buttons with mouse or use keyboard hotkeys [ENTER], [R], [ESC]",
            (rx1 + 18, card2_y1 + 215),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.36,
            (140, 140, 150),
            1,
            cv2.LINE_AA
        )

        return frame

    def show_menu(
        self,
        json_spec: Dict[str, Any],
        iteration: int = 1,
        auto_accept: bool = False
    ) -> str:
        """
        Displays the review window and blocks until user clicks a button or presses a shortcut.
        Returns: 'accept', 'regenerate', or 'cancel'.
        """
        if auto_accept:
            logger.info("[UI] Auto-accept flag active. Proceeding automatically.")
            return "accept"

        logger.info("\n" + "=" * 60)
        logger.info("[UI MENU] Pookalam Design Preview Opened (Widescreen HUD).")
        logger.info("  -> Click [ACCEPT & PLOT] or press [ENTER] / [A] to proceed to CNC.")
        logger.info("  -> Click [REGENERATE] or press [R] / [SPACE] for a new AI design.")
        logger.info("  -> Click [CANCEL] or press [ESC] / [Q] to exit.")
        logger.info("=" * 60 + "\n")

        self.action = None

        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback(self.window_name, self._on_mouse)

            while self.action is None:
                hud_frame = self.build_hud_frame(json_spec, iteration=iteration)
                cv2.imshow(self.window_name, hud_frame)

                key = cv2.waitKey(30) & 0xFF

                # Key shortcuts
                if key in (13, 10, ord('a'), ord('A')):  # Enter or 'a'
                    self.action = "accept"
                elif key in (ord('r'), ord('R'), 32):    # 'r' or Space
                    self.action = "regenerate"
                elif key in (27, ord('q'), ord('Q')):    # ESC or 'q'
                    self.action = "cancel"

                # Check if window was closed with X button
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    if self.action is None:
                        self.action = "cancel"
                    break

            cv2.destroyWindow(self.window_name)
            cv2.waitKey(1)
            return self.action

        except Exception as e:
            logger.warning(f"[UI] GUI window failed ({e}). Falling back to terminal prompt.")
            while True:
                choice = input("\n[UI Review] Choose option: [A]ccept & Plot, [R]egenerate, [Q]uit: ").strip().lower()
                if choice in ("a", "accept", "y", "yes", ""):
                    return "accept"
                elif choice in ("r", "regen", "regenerate"):
                    return "regenerate"
                elif choice in ("q", "quit", "c", "cancel"):
                    return "cancel"


def review_pookalam_design(
    json_spec: Dict[str, Any],
    iteration: int = 1,
    auto_accept: bool = False
) -> str:
    """Convenience functional interface for the UI menu."""
    menu = PookalamReviewMenu()
    return menu.show_menu(json_spec, iteration=iteration, auto_accept=auto_accept)
