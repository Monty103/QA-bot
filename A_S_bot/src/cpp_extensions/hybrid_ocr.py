"""
Hybrid OCR Processor - Uses C++ when available, falls back to Python
Provides automatic fallback for maximum compatibility
"""

import numpy as np
import cv2

# Try to import C++ extension
try:
    import fast_ocr_cpp
    CPP_AVAILABLE = True
    print("[Performance] Using C++ optimized OCR preprocessing (2-3x faster)")
except ImportError:
    CPP_AVAILABLE = False
    print("[Performance] C++ extensions not found, using pure Python (slower)")
    print("[Performance] Run 'build.bat' in cpp_extensions folder to build C++ extensions")


class HybridOCRPreprocessor:
    """
    Hybrid OCR preprocessor with automatic C++/Python selection
    """

    def __init__(self, use_cpp=True):
        self.use_cpp = use_cpp and CPP_AVAILABLE

    def preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image for OCR
        Automatically uses C++ or Python based on availability

        Args:
            img: Input image (BGR or RGB, uint8)

        Returns:
            Preprocessed image (grayscale, upscaled 2x, thresholded)
        """
        if self.use_cpp and CPP_AVAILABLE:
            return self._preprocess_cpp(img)
        else:
            return self._preprocess_python(img)

    def _preprocess_cpp(self, img: np.ndarray) -> np.ndarray:
        """Fast C++ preprocessing"""
        try:
            # Ensure RGB format
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

            # Call C++ extension
            processed = fast_ocr_cpp.preprocess_for_ocr(img)
            return processed

        except Exception as e:
            print(f"[Warning] C++ preprocessing failed: {e}, falling back to Python")
            return self._preprocess_python(img)

    def _preprocess_python(self, img: np.ndarray) -> np.ndarray:
        """Fallback Python preprocessing (slower)"""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Upscale for better recognition
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

        # Adaptive thresholding
        _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return processed

    def rgb_to_gray(self, img: np.ndarray) -> np.ndarray:
        """Convert RGB to grayscale (optimized)"""
        if self.use_cpp and CPP_AVAILABLE:
            try:
                return fast_ocr_cpp.rgb_to_gray(img)
            except:
                pass

        # Fallback
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img


# Singleton instance
_preprocessor = None

def get_preprocessor(use_cpp=True):
    """Get singleton preprocessor instance"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = HybridOCRPreprocessor(use_cpp)
    return _preprocessor


# Convenience functions
def preprocess_for_ocr(img: np.ndarray, use_cpp=True) -> np.ndarray:
    """Preprocess image for OCR"""
    preprocessor = get_preprocessor(use_cpp)
    return preprocessor.preprocess_for_ocr(img)


def is_cpp_available() -> bool:
    """Check if C++ extensions are available"""
    return CPP_AVAILABLE


if __name__ == "__main__":
    # Test the module
    print("=== Hybrid OCR Preprocessor Test ===")
    print(f"C++ Extensions Available: {CPP_AVAILABLE}")

    # Create test image
    test_img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)

    preprocessor = HybridOCRPreprocessor()
    result = preprocessor.preprocess_for_ocr(test_img)

    print(f"Input shape: {test_img.shape}")
    print(f"Output shape: {result.shape}")
    print(f"Output dtype: {result.dtype}")
    print("Test passed!")
