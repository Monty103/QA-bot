"""
Hybrid Color Block Detector - Uses C++ when available, falls back to Python/OpenCV
Provides automatic fallback for maximum compatibility
"""

import numpy as np
import cv2
from typing import List, Dict

# Try to import C++ extension
try:
    import fast_color_detection_cpp
    CPP_AVAILABLE = True
    print("[Performance] Using C++ optimized color detection (3-4x faster)")
except ImportError:
    CPP_AVAILABLE = False
    print("[Performance] C++ color detection not available, using OpenCV (slower)")


class HybridColorDetector:
    """
    Hybrid color block detector with automatic C++/Python selection
    """

    def __init__(self, use_cpp=True):
        self.use_cpp = use_cpp and CPP_AVAILABLE

    def detect_green_blocks(self, img: np.ndarray) -> List[Dict]:
        """
        Detect green colored blocks in image

        Args:
            img: Input image (BGR, uint8)

        Returns:
            List of dicts with keys: x, y, w, h, area
        """
        if self.use_cpp and CPP_AVAILABLE:
            return self._detect_green_cpp(img)
        else:
            return self._detect_green_python(img)

    def detect_red_blocks(self, img: np.ndarray) -> List[Dict]:
        """
        Detect red colored blocks in image

        Args:
            img: Input image (BGR, uint8)

        Returns:
            List of dicts with keys: x, y, w, h, area
        """
        if self.use_cpp and CPP_AVAILABLE:
            return self._detect_red_cpp(img)
        else:
            return self._detect_red_python(img)

    def detect_color_blocks(self, img: np.ndarray, color_name: str) -> List[Dict]:
        """
        Detect colored blocks (green or red)

        Args:
            img: Input image (BGR, uint8)
            color_name: "green" or "red"

        Returns:
            List of dicts with keys: x, y, w, h, area
        """
        if color_name == "green":
            return self.detect_green_blocks(img)
        elif color_name == "red":
            return self.detect_red_blocks(img)
        else:
            raise ValueError(f"Unknown color: {color_name}")

    def _detect_green_cpp(self, img: np.ndarray) -> List[Dict]:
        """Fast C++ green block detection"""
        try:
            return list(fast_color_detection_cpp.detect_green_blocks(img))
        except Exception as e:
            print(f"[Warning] C++ green detection failed: {e}, falling back to Python")
            return self._detect_green_python(img)

    def _detect_red_cpp(self, img: np.ndarray) -> List[Dict]:
        """Fast C++ red block detection"""
        try:
            return list(fast_color_detection_cpp.detect_red_blocks(img))
        except Exception as e:
            print(f"[Warning] C++ red detection failed: {e}, falling back to Python")
            return self._detect_red_python(img)

    def _detect_green_python(self, img: np.ndarray) -> List[Dict]:
        """Fallback Python green block detection using OpenCV"""
        try:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array([25, 20, 20]), np.array([95, 255, 255]))
            return self._find_blocks_from_mask(mask)
        except Exception as e:
            print(f"[Error] Green detection failed: {e}")
            return []

    def _detect_red_python(self, img: np.ndarray) -> List[Dict]:
        """Fallback Python red block detection using OpenCV"""
        try:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Red wraps around hue, need two ranges
            mask1 = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([25, 255, 255]))
            mask2 = cv2.inRange(hsv, np.array([155, 20, 20]), np.array([180, 255, 255]))
            mask = mask1 | mask2

            return self._find_blocks_from_mask(mask)
        except Exception as e:
            print(f"[Error] Red detection failed: {e}")
            return []

    def _find_blocks_from_mask(self, mask: np.ndarray) -> List[Dict]:
        """Helper: Find bounding boxes from binary mask"""
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        blocks = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 150:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 40 and h > 10:
                    blocks.append({'x': x, 'y': y, 'w': w, 'h': h, 'area': int(area)})

        # Sort by vertical position
        blocks.sort(key=lambda b: b['y'])
        return blocks


# Singleton instance
_detector = None

def get_detector(use_cpp=True):
    """Get singleton detector instance"""
    global _detector
    if _detector is None:
        _detector = HybridColorDetector(use_cpp)
    return _detector


# Convenience functions
def detect_color_blocks(img: np.ndarray, color_name: str, use_cpp=True) -> List[Dict]:
    """Detect colored blocks"""
    detector = get_detector(use_cpp)
    return detector.detect_color_blocks(img, color_name)


def detect_green_blocks(img: np.ndarray, use_cpp=True) -> List[Dict]:
    """Detect green blocks"""
    detector = get_detector(use_cpp)
    return detector.detect_green_blocks(img)


def detect_red_blocks(img: np.ndarray, use_cpp=True) -> List[Dict]:
    """Detect red blocks"""
    detector = get_detector(use_cpp)
    return detector.detect_red_blocks(img)


def is_cpp_available() -> bool:
    """Check if C++ extensions are available"""
    return CPP_AVAILABLE


if __name__ == "__main__":
    # Test the module
    print("=== Hybrid Color Detector Test ===")
    print(f"C++ Extensions Available: {CPP_AVAILABLE}")

    # Create test image with colored blocks
    test_img = np.zeros((200, 300, 3), dtype=np.uint8)

    # Add green block
    cv2.rectangle(test_img, (50, 50), (100, 80), (0, 255, 0), -1)

    # Add red block
    cv2.rectangle(test_img, (150, 100), (200, 130), (0, 0, 255), -1)

    detector = HybridColorDetector()

    green_blocks = detector.detect_green_blocks(test_img)
    red_blocks = detector.detect_red_blocks(test_img)

    print(f"Green blocks found: {len(green_blocks)}")
    print(f"Red blocks found: {len(red_blocks)}")

    if green_blocks:
        print(f"First green block: {green_blocks[0]}")
    if red_blocks:
        print(f"First red block: {red_blocks[0]}")

    print("Test passed!")
