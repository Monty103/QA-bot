"""
Radio Button Detector - Template-based detection for bubbles and checkboxes
Finds radio button/checkbox positions and extracts associated answer text
Uses template matching for reliable detection
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pathlib import Path


class RadioButtonDetector:
    """Detect radio buttons/checkboxes and extract answer information using template matching"""

    # Orange color range in HSV (for selected state detection)
    ORANGE_HSV_LOWER = np.array([5, 100, 100])
    ORANGE_HSV_UPPER = np.array([25, 255, 255])

    # Selection detection thresholds
    ORANGE_PIXEL_THRESHOLD = 0.15  # 15% of bubble area must be orange to be "selected"

    def __init__(self, tesseract_path, ocr_language="srp+eng", templates_dir=None):
        """
        Initialize radio button detector with template matching

        Args:
            tesseract_path: Path to Tesseract executable
            ocr_language: Language for OCR
            templates_dir: Directory containing bubble template images (default: ../docs/)
        """
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.ocr_language = ocr_language

        # Determine templates directory
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "docs"
        else:
            templates_dir = Path(templates_dir)

        # Load bubble templates
        self.templates = self._load_templates(templates_dir)

        # Template matching threshold
        self.match_threshold = 0.7

    def _load_templates(self, templates_dir):
        """
        Load all bubble template images

        Args:
            templates_dir: Path to directory containing templates

        Returns:
            Dict of template images
        """
        templates = {}

        template_files = {
            'circle_unselected': 'bubble_1_answer.png',
            'circle_selected': 'bubble_selected_1_answer.png',
            'square_unselected': 'bubble_multy_answer.png',
            'square_selected': 'bubble_selected_multy_answer.png',
        }

        for name, filename in template_files.items():
            path = templates_dir / filename
            if path.exists():
                # Load as color image first, then convert
                template = cv2.imread(str(path), cv2.IMREAD_COLOR)
                if template is not None:
                    # Store both color and grayscale versions
                    templates[name] = {
                        'color': template,
                        'gray': cv2.cvtColor(template, cv2.COLOR_BGR2GRAY),
                        'size': (template.shape[1], template.shape[0])  # (width, height)
                    }
                    print(f"[*] Loaded template: {name} ({template.shape[1]}x{template.shape[0]})")
                else:
                    print(f"[WARN] Failed to load template: {path}")
            else:
                print(f"[WARN] Template not found: {path}")

        return templates

    def find_radio_buttons(self, screenshot, region):
        """
        Find all radio buttons/checkboxes and extract their information

        Args:
            screenshot: PIL Image or numpy array of screenshot
            region: Dict with 'x', 'y', 'width', 'height' keys

        Returns:
            List of dicts with:
                - position: (x, y) center of button (in full screenshot coords)
                - text: Answer text next to button
                - selected: Boolean if button is selected
                - bubble_type: 'circle' or 'square'
        """
        # Convert PIL to numpy if needed
        if isinstance(screenshot, Image.Image):
            img = np.array(screenshot)
        else:
            img = screenshot.copy()

        # Ensure BGR format for OpenCV
        if len(img.shape) == 3 and img.shape[2] == 3:
            # Check if RGB (PIL) or BGR (OpenCV)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = img

        # Crop to answer region
        x = region.get('x', 0)
        y = region.get('y', 0)
        width = region.get('width', img.shape[1])
        height = region.get('height', img.shape[0])

        answers_area = img_bgr[y:y+height, x:x+width]
        answers_area_rgb = img[y:y+height, x:x+width]  # Keep RGB for OCR

        # Find bubbles using template matching
        bubbles = self._find_bubbles_template(answers_area)

        if not bubbles:
            # Fallback: try with relaxed threshold
            bubbles = self._find_bubbles_template(answers_area, threshold=0.6)

        if not bubbles:
            print("[WARN] No bubbles detected with template matching")
            return []

        # Extract answer information for each bubble
        answers = []
        for bubble in bubbles:
            bx, by, bw, bh, bubble_type = bubble

            # Calculate center
            cx = bx + bw // 2
            cy = by + bh // 2

            # Check if selected using color detection
            is_selected = self._is_selected_by_color(answers_area, bx, by, bw, bh)

            # Extract text to the right of bubble
            answer_text = self._extract_answer_text(answers_area_rgb, bx, by, bw, bh)

            # Convert coordinates back to full screenshot
            full_x = x + cx
            full_y = y + cy

            answers.append({
                'position': (full_x, full_y),
                'bbox': (x + bx, y + by, bw, bh),
                'text': answer_text,
                'selected': is_selected,
                'bubble_type': bubble_type
            })

        # Sort by Y position (top to bottom)
        answers = sorted(answers, key=lambda a: a['position'][1])

        print(f"[DEBUG] Found {len(answers)} answers: {[a['bubble_type'] for a in answers]}")
        return answers

    def _find_bubbles_template(self, img, threshold=None):
        """
        Find bubbles using template matching

        Args:
            img: Input image (BGR numpy array)
            threshold: Match threshold (default: self.match_threshold)

        Returns:
            List of (x, y, width, height, type) tuples
        """
        if threshold is None:
            threshold = self.match_threshold

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        bubbles = []

        # Try each template type (prefer unselected templates for detection)
        template_priority = [
            ('circle_unselected', 'circle'),
            ('square_unselected', 'square'),
            ('circle_selected', 'circle'),
            ('square_selected', 'square'),
        ]

        found_positions = []  # Track found positions to avoid duplicates

        for template_name, bubble_type in template_priority:
            if template_name not in self.templates:
                continue

            template_data = self.templates[template_name]
            template_gray = template_data['gray']
            tw, th = template_data['size']

            # Skip if template is larger than image
            if tw > gray.shape[1] or th > gray.shape[0]:
                continue

            # Multi-scale template matching
            for scale in [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5]:
                scaled_w = int(tw * scale)
                scaled_h = int(th * scale)

                if scaled_w > gray.shape[1] or scaled_h > gray.shape[0]:
                    continue
                if scaled_w < 10 or scaled_h < 10:
                    continue

                scaled_template = cv2.resize(template_gray, (scaled_w, scaled_h))

                # Perform template matching
                result = cv2.matchTemplate(gray, scaled_template, cv2.TM_CCOEFF_NORMED)

                # Find all matches above threshold
                locations = np.where(result >= threshold)

                for pt in zip(*locations[::-1]):  # x, y
                    px, py = pt

                    # Check if this position already has a bubble (avoid duplicates)
                    is_duplicate = False
                    for fx, fy, fw, fh, _ in found_positions:
                        # Check overlap
                        if abs(px - fx) < max(scaled_w, fw) * 0.5 and abs(py - fy) < max(scaled_h, fh) * 0.5:
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        found_positions.append((px, py, scaled_w, scaled_h, bubble_type))
                        bubbles.append((px, py, scaled_w, scaled_h, bubble_type))

        return bubbles

    def _is_selected_by_color(self, img, x, y, w, h):
        """
        Check if bubble is selected by detecting orange color

        Args:
            img: Image containing the bubble (BGR)
            x, y, w, h: Bubble bounding box

        Returns:
            Boolean indicating if selected
        """
        # Extract bubble region with small padding
        pad = 2
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img.shape[1], x + w + pad)
        y2 = min(img.shape[0], y + h + pad)

        bubble_region = img[y1:y2, x1:x2]

        if bubble_region.size == 0:
            return False

        # Convert to HSV
        hsv = cv2.cvtColor(bubble_region, cv2.COLOR_BGR2HSV)

        # Create mask for orange color
        mask = cv2.inRange(hsv, self.ORANGE_HSV_LOWER, self.ORANGE_HSV_UPPER)

        # Calculate percentage of orange pixels
        total_pixels = mask.size
        orange_pixels = np.count_nonzero(mask)
        orange_ratio = orange_pixels / total_pixels if total_pixels > 0 else 0

        is_selected = orange_ratio >= self.ORANGE_PIXEL_THRESHOLD

        return is_selected

    def _extract_answer_text(self, img, bx, by, bw, bh):
        """
        Extract text associated with a bubble

        Args:
            img: Image containing the bubble (RGB for OCR)
            bx, by, bw, bh: Bubble bounding box

        Returns:
            Extracted text string
        """
        # Define text region to the right of bubble
        # Give more vertical space for multi-line answers
        text_x_start = bx + bw + 5
        text_x_end = img.shape[1]  # Go to end of region

        # Expand vertical range to capture full text line
        line_height = max(30, bh * 2)  # At least 30px or 2x bubble height
        text_y_start = max(0, by - 5)
        text_y_end = min(img.shape[0], by + line_height)

        # Ensure we have a valid region
        if text_x_start >= text_x_end or text_y_start >= text_y_end:
            return ""

        text_region = img[text_y_start:text_y_end, text_x_start:text_x_end]

        if text_region.size == 0:
            return ""

        # Preprocess for OCR
        processed = self._preprocess_text_area(text_region)

        # Extract text
        try:
            # Use PSM 7 for single line, or PSM 6 for block
            text = pytesseract.image_to_string(
                processed,
                lang=self.ocr_language,
                config='--oem 3 --psm 6'
            ).strip()

            # Clean up the text
            text = self._clean_ocr_text(text)
            return text
        except Exception as e:
            print(f"[WARN] Failed to extract answer text: {e}")
            return ""

    def _preprocess_text_area(self, img):
        """
        Preprocess text area for OCR

        Args:
            img: Input image (RGB numpy array)

        Returns:
            Preprocessed image
        """
        # Convert to grayscale if color
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img.copy()

        # Resize for better OCR (scale up small text)
        scale = 2
        scaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(scaled)

        # Light denoising (preserve text details)
        denoised = cv2.fastNlMeansDenoising(enhanced, h=8)

        # Adaptive thresholding works better for varying backgrounds
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        return binary

    def _clean_ocr_text(self, text):
        """
        Clean up OCR output

        Args:
            text: Raw OCR text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove common OCR artifacts
        text = text.replace('|', 'I')
        text = text.replace('}{', 'H')

        # Remove leading/trailing punctuation that's likely noise
        text = text.strip('.,;:-_=+[]{}()')

        return text

    def get_question_type(self, answers):
        """
        Determine question type from detected bubbles

        Args:
            answers: List of answer dicts from find_radio_buttons

        Returns:
            'single' for radio buttons, 'multiple' for checkboxes
        """
        if not answers:
            return 'unknown'

        # Check bubble types
        types = [a.get('bubble_type', 'circle') for a in answers]

        if 'square' in types:
            return 'multiple'
        return 'single'

    def get_selected_answers(self, answers):
        """
        Get list of currently selected answers

        Args:
            answers: List of answer dicts from find_radio_buttons

        Returns:
            List of selected answer dicts
        """
        return [a for a in answers if a.get('selected', False)]

    def click_button(self, position):
        """
        Click a button at position

        Args:
            position: (x, y) tuple of button center

        Returns:
            True if successful
        """
        try:
            import pyautogui
            x, y = position
            pyautogui.click(x, y)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to click button: {e}")
            return False


