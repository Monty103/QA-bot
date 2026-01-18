"""
Question Reader - OCR-based question text extraction
Extracts question text from questionnaire screenshots with improved preprocessing
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import re


class QuestionReader:
    """Extract question text from questionnaire using OCR"""

    def __init__(self, tesseract_path, ocr_language="srp+eng"):
        """
        Initialize question reader

        Args:
            tesseract_path: Path to Tesseract executable
            ocr_language: Language for OCR (default: Serbian + English)
        """
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.ocr_language = ocr_language

    def extract_question(self, screenshot, region):
        """
        Extract question text from screenshot

        Args:
            screenshot: PIL Image or numpy array of screenshot
            region: Dict with 'x', 'y', 'width', 'height' keys

        Returns:
            Extracted text string
        """
        # Convert PIL to numpy if needed
        if isinstance(screenshot, Image.Image):
            img = np.array(screenshot)
        else:
            img = screenshot

        # Crop to question region
        x = region.get('x', 0)
        y = region.get('y', 0)
        width = region.get('width', img.shape[1])
        height = region.get('height', img.shape[0])

        question_area = img[y:y+height, x:x+width]

        # Try multiple preprocessing methods and pick best result
        results = []

        # Method 1: Standard preprocessing
        processed1 = self._preprocess_standard(question_area)
        text1 = self._ocr_extract(processed1)
        if text1:
            results.append(text1)

        # Method 2: Adaptive threshold preprocessing
        processed2 = self._preprocess_adaptive(question_area)
        text2 = self._ocr_extract(processed2)
        if text2:
            results.append(text2)

        # Method 3: Minimal preprocessing (for already clean images)
        processed3 = self._preprocess_minimal(question_area)
        text3 = self._ocr_extract(processed3)
        if text3:
            results.append(text3)

        # Pick the best result (longest coherent text)
        if results:
            best = max(results, key=lambda t: self._text_quality_score(t))
            return best

        return ""

    def _ocr_extract(self, processed_img):
        """Run OCR on preprocessed image"""
        try:
            text = pytesseract.image_to_string(
                processed_img,
                lang=self.ocr_language,
                config='--oem 3 --psm 6'
            ).strip()
            return text
        except Exception as e:
            print(f"[ERROR] OCR failed: {e}")
            return ""

    def _text_quality_score(self, text):
        """
        Score text quality based on coherence

        Args:
            text: Input text

        Returns:
            Quality score (higher is better)
        """
        if not text:
            return 0

        score = len(text)

        # Penalize too many special characters
        special_ratio = sum(1 for c in text if not c.isalnum() and c not in ' .,?!:;-') / max(len(text), 1)
        if special_ratio > 0.3:
            score *= 0.5

        # Penalize too many short words (likely noise)
        words = text.split()
        if words:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len < 2:
                score *= 0.5

        # Bonus for Serbian/Latin characters
        cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        latin_count = sum(1 for c in text if c.isalpha() and c.isascii())
        if cyrillic_count > 0 or latin_count > 5:
            score *= 1.2

        return score

    def _preprocess_standard(self, img):
        """
        Standard preprocessing for OCR

        Args:
            img: Input image (numpy array)

        Returns:
            Preprocessed image
        """
        # Convert to grayscale if color
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img.copy()

        # Scale up for better OCR
        scale = 2
        scaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Increase contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(scaled)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        # Binary threshold
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def _preprocess_adaptive(self, img):
        """
        Adaptive threshold preprocessing (better for varying backgrounds)

        Args:
            img: Input image (numpy array)

        Returns:
            Preprocessed image
        """
        # Convert to grayscale if color
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img.copy()

        # Scale up
        scale = 2
        scaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Light denoise
        denoised = cv2.fastNlMeansDenoising(scaled, h=8)

        # Adaptive threshold
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15, 4
        )

        return binary

    def _preprocess_minimal(self, img):
        """
        Minimal preprocessing (for already clean/high-contrast images)

        Args:
            img: Input image (numpy array)

        Returns:
            Preprocessed image
        """
        # Convert to grayscale if color
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img.copy()

        # Just scale up
        scale = 2
        scaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        return scaled

    def clean_text(self, text):
        """
        Clean OCR output and filter headers/noise

        Args:
            text: Raw OCR text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Filter out common headers/titles (Serbian questionnaire)
        headers_to_remove = [
            r'^\d+\s*pitanj[ai].*?ispit',  # "4 Pitanja za teorijski ispit"
            r'^ve[zž]banj[ae]',  # "vezbanje", "vežbanje"
            r'^\d+\s*question',  # "4 Questions"
            r'^test\s*\d+',  # "Test 1"
            r'^practice',  # "Practice"
            r'^teorijski\s*ispit',  # "Teorijski ispit"
            r'^broj.*?odgovor',  # "Broj potrebnih odgovora"
            r'^pitanje\s*\d+/\d+',  # "Pitanje 6/8"
            r'^broj\s*poena',  # "Broj poena"
        ]

        for pattern in headers_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()

        # Remove leading numbers/bullets
        text = re.sub(r'^[\d\.\-\*\)\]\s]+', '', text).strip()

        # Remove common OCR artifacts
        text = text.replace('|', 'I')  # Pipe to I
        text = text.replace('}{', 'H')  # Curly braces to H

        # Fix common Serbian OCR errors
        text = text.replace('č', 'c').replace('ć', 'c')  # Normalize if needed
        text = text.replace('š', 's').replace('ž', 'z')

        # Remove lines that are too short (likely noise)
        if len(text) < 10:
            return ""

        return text

    def extract_question_with_confidence(self, screenshot, region):
        """
        Extract question text with confidence score

        Args:
            screenshot: PIL Image or numpy array of screenshot
            region: Dict with 'x', 'y', 'width', 'height' keys

        Returns:
            Tuple of (text, confidence)
        """
        # Convert PIL to numpy if needed
        if isinstance(screenshot, Image.Image):
            img = np.array(screenshot)
        else:
            img = screenshot

        # Crop to question region
        x = region.get('x', 0)
        y = region.get('y', 0)
        width = region.get('width', img.shape[1])
        height = region.get('height', img.shape[0])

        question_area = img[y:y+height, x:x+width]

        # Preprocess
        processed = self._preprocess_adaptive(question_area)

        try:
            # Get detailed OCR data including confidence
            data = pytesseract.image_to_data(
                processed,
                lang=self.ocr_language,
                config='--oem 3 --psm 6',
                output_type=pytesseract.Output.DICT
            )

            # Extract text and calculate average confidence
            words = []
            confidences = []

            for i, text in enumerate(data['text']):
                conf = int(data['conf'][i])
                if conf > 0 and text.strip():
                    words.append(text)
                    confidences.append(conf)

            full_text = ' '.join(words)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return full_text, avg_confidence

        except Exception as e:
            print(f"[ERROR] OCR with confidence failed: {e}")
            return "", 0
