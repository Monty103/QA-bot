"""
Click Monitor - Detects user clicks in answer region
Monitors mouse position and identifies clicks within the answer area
"""

import time
from pynput import mouse
from fuzzywuzzy import fuzz


class ClickMonitor:
    """Monitor for user clicks in answer region"""

    def __init__(self, answer_region, click_threshold=5):
        """
        Initialize click monitor

        Args:
            answer_region: Dict with 'x', 'y', 'width', 'height' keys
            click_threshold: Minimum distance (pixels) to detect as click (unused, kept for API compatibility)
        """
        self.answer_region = answer_region
        self.click_threshold = click_threshold

        self.click_detected = False
        self.clicked_position = None
        self.click_time = None
        self.listener = None

    def start(self):
        """Start the mouse listener"""
        if self.listener is None:
            try:
                self.listener = mouse.Listener(on_click=self._on_mouse_click)
                self.listener.start()
            except Exception as e:
                print(f"[WARN] Could not start click listener: {e}")
                self.listener = None

    def check_click(self):
        """
        Check if user clicked in answer region

        Returns:
            Boolean indicating if click detected
        """
        return self.click_detected

    def get_click_position(self):
        """
        Get position where user clicked

        Returns:
            (x, y) tuple or None
        """
        return self.clicked_position

    def reset_click(self):
        """Reset click detection for next click"""
        self.click_detected = False
        self.clicked_position = None
        self.click_time = None

    def _on_mouse_click(self, x, y, button, pressed):
        """Mouse click event handler"""
        # Only handle button press (not release)
        if pressed and button == mouse.Button.left:
            # Check if in answer region
            if self._in_region((x, y)):
                self.click_detected = True
                self.clicked_position = (x, y)
                self.click_time = time.time()

    def _in_region(self, position):
        """Check if position is in answer region"""
        x, y = position

        region_x = self.answer_region.get('x', 0)
        region_y = self.answer_region.get('y', 0)
        region_w = self.answer_region.get('width', 1000)
        region_h = self.answer_region.get('height', 300)

        return (region_x <= x < region_x + region_w and
                region_y <= y < region_y + region_h)

    def _distance(self, pos1, pos2):
        """Calculate distance between two positions"""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        return (dx**2 + dy**2)**0.5

    def stop(self):
        """Stop monitoring"""
        if self.listener:
            self.listener.stop()

    def __del__(self):
        """Cleanup on deletion"""
        self.stop()


def find_closest_answer(click_pos, answers):
    """
    Find which answer was clicked

    Args:
        click_pos: (x, y) click position
        answers: List of answer dicts with 'position' key

    Returns:
        Answer dict or None
    """
    if not answers:
        return None

    closest = None
    min_distance = float('inf')

    for answer in answers:
        pos = answer['position']
        dist = (click_pos[0] - pos[0])**2 + (click_pos[1] - pos[1])**2
        dist = dist**0.5

        if dist < min_distance:
            min_distance = dist
            closest = answer

    # Only return if reasonably close (within 100 pixels)
    if min_distance < 100:
        return closest

    return None


def find_answer_by_text(target_text, answers, threshold=80):
    """
    Find answer by text content using fuzzy matching

    Args:
        target_text: Text to search for
        answers: List of answer dicts with 'text' key
        threshold: Minimum similarity threshold (0-100)

    Returns:
        Answer dict or None
    """
    if not answers:
        return None

    best_match = None
    best_score = 0

    for answer in answers:
        score = fuzz.ratio(target_text.lower(), answer['text'].lower())

        if score > best_score:
            best_score = score
            best_match = answer

    # Only return if good match
    if best_score >= threshold:
        return best_match

    return None
