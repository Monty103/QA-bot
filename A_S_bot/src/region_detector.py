"""
Region Detector - Dynamic region detection using anchor points
Finds question and answer regions automatically regardless of screen resolution
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path


class RegionDetector:
    """Dynamically detect question and answer regions using anchor templates"""

    def __init__(self, templates_dir=None):
        """
        Initialize region detector

        Args:
            templates_dir: Directory containing anchor template images (default: ../docs/)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "docs"
        else:
            templates_dir = Path(templates_dir)

        self.templates_dir = templates_dir
        self.anchors = self._load_anchor_templates()

        # Cache for detected regions (reset when screen changes)
        self._cached_regions = None
        self._last_screenshot_hash = None

    def _load_anchor_templates(self):
        """Load anchor point templates"""
        anchors = {}

        anchor_files = {
            'next_button': 'next_question.png',
            'prev_button': 'previouse_question.png',
            'bubble_circle': 'bubble_1_answer.png',
            'bubble_square': 'bubble_multy_answer.png',
            'bubble_circle_selected': 'bubble_selected_1_answer.png',
            'bubble_square_selected': 'bubble_selected_multy_answer.png',
        }

        for name, filename in anchor_files.items():
            path = self.templates_dir / filename
            if path.exists():
                template = cv2.imread(str(path), cv2.IMREAD_COLOR)
                if template is not None:
                    anchors[name] = {
                        'color': template,
                        'gray': cv2.cvtColor(template, cv2.COLOR_BGR2GRAY),
                        'size': (template.shape[1], template.shape[0])
                    }
                    print(f"[*] Loaded anchor: {name} ({template.shape[1]}x{template.shape[0]})")

        return anchors

    def detect_regions(self, screenshot, use_cache=True):
        """
        Detect question and answer regions dynamically

        Args:
            screenshot: PIL Image or numpy array of screenshot
            use_cache: Use cached regions if screenshot hasn't changed significantly

        Returns:
            Dict with 'question_region' and 'answer_region' keys,
            each containing 'x', 'y', 'width', 'height'
        """
        # Convert PIL to numpy if needed
        if isinstance(screenshot, Image.Image):
            img = np.array(screenshot)
        else:
            img = screenshot.copy()

        # Convert RGB to BGR for OpenCV
        if len(img.shape) == 3 and img.shape[2] == 3:
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = img

        screen_height, screen_width = img.shape[:2]

        # Find anchor points
        nav_buttons = self._find_navigation_buttons(img_bgr)
        first_bubble = self._find_first_bubble(img_bgr)
        header_bottom = self._find_header_bottom(img_bgr)

        # Calculate regions based on anchors
        regions = self._calculate_regions(
            screen_width, screen_height,
            nav_buttons, first_bubble, header_bottom
        )

        return regions

    def _find_navigation_buttons(self, img):
        """
        Find navigation buttons (Previous/Next question)

        Args:
            img: Screenshot in BGR format

        Returns:
            Dict with button positions or None
        """
        results = {}

        for btn_name in ['prev_button', 'next_button']:
            if btn_name not in self.anchors:
                continue

            anchor = self.anchors[btn_name]
            pos = self._template_match(img, anchor, threshold=0.7)

            if pos:
                results[btn_name] = pos
                print(f"[DEBUG] Found {btn_name} at {pos}")

        return results if results else None

    def _find_first_bubble(self, img):
        """
        Find the first (topmost) bubble in the screenshot

        Args:
            img: Screenshot in BGR format

        Returns:
            Dict with 'x', 'y', 'width', 'height' of first bubble, or None
        """
        all_bubbles = []

        # Search for all bubble types
        for bubble_name in ['bubble_circle', 'bubble_square',
                           'bubble_circle_selected', 'bubble_square_selected']:
            if bubble_name not in self.anchors:
                continue

            anchor = self.anchors[bubble_name]
            positions = self._template_match_all(img, anchor, threshold=0.7)

            for pos in positions:
                all_bubbles.append(pos)

        if not all_bubbles:
            print("[WARN] No bubbles found for region detection")
            return None

        # Find topmost bubble (smallest y)
        first = min(all_bubbles, key=lambda b: b['y'])
        print(f"[DEBUG] First bubble at y={first['y']}")
        return first

    def _find_header_bottom(self, img):
        """
        Find the bottom of the header area (blue bar)

        Args:
            img: Screenshot in BGR format

        Returns:
            Y coordinate of header bottom, or default value
        """
        # The header is a blue bar at the top
        # Look for transition from blue to white/light background

        # Convert to HSV for blue detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Blue color range (the header bar)
        blue_lower = np.array([100, 50, 50])
        blue_upper = np.array([130, 255, 255])

        blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)

        # Scan from top to find where blue header ends
        height = img.shape[0]
        header_bottom = 50  # Default

        for y in range(min(200, height)):  # Only check top 200 pixels
            row = blue_mask[y, :]
            blue_ratio = np.count_nonzero(row) / len(row)

            # If row is mostly blue (>50%), we're still in header
            if blue_ratio > 0.5:
                header_bottom = y + 1

        # Add some padding
        header_bottom += 10

        print(f"[DEBUG] Header bottom at y={header_bottom}")
        return header_bottom

    def _calculate_regions(self, screen_width, screen_height,
                          nav_buttons, first_bubble, header_bottom):
        """
        Calculate question and answer regions based on detected anchors

        Args:
            screen_width, screen_height: Screen dimensions
            nav_buttons: Dict of navigation button positions
            first_bubble: First bubble position
            header_bottom: Y coordinate of header bottom

        Returns:
            Dict with 'question_region' and 'answer_region'
        """
        # Default margins
        left_margin = 25
        right_margin = 50

        # Determine bottom boundary from navigation buttons
        if nav_buttons:
            # Use the topmost navigation button as bottom boundary
            nav_y = min(btn['y'] for btn in nav_buttons.values())
            content_bottom = nav_y - 20  # 20px padding above buttons
        else:
            # Fallback: 85% of screen height
            content_bottom = int(screen_height * 0.85)

        # Determine where answers start (first bubble)
        if first_bubble:
            answers_start = first_bubble['y'] - 10  # Small padding above first bubble
        else:
            # Fallback: estimate based on header
            answers_start = header_bottom + 60

        # Question region: from header to just before answers
        question_region = {
            'x': left_margin,
            'y': header_bottom,
            'width': screen_width - left_margin - right_margin,
            'height': max(30, answers_start - header_bottom - 10)
        }

        # Answer region: from first bubble to navigation buttons
        answer_region = {
            'x': left_margin,
            'y': answers_start,
            'width': screen_width - left_margin - right_margin,
            'height': max(100, content_bottom - answers_start)
        }

        print(f"[*] Detected question region: {question_region}")
        print(f"[*] Detected answer region: {answer_region}")

        return {
            'question_region': question_region,
            'answer_region': answer_region,
            'anchors_found': {
                'nav_buttons': nav_buttons is not None,
                'first_bubble': first_bubble is not None,
                'header': header_bottom > 50
            }
        }

    def _template_match(self, img, anchor, threshold=0.7):
        """
        Find single best match for template

        Args:
            img: Screenshot in BGR format
            anchor: Anchor dict with 'gray' and 'size' keys
            threshold: Match threshold

        Returns:
            Dict with 'x', 'y', 'width', 'height' or None
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        template = anchor['gray']
        tw, th = anchor['size']

        # Multi-scale matching
        best_match = None
        best_val = 0

        for scale in [0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0]:
            scaled_w = int(tw * scale)
            scaled_h = int(th * scale)

            if scaled_w > gray.shape[1] or scaled_h > gray.shape[0]:
                continue
            if scaled_w < 5 or scaled_h < 5:
                continue

            scaled_template = cv2.resize(template, (scaled_w, scaled_h))

            result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > best_val and max_val >= threshold:
                best_val = max_val
                best_match = {
                    'x': max_loc[0],
                    'y': max_loc[1],
                    'width': scaled_w,
                    'height': scaled_h,
                    'confidence': max_val
                }

        return best_match

    def _template_match_all(self, img, anchor, threshold=0.7):
        """
        Find all matches for template

        Args:
            img: Screenshot in BGR format
            anchor: Anchor dict with 'gray' and 'size' keys
            threshold: Match threshold

        Returns:
            List of dicts with 'x', 'y', 'width', 'height'
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        template = anchor['gray']
        tw, th = anchor['size']

        matches = []
        found_positions = []

        for scale in [0.75, 0.9, 1.0, 1.1, 1.25, 1.5]:
            scaled_w = int(tw * scale)
            scaled_h = int(th * scale)

            if scaled_w > gray.shape[1] or scaled_h > gray.shape[0]:
                continue
            if scaled_w < 5 or scaled_h < 5:
                continue

            scaled_template = cv2.resize(template, (scaled_w, scaled_h))

            result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)

            for pt in zip(*locations[::-1]):
                px, py = pt

                # Check for duplicates
                is_dup = False
                for fx, fy in found_positions:
                    if abs(px - fx) < scaled_w * 0.5 and abs(py - fy) < scaled_h * 0.5:
                        is_dup = True
                        break

                if not is_dup:
                    found_positions.append((px, py))
                    matches.append({
                        'x': px,
                        'y': py,
                        'width': scaled_w,
                        'height': scaled_h
                    })

        return matches


def detect_screen_regions(screenshot, templates_dir=None):
    """
    Convenience function to detect regions in a screenshot

    Args:
        screenshot: PIL Image or numpy array
        templates_dir: Path to templates directory

    Returns:
        Dict with 'question_region' and 'answer_region'
    """
    detector = RegionDetector(templates_dir)
    return detector.detect_regions(screenshot)