# Backwards compatibility - keep the old function signatures working
def find_closest_answer(click_position, answers, max_distance=50):
    """
    Find the answer closest to a click position

    Args:
        click_position: (x, y) tuple
        answers: List of answer dicts
        max_distance: Maximum distance to consider

    Returns:
        Closest answer dict or None
    """
    if not answers:
        return None

    cx, cy = click_position
    closest = None
    min_dist = float('inf')

    for answer in answers:
        ax, ay = answer['position']
        dist = ((cx - ax) ** 2 + (cy - ay) ** 2) ** 0.5

        if dist < min_dist and dist <= max_distance:
            min_dist = dist
            closest = answer

    return closest


def find_answer_by_text(target_text, answers, threshold=80):
    """
    Find answer by matching text

    Args:
        target_text: Text to search for
        answers: List of answer dicts
        threshold: Fuzzy match threshold (0-100)

    Returns:
        Matching answer dict or None
    """
    if not answers or not target_text:
        return None

    try:
        from fuzzywuzzy import fuzz
    except ImportError:
        # Fallback to simple matching
        target_lower = target_text.lower()
        for answer in answers:
            if target_lower in answer['text'].lower() or answer['text'].lower() in target_lower:
                return answer
        return None

    best_match = None
    best_score = 0

    for answer in answers:
        score = fuzz.ratio(target_text.lower(), answer['text'].lower())
        if score > best_score and score >= threshold:
            best_score = score
            best_match = answer

    return best_match
