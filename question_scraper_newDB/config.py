"""
Configuration file for Serbian Questionnaire Scraper
Customize settings here instead of editing the main application
"""

import os

# ============================================================================
# API CONFIGURATION
# ============================================================================

# Base URL for the question database API
API_BASE_URL = "https://question-database-api.onrender.com"

# API endpoint timeouts (in seconds)
API_TIMEOUT = 10

# ============================================================================
# OCR CONFIGURATION
# ============================================================================

# Path to Tesseract-OCR executable
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Language for OCR - "srp" for Serbian
OCR_LANGUAGE = "srp"

# ============================================================================
# COLOR DETECTION CONFIGURATION
# ============================================================================

# HSV color ranges for green (correct answers)
# Format: (lower_hue, lower_sat, lower_val), (upper_hue, upper_sat, upper_val)
GREEN_LOWER = (35, 40, 40)      # Lower bound of green in HSV
GREEN_UPPER = (85, 255, 255)    # Upper bound of green in HSV

# HSV color ranges for red (incorrect answers)
# Red wraps around in HSV (0-10 and 170-180)
RED_LOWER_1 = (0, 40, 40)       # Red lower range 1
RED_UPPER_1 = (10, 255, 255)    # Red upper range 1
RED_LOWER_2 = (170, 40, 40)     # Red lower range 2 (wrap-around)
RED_UPPER_2 = (180, 255, 255)   # Red upper range 2 (wrap-around)

# Pixel count threshold for determining answer correctness
# If green_pixels > red_pixels, answer is marked as correct
# (This is handled in the code; adjust if needed for sensitivity)

# ============================================================================
# UI CONFIGURATION
# ============================================================================

# Main window size
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

# Application title
APP_TITLE = "Serbian Questionnaire Scraper"

# Button colors (RGB hex codes)
BUTTON_START_COLOR = "#4CAF50"      # Green
BUTTON_STOP_COLOR = "#f44336"       # Red
BUTTON_SYNC_COLOR = "#2196F3"       # Blue
BUTTON_PREVIEW_COLOR = "#FF9800"    # Orange

# Font settings
FONT_BUTTON = ("Arial", 12, "bold")
FONT_LABEL = ("Arial", 10)
FONT_TITLE = ("Arial", 11, "bold")
FONT_MONOSPACE = ("Courier", 9)

# ============================================================================
# CAPTURE CONFIGURATION
# ============================================================================

# Selection rectangle color for area selection (BGR format for OpenCV)
SELECTION_RECT_COLOR = (0, 255, 0)  # Green rectangle
SELECTION_RECT_WIDTH = 2             # Width in pixels

# Time to wait between consecutive captures (milliseconds)
# Set to 0 for no delay
CAPTURE_DELAY_MS = 500

# ============================================================================
# QUESTION TYPE RULES
# ============================================================================

# Automatically determine question type based on correct answers count:
# If correct_answers == 1: "single"
# If correct_answers > 1:  "multi"
# This is handled automatically in the application

# ============================================================================
# PREVIEW & DISPLAY CONFIGURATION
# ============================================================================

# Show full question text or truncated version in status
TRUNCATE_PREVIEW = True
PREVIEW_TEXT_LENGTH = 50

# Format for displaying captured time
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# LOGGING & DEBUG
# ============================================================================

# Enable debug output to console
DEBUG_MODE = False

# Log file path (set to None to disable file logging)
LOG_FILE = None  # Example: "scraper_debug.log"

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# Retry attempts for failed API requests
MAX_API_RETRIES = 2

# Wait time between retries (in seconds)
RETRY_WAIT_TIME = 2

# Enable SSL verification for API requests
# Set to False only for development/testing with self-signed certificates
VERIFY_SSL = True

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config():
    """
    Returns configuration as a dictionary
    Useful for passing config to different parts of the application
    """
    return {
        "api_url": API_BASE_URL,
        "api_timeout": API_TIMEOUT,
        "tesseract_path": TESSERACT_PATH,
        "ocr_language": OCR_LANGUAGE,
        "green_hsv": (GREEN_LOWER, GREEN_UPPER),
        "red_hsv": ((RED_LOWER_1, RED_UPPER_1), (RED_LOWER_2, RED_UPPER_2)),
        "debug": DEBUG_MODE,
    }

def validate_config():
    """
    Validates that all configuration values are set correctly
    Returns True if all settings are valid
    """
    # Check if Tesseract path exists
    if not os.path.exists(TESSERACT_PATH):
        print(f"WARNING: Tesseract-OCR not found at {TESSERACT_PATH}")
        print("Please install Tesseract-OCR or update TESSERACT_PATH in config.py")
        return False

    # Validate color ranges (HSV values should be 0-180 for H, 0-255 for S,V)
    if not (0 <= GREEN_LOWER[0] <= 180 and 0 <= GREEN_UPPER[0] <= 180):
        print("ERROR: Invalid GREEN hue range in config")
        return False

    # Check API URL format
    if not API_BASE_URL.startswith("http"):
        print("ERROR: Invalid API_BASE_URL in config")
        return False

    return True

# ============================================================================
# Example: Custom Color Detection for Different Languages/Contexts
# ============================================================================

# If you need to adjust color detection for different scenarios,
# you can create alternative color profiles:

COLOR_PROFILES = {
    "green_red": {
        "correct": (GREEN_LOWER, GREEN_UPPER),
        "incorrect": ((RED_LOWER_1, RED_UPPER_1), (RED_LOWER_2, RED_UPPER_2))
    },
    "blue_orange": {
        # Blue: 100-130 hue
        "correct": ((100, 40, 40), (130, 255, 255)),
        # Orange: 10-35 hue
        "incorrect": ((10, 40, 40), (35, 255, 255))
    },
    # Add more profiles as needed
}

# ============================================================================
# Version Information
# ============================================================================

APP_VERSION = "1.0"
APP_AUTHOR = "Question Scraper Project"
LAST_UPDATED = "November 2024"
