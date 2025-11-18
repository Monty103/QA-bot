"""
AUTO TEST CORRECTOR - ENHANCED VERSION
Fully automatic test monitoring and correction system

Features:
- Monitors screen continuously in background
- Detects user answer selections automatically
- Validates against database using fuzzy matching
- Auto-corrects ONLY wrong answers
- Detects question type (single/multi) automatically via box shape
- Serbian language support (latinica) + English
- Comprehensive logging and statistics
- Modular architecture for easy maintenance

Version: 2.0
Last Updated: 2025

TODO: Import json DB
    - Switch to new DB
    - optimize import APP (question_scrapper) for new DB
    -
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageTk, ImageEnhance
import pyautogui
import sqlite3
import json
import os
import time
import threading
from datetime import datetime
from fuzzywuzzy import fuzz
import re
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


# =====================================================================
# UTILITY CLASSES FOR MODULAR ARCHITECTURE
# =====================================================================

class Config:
    """Configuration management"""
    def __init__(self):
        self.TESSERACT_PATH = r"C:\dt\Tesseract-OCR\tesseract.exe"
        self.DB_FILE = "test_questions.db"
        self.FUZZY_THRESHOLD = 85  # Minimum similarity for matching
        self.OCR_LANG = "srp+eng"  # Serbian + English
        self.MONITOR_INTERVAL = 0.5  # Screenshot interval in seconds
        self.CLICK_DETECT_THRESHOLD = 5  # Screen change threshold
        self.CORRECTION_DELAY = 0.2  # Delay between auto-clicks

        # Shape detection for question type
        self.CIRCLE_MIN_CIRCULARITY = 0.7  # For radio buttons
        self.SQUARE_MAX_CIRCULARITY = 0.5  # For checkboxes


class OCRProcessor:
    """Enhanced OCR processing with Serbian support"""

    def __init__(self, config: Config):
        self.config = config
        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH

    def extract_text(self, img: np.ndarray, enhance: bool = True) -> Tuple[str, float]:
        """
        Extract text from image with optional enhancement
        Returns: (text, confidence)
        """
        try:
            if enhance:
                img = self._preprocess_image(img)

            # Try Serbian + English first
            text = pytesseract.image_to_string(
                img,
                lang=self.config.OCR_LANG,
                config="--oem 1 --psm 6"
            ).strip()

            confidence = 75  # Baseline confidence

            if not text:
                # Fallback to English only
                text = pytesseract.image_to_string(
                    img,
                    lang="eng",
                    config="--psm 6"
                ).strip()
                confidence = 60

            return text, confidence

        except Exception as e:
            print(f"OCR Error: {e}")
            return "", 0

    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR"""
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

    @staticmethod
    def clean_question_text(text: str) -> str:
        """Clean question text by removing indicators and bubble chars"""
        # Remove "Broj potrebnih odgovora: N"
        cleaned = re.sub(
            r"Broj potrebnih odgovora:\s*\d+",
            "",
            text,
            flags=re.IGNORECASE
        )

        # Remove bubble characters from line starts
        lines = []
        for line in cleaned.split('\n'):
            line = line.strip()
            if line:
                # Remove leading bubble chars
                line = re.sub(r'^[0oOоОФфΦφMМмBbБб○◯●]+\s*', '', line)
                if len(line) > 3:
                    lines.append(line)

        result = ' '.join(lines)
        result = re.sub(r'\s+', ' ', result).strip()

        return result if result else text

    @staticmethod
    def clean_answer_text(text: str) -> str:
        """Enhanced answer cleaning - removes ALL bubble variations"""
        original = text.strip()

        # Comprehensive bubble patterns
        bubble_patterns = [
            r'^[0oOоО]+\s*',  # Single answer bubbles (round)
            r'^[ФфΦφ]+\s*',
            r'^[○◯●⚫⚪]+\s*',
            r'^[MМм]+\s*',  # Multi-answer bubbles (rectangular)
            r'^[MМм][IiІі]+\s*',
            r'^[БбBb]+\s*',
            r'^[БбBb][IiІі]+\s*',
            r'^[ИиIi]+\s*',
            r'^[ПпPp]+\s*',
            r'^[НнHhNn]+\s*',
            r'^[0oOоОФфΦφ○◯●⚫⚪MМмBbБбИиIiПпPpНнHhNn]+[IiІі]*\s*',
        ]

        cleaned = original
        for pattern in bubble_patterns:
            new_cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            if new_cleaned != cleaned and len(new_cleaned.strip()) > 2:
                cleaned = new_cleaned.strip()
                break

        # Remove remaining artifacts
        if cleaned:
            cleaned = re.sub(r'^[0oOоОФфΦφMМмBbБбИиIi]\s+', '', cleaned)
            cleaned = re.sub(r'^[.,-]+\s*', '', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned if cleaned and len(cleaned) > 2 else original


class ShapeDetector:
    """Detects question type by analyzing selection box shapes"""

    def __init__(self, config: Config):
        self.config = config

    def detect_question_type(self, answers_region_img: np.ndarray) -> Tuple[str, int]:
        """
        Analyze selection boxes to determine question type
        Returns: (type, required_count)
        - 'single' for radio buttons (circles)
        - 'multi' for checkboxes (squares)
        """
        gray = cv2.cvtColor(answers_region_img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        circle_count = 0
        square_count = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if 50 < area < 500:  # Reasonable size for selection boxes
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue

                circularity = 4 * np.pi * area / (perimeter * perimeter)

                if circularity > self.config.CIRCLE_MIN_CIRCULARITY:
                    circle_count += 1
                elif circularity < self.config.SQUARE_MAX_CIRCULARITY:
                    square_count += 1

        # Determine type based on dominant shape
        if circle_count > square_count:
            return 'single', 1
        elif square_count > 0:
            # For multi-answer, we'll determine count from database
            return 'multi', 0  # Will be set later from DB
        else:
            return 'unknown', 1


class AnswerBlockDetector:
    """Detects and locates answer blocks by color"""

    @staticmethod
    def detect_color_blocks(img: np.ndarray, color_name: str) -> List[Dict]:
        """
        Detect colored answer blocks (green/red)
        Returns list of blocks with coordinates
        """
        try:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            if color_name == "green":
                mask = cv2.inRange(hsv, np.array([25, 20, 20]), np.array([95, 255, 255]))
            else:  # red
                mask1 = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([25, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([155, 20, 20]), np.array([180, 255, 255]))
                mask = mask1 + mask2

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            blocks = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 150:
                    x, y, w, h = cv2.boundingRect(contour)
                    if w > 40 and h > 10:
                        blocks.append({'x': x, 'y': y, 'w': w, 'h': h, 'area': area})

            # Sort by vertical position
            blocks.sort(key=lambda b: b['y'])
            return blocks

        except Exception as e:
            print(f"Block detection error: {e}")
            return []


# =====================================================================
# MAIN APPLICATION CLASS
# =====================================================================

class AutoTestCorrector:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Test Corrector - Enhanced v2.0")
        self.root.geometry("1200x850")

        # Initialize configuration and utility modules
        self.config = Config()
        self.ocr_processor = OCRProcessor(self.config)
        self.shape_detector = ShapeDetector(self.config)
        self.block_detector = AnswerBlockDetector()

        # Database
        self.db_file = self.config.DB_FILE
        self.init_database()

        # State management
        self.monitoring = False
        self.question_region = None
        self.answers_region = None
        self.current_question_text = None
        self.current_question_id = None
        self.current_question_type = 'unknown'  # 'single' or 'multi'
        self.required_answers = 1
        self.answer_positions = []  # List of {text, x, y, region, is_correct}
        self.last_screenshot = None
        self.auto_correcting = False  # Flag to prevent loop during correction

        # Statistics
        self.correction_count = 0
        self.total_questions = 0
        self.correct_first_try = 0
        self.session_start_time = None

        # Threading
        self.monitor_thread = None
        self.selection_window = None
        self.setup_step = 0

        # Create GUI
        self.create_gui()

        # Import existing data if available
        self.import_existing_data()
        
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'single',
                required_answers INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Answers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                answer_text TEXT NOT NULL,
                is_correct BOOLEAN,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)
        
        # Correction log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                question_text TEXT,
                wrong_answer TEXT,
                correct_answer TEXT,
                correction_successful BOOLEAN
            )
        """)
        
        conn.commit()
        conn.close()
        
    def create_gui(self):
        """Create main GUI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(title_frame, text="🤖 Auto Test Corrector", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        self.status_indicator = ttk.Label(title_frame, text="● IDLE", 
                                         font=('Arial', 12, 'bold'), foreground="gray")
        self.status_indicator.pack(side=tk.LEFT, padx=(20, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.setup_button = ttk.Button(control_frame, text="⚙️ Setup Regions", 
                                      command=self.start_setup_wizard)
        self.setup_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.start_button = ttk.Button(control_frame, text="🚀 Start Monitoring", 
                                      command=self.start_monitoring, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stop", 
                                     command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="📊 Database Stats", 
                  command=self.show_database_stats).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="📥 Import Data", 
                  command=self.import_data_dialog).pack(side=tk.LEFT, padx=(0, 5))
        
        # Status panel
        status_frame = ttk.LabelFrame(main_frame, text="📊 Current Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        stats_grid = ttk.Frame(status_frame)
        stats_grid.pack(fill=tk.X)
        
        # Left column
        left_stats = ttk.Frame(stats_grid)
        left_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_stats, text="Current Question:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.current_q_label = ttk.Label(left_stats, text="None", font=('Arial', 9))
        self.current_q_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(left_stats, text="Total Questions:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W)
        self.total_q_label = ttk.Label(left_stats, text="0", font=('Arial', 9))
        self.total_q_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        # Right column
        right_stats = ttk.Frame(stats_grid)
        right_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_stats, text="Correct First Try:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.correct_label = ttk.Label(right_stats, text="0", font=('Arial', 9), foreground="green")
        self.correct_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(right_stats, text="Auto-Corrected:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W)
        self.corrected_label = ttk.Label(right_stats, text="0", font=('Arial', 9), foreground="orange")
        self.corrected_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        # Current question display
        question_frame = ttk.LabelFrame(main_frame, text="📝 Current Question", padding="10")
        question_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.question_display = scrolledtext.ScrolledText(question_frame, height=4, 
                                                          font=('Arial', 10), wrap=tk.WORD)
        self.question_display.pack(fill=tk.BOTH, expand=True)
        
        # Activity log
        log_frame = ttk.LabelFrame(main_frame, text="📋 Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_display = scrolledtext.ScrolledText(log_frame, height=8, 
                                                     font=('Courier', 9), wrap=tk.WORD)
        self.log_display.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️ Quick Start", padding="10")
        info_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        instructions = """1. Click '⚙️ Setup Regions' → Select question area → Select answers area
2. Click '🚀 Start Monitoring' → System watches in background
3. Take your test normally → System auto-corrects wrong answers
4. Press 'N' key or wait for screen change to signal next question

Database: Questions imported from qa_data.json (if exists)
OCR: Serbian (latinica) + English support"""
        
        ttk.Label(info_frame, text=instructions, justify=tk.LEFT, 
                 font=('Arial', 8)).pack(anchor=tk.W)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=2)
        
        self.log("System initialized. Import data or setup regions to begin.")
        
    def log(self, message, level="INFO"):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "ERROR":
            prefix = "❌"
            color = "red"
        elif level == "SUCCESS":
            prefix = "✅"
            color = "green"
        elif level == "WARNING":
            prefix = "⚠️"
            color = "orange"
        elif level == "CORRECTION":
            prefix = "🔧"
            color = "blue"
        else:
            prefix = "ℹ️"
            color = "black"
            
        log_message = f"[{timestamp}] {prefix} {message}\n"
        
        self.log_display.insert(tk.END, log_message)
        self.log_display.see(tk.END)
        
    def start_setup_wizard(self):
        """Start region setup wizard"""
        self.log("Starting setup wizard...")
        self.setup_step = 1
        self.take_screenshot_for_setup()
        
    def take_screenshot_for_setup(self):
        """Take screenshot and open selection"""
        try:
            screenshot = pyautogui.screenshot()
            self.current_screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            if self.setup_step == 1:
                title = "STEP 1: Select Question Region"
                instruction = "Drag around the QUESTION area"
            else:
                title = "STEP 2: Select Answers Region"
                instruction = "Drag around ALL ANSWERS area"
                
            self.open_selection_window(screenshot, title, instruction)
            
        except Exception as e:
            self.log(f"Screenshot failed: {e}", "ERROR")

    def open_selection_window(self, screenshot_pil, title, instruction):
        """Open fullscreen selection window"""
        if self.selection_window:
            self.selection_window.destroy()
            
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.title(title)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.configure(bg='black')
        
        screen_width = self.selection_window.winfo_screenwidth()
        screen_height = self.selection_window.winfo_screenheight()
        
        screenshot_resized = screenshot_pil.resize((screen_width, screen_height), 
                                                   Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(screenshot_resized)
        
        canvas = tk.Canvas(self.selection_window, width=screen_width, 
                          height=screen_height, bg='black', highlightthickness=0)
        canvas.pack()
        
        canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)
        
        # Instructions
        canvas.create_text(screen_width//2, 30, text=title, 
                          fill='yellow', font=('Arial', 20, 'bold'))
        canvas.create_text(screen_width//2, 70, text=instruction, 
                          fill='white', font=('Arial', 14))
        canvas.create_text(screen_width//2, 100, text="Drag & Release | ESC = Cancel", 
                          fill='lightgray', font=('Arial', 10))
        
        self.setup_selection_events(canvas, screen_width, screen_height)
    
    #MARK: Monitoring data
    def setup_selection_events(self, canvas, screen_width, screen_height):
        """Setup mouse events for region selection"""
        self.selection_start = None
        self.selection_rect = None
        
        def on_mouse_down(event):
            self.selection_start = (event.x, event.y)
            if self.selection_rect:
                canvas.delete(self.selection_rect)
                
        def on_mouse_drag(event):
            if self.selection_start:
                if self.selection_rect:
                    canvas.delete(self.selection_rect)
                    
                x1, y1 = self.selection_start
                x2, y2 = event.x, event.y
                
                self.selection_rect = canvas.create_rectangle(
                    x1, y1, x2, y2, outline='yellow', width=3
                )
                
        def on_mouse_up(event):
            if self.selection_start:
                x1, y1 = self.selection_start
                x2, y2 = event.x, event.y
                
                left = min(x1, x2)
                top = min(y1, y2)
                right = max(x1, x2)
                bottom = max(y1, y2)
                
                # Scale coordinates
                orig_width = self.current_screenshot.shape[1]
                orig_height = self.current_screenshot.shape[0]
                scale_x = orig_width / screen_width
                scale_y = orig_height / screen_height
                
                coords = (
                    int(left * scale_x), int(top * scale_y),
                    int(right * scale_x), int(bottom * scale_y)
                )
                
                self.save_selected_region(coords)
                
        def on_escape(event):
            self.selection_window.destroy()
            self.selection_window = None
            self.log("Setup cancelled", "WARNING")
            
        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_drag)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        canvas.bind('<Escape>', on_escape)
        self.selection_window.focus_set()
        
    def save_selected_region(self, coords):
        """Save selected region coordinates"""
        if self.setup_step == 1:
            self.question_region = coords
            self.log(f"Question region saved: {coords}", "SUCCESS")
            self.selection_window.destroy()
            self.selection_window = None
            self.setup_step = 2
            self.take_screenshot_for_setup()
        else:
            self.answers_region = coords
            self.log(f"Answers region saved: {coords}", "SUCCESS")
            self.selection_window.destroy()
            self.selection_window = None
            self.start_button.config(state=tk.NORMAL)
            messagebox.showinfo("Setup Complete", 
                              "Regions configured! Click 'Start Monitoring' to begin.")
            
    def start_monitoring(self):
        """Start background monitoring"""
        if not self.question_region or not self.answers_region:
            messagebox.showerror("Setup Required", "Please setup regions first!")
            return
            
        self.monitoring = True
        self.status_indicator.config(text="● MONITORING", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.setup_button.config(state=tk.DISABLED)
        
        self.log("Monitoring started! Take your test normally.", "SUCCESS")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.status_indicator.config(text="● STOPPED", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.setup_button.config(state=tk.NORMAL)
        
        self.log("Monitoring stopped.", "WARNING")
        
    def monitor_loop(self):
        """Main monitoring loop (runs in background thread)"""
        last_question_hash = None
        
        while self.monitoring:
            try:
                # Capture current question
                screenshot = pyautogui.screenshot()
                screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                x1, y1, x2, y2 = self.question_region
                question_img = screenshot_cv[y1:y2, x1:x2]
                
                # Hash to detect changes
                current_hash = hash(question_img.tobytes())
                
                if current_hash != last_question_hash:
                    self.log("New question detected, processing...")

                    # Extract and match question
                    raw_question_text = self.ocr_text(question_img)

                    if raw_question_text:
                        # Clean question text using OCR processor
                        self.current_question_text = OCRProcessor.clean_question_text(raw_question_text)
                        matched_id = self.match_question(self.current_question_text)
                        
                        if matched_id:
                            self.current_question_id = matched_id
                            self.total_questions += 1
                            self.update_stats()

                            self.root.after(0, self.question_display.delete, 1.0, tk.END)
                            self.root.after(0, self.question_display.insert, 1.0, self.current_question_text)
                            
                            self.log(f"Question matched (ID: {matched_id})", "SUCCESS")
                            
                            # Scan answer positions
                            self.scan_answer_positions(screenshot_cv)
                            
                            # Wait for user click
                            self.wait_for_user_answer(screenshot_cv)
                        else:
                            self.log("Question not in database!", "WARNING")
                    
                    last_question_hash = current_hash
                    
                time.sleep(0.5)
                
            except Exception as e:
                self.log(f"Monitor error: {e}", "ERROR")
                time.sleep(1)
                
    def ocr_text(self, img):
        """Extract text from image using enhanced OCR processor"""
        text, confidence = self.ocr_processor.extract_text(img)
        return text
            
    def match_question(self, question_text):
        """Match question against database using fuzzy matching"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, question_text FROM questions")
        questions = cursor.fetchall()
        conn.close()
        
        best_match = None
        best_score = 0
        
        for qid, db_question in questions:
            score = fuzz.ratio(question_text.lower(), db_question.lower())
            if score > best_score:
                best_score = score
                best_match = qid
                
        if best_score >= 85:  # 85% similarity threshold
            return best_match
        return None
        
    def scan_answer_positions(self, screenshot_cv):
        """Scan and store answer block positions with enhanced detection"""
        x1, y1, x2, y2 = self.answers_region
        answers_img = screenshot_cv[y1:y2, x1:x2]

        # Detect question type by box shape
        detected_type, _ = self.shape_detector.detect_question_type(answers_img)
        if detected_type != 'unknown':
            self.current_question_type = detected_type
            self.log(f"Question type detected: {detected_type.upper()}")

        # Detect green and red blocks using enhanced detector
        green_blocks = self.block_detector.detect_color_blocks(answers_img, "green")
        red_blocks = self.block_detector.detect_color_blocks(answers_img, "red")

        self.answer_positions = []

        # Process correct answers (green blocks)
        for block in green_blocks:
            bx, by, bw, bh = block['x'], block['y'], block['w'], block['h']
            answer_region = answers_img[by:by+bh, bx:bx+bw]
            answer_text = self.ocr_text(answer_region)

            if answer_text:
                # Clean the answer text
                clean_text = OCRProcessor.clean_answer_text(answer_text)

                # Store absolute screen coordinates
                abs_x = x1 + bx + bw//2
                abs_y = y1 + by + bh//2

                self.answer_positions.append({
                    'text': clean_text,
                    'raw_text': answer_text,
                    'x': abs_x,
                    'y': abs_y,
                    'region': (bx, by, bw, bh),
                    'is_correct': True
                })

        # Process wrong answers (red blocks)
        for block in red_blocks:
            bx, by, bw, bh = block['x'], block['y'], block['w'], block['h']
            answer_region = answers_img[by:by+bh, bx:bx+bw]
            answer_text = self.ocr_text(answer_region)

            if answer_text:
                # Clean the answer text
                clean_text = OCRProcessor.clean_answer_text(answer_text)

                # Store absolute screen coordinates
                abs_x = x1 + bx + bw//2
                abs_y = y1 + by + bh//2

                self.answer_positions.append({
                    'text': clean_text,
                    'raw_text': answer_text,
                    'x': abs_x,
                    'y': abs_y,
                    'region': (bx, by, bw, bh),
                    'is_correct': False
                })

        correct_count = sum(1 for a in self.answer_positions if a['is_correct'])
        wrong_count = len(self.answer_positions) - correct_count

        self.log(f"Found {len(self.answer_positions)} answers (✅{correct_count} ❌{wrong_count})")
            
    def wait_for_user_answer(self, screenshot_before):
        """Wait for user to click an answer and validate"""
        x1, y1, x2, y2 = self.answers_region
        
        # Wait for screen change in answers region
        attempts = 0
        max_attempts = 200  # 20 seconds max wait
        
        while self.monitoring and attempts < max_attempts:
            time.sleep(0.1)
            attempts += 1
            
            try:
                current_screenshot = pyautogui.screenshot()
                current_cv = cv2.cvtColor(np.array(current_screenshot), cv2.COLOR_RGB2BGR)
                
                before_region = screenshot_before[y1:y2, x1:x2]
                current_region = current_cv[y1:y2, x1:x2]
                
                # Check if significant change occurred
                diff = cv2.absdiff(before_region, current_region)
                change = np.sum(diff) / diff.size
                
                if change > 5:  # Threshold for change detection
                    self.log("Answer click detected!")
                    
                    # Small delay for UI to settle
                    time.sleep(0.3)
                    
                    # Capture final state
                    final_screenshot = pyautogui.screenshot()
                    final_cv = cv2.cvtColor(np.array(final_screenshot), cv2.COLOR_RGB2BGR)
                    
                    # Validate answer
                    self.validate_and_correct(final_cv)
                    break
                    
            except:
                pass


    #ovo nekako radi ne diraj
    #MARK: Validation_C
    def validate_and_correct(self, screenshot_cv):
        """
        Enhanced validation and auto-correction system
        - Detects what user clicked
        - Validates against database
        - Only corrects if wrong
        - Handles both single and multi-answer questions
        """
        if not self.current_question_id or self.auto_correcting:
            return

        # Get correct and wrong answers from database
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT answer_text FROM answers
            WHERE question_id = ? AND is_correct = 1
        """, (self.current_question_id,))
        db_correct_answers = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT answer_text FROM answers
            WHERE question_id = ? AND is_correct = 0
        """, (self.current_question_id,))
        db_wrong_answers = [row[0] for row in cursor.fetchall()]

        # Get question type from database
        cursor.execute("""
            SELECT question_type, required_answers FROM questions
            WHERE id = ?
        """, (self.current_question_id,))
        result = cursor.fetchone()
        if result:
            db_question_type, db_required = result
            if db_question_type:
                self.current_question_type = db_question_type
            if db_required:
                self.required_answers = db_required

        conn.close()

        # Detect which answers are currently selected
        x1, y1, x2, y2 = self.answers_region
        answers_img = screenshot_cv[y1:y2, x1:x2]

        selected_answers = []

        # Check each answer position for selection indicators
        for ans_pos in self.answer_positions:
            bx, by, bw, bh = ans_pos['region']
            block_img = answers_img[by:by+bh, bx:bx+bw]

            if self.is_answer_selected(block_img):
                selected_answers.append(ans_pos)

        if not selected_answers:
            self.log("No selected answers detected", "WARNING")
            return

        # Validate selections
        is_correct_selection = self._validate_answer_selection(
            selected_answers,
            db_correct_answers,
            db_wrong_answers
        )

        if is_correct_selection:
            # User selected correctly
            selected_texts = [a['text'] for a in selected_answers]
            self.log(f"✅ Correct! Selected: {', '.join(selected_texts)}", "SUCCESS")
            self.correct_first_try += 1
            self.update_stats()
        else:
            # User selected wrong - perform auto-correction
            self._perform_auto_correction(
                selected_answers,
                db_correct_answers
            )

    def _validate_answer_selection(self, selected_answers, db_correct_answers, db_wrong_answers):
        """
        Validate if user's selection is correct
        Returns True if correct, False if wrong
        """
        selected_texts = [ans['text'] for ans in selected_answers]

        # For single answer questions
        if self.current_question_type == 'single':
            if len(selected_texts) != 1:
                return False

            # Check if the selected answer fuzzy-matches a correct answer
            for correct in db_correct_answers:
                if fuzz.ratio(selected_texts[0].lower(), correct.lower()) >= self.config.FUZZY_THRESHOLD:
                    return True
            return False

        # For multi-answer questions
        elif self.current_question_type == 'multi':
            # Check if all selected answers are correct
            matched_correct = 0
            for selected in selected_texts:
                for correct in db_correct_answers:
                    if fuzz.ratio(selected.lower(), correct.lower()) >= self.config.FUZZY_THRESHOLD:
                        matched_correct += 1
                        break

            # All selected must be correct AND count must match required
            return matched_correct == len(selected_texts) == self.required_answers

        return False

    #da se debaguje TODO:31 MARK:31
    def _perform_auto_correction(self, wrong_selections, db_correct_answers):
        """
        Auto-click the correct answers
        """
        self.auto_correcting = True  # Prevent re-triggering

        try:
            wrong_texts = [a['text'] for a in wrong_selections]
            self.log(f"❌ Wrong selection: {', '.join(wrong_texts)}", "ERROR")

            # Find correct answer positions by fuzzy matching
            correct_positions = []
            for db_correct in db_correct_answers:
                best_match = None
                best_score = 0

                for ans_pos in self.answer_positions:
                    score = fuzz.ratio(ans_pos['text'].lower(), db_correct.lower())
                    if score > best_score:
                        best_score = score
                        best_match = ans_pos

                if best_match and best_score >= self.config.FUZZY_THRESHOLD:
                    correct_positions.append(best_match)

            if not correct_positions:
                self.log("Could not locate correct answers on screen!", "ERROR")
                self.auto_correcting = False
                return

            # For single-answer: Unclick wrong, click correct
            if self.current_question_type == 'single':
                # Unclick wrong answer (if it's a radio, clicking correct will auto-unclick)
                # Just click the correct one
                correct = correct_positions[0]
                self.log(f"🔧 Auto-correcting to: {correct['text']}", "CORRECTION")     #da se promeni ovaj printf (ikonice su sranje/unsupported)

                time.sleep(self.config.CORRECTION_DELAY)
                pyautogui.click(correct['x'], correct['y'])
                time.sleep(self.config.CORRECTION_DELAY)

                self.correction_count += 1
                self.update_stats()
                self.log_correction(', '.join(wrong_texts), correct['text'], True)
                self.log("✅ Correction successful!", "SUCCESS")

            # For multi-answer: Unclick wrong ones, click correct ones
            elif self.current_question_type == 'multi':
                # Unclick wrong selections
                for wrong in wrong_selections:
                    pyautogui.click(wrong['x'], wrong['y'])
                    time.sleep(self.config.CORRECTION_DELAY)

                # Click correct answers
                correct_texts = []
                for correct in correct_positions:
                    pyautogui.click(correct['x'], correct['y'])
                    time.sleep(self.config.CORRECTION_DELAY)
                    correct_texts.append(correct['text'])

                self.correction_count += 1
                self.update_stats()
                self.log_correction(', '.join(wrong_texts), ', '.join(correct_texts), True)
                self.log(f"✅ Corrected to: {', '.join(correct_texts)}", "SUCCESS")

        except Exception as e:
            self.log(f"Correction error: {e}", "ERROR")

        finally:
            self.auto_correcting = False
                
    def is_answer_selected(self, block_img):
        """Check if answer block appears selected"""
        # Simple heuristic: selected answers often have darker/different color
        # You may need to adjust this based on your test UI
        try:
            hsv = cv2.cvtColor(block_img, cv2.COLOR_BGR2HSV)
            
            # Check for blue/dark selection indicators
            mask_blue = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
            mask_dark = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 100]))
            
            blue_ratio = np.sum(mask_blue > 0) / mask_blue.size
            dark_ratio = np.sum(mask_dark > 0) / mask_dark.size
            
            return blue_ratio > 0.1 or dark_ratio > 0.3
        except:
            return False
            
    def log_correction(self, wrong, correct, success):
        """Log correction to database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO correction_log (question_text, wrong_answer, correct_answer, correction_successful)
            VALUES (?, ?, ?, ?)
        """, (self.current_question_text, wrong, correct, success))

        conn.commit()
        conn.close()
    
    #this is problematic, fix latter TODO:11 MARK: 11
    def update_stats(self):
        """Update statistics display"""
        self.root.after(0, self.total_q_label.config, {'text': str(self.total_questions)})
        self.root.after(0, self.correct_label.config, {'text': str(self.correct_first_try)})
        self.root.after(0, self.corrected_label.config, {'text': str(self.correction_count)})
        
        if self.total_questions > 0:
            success_rate = (self.correct_first_try / self.total_questions) * 100
            self.root.after(0, self.current_q_label.config, 
                          {'text': f"Q{self.total_questions} ({success_rate:.1f}% accuracy)"})
        
    #MARK: Import data
    def import_existing_data(self):
        """Import data from existing qa_data.json if it exists"""
        json_file = "qa_data.json"
        
        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                if "questions" in data:
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    
                    imported = 0
                    
                    for q in data["questions"]:
                        # Check if question already exists
                        question_text = q.get("question", "")
                        if not question_text:
                            continue
                            
                        cursor.execute("SELECT id FROM questions WHERE question_text = ?", 
                                     (question_text,))
                        existing = cursor.fetchone()
                        
                        if not existing:
                            # Insert question
                            qtype = q.get("question_type", "single")
                            required = q.get("required_correct_answers", 1)
                            
                            cursor.execute("""
                                INSERT INTO questions (question_text, question_type, required_answers)
                                VALUES (?, ?, ?)
                            """, (question_text, qtype, required))
                            
                            question_id = cursor.lastrowid
                            
                            # Insert correct answers
                            for ans in q.get("correct_answers", []):
                                cursor.execute("""
                                    INSERT INTO answers (question_id, answer_text, is_correct)
                                    VALUES (?, ?, 1)
                                """, (question_id, ans))
                                
                            # Insert wrong answers
                            for ans in q.get("wrong_answers", []):
                                cursor.execute("""
                                    INSERT INTO answers (question_id, answer_text, is_correct)
                                    VALUES (?, ?, 0)
                                """, (question_id, ans))
                                
                            imported += 1
                            
                    conn.commit()
                    conn.close()
                    
                    if imported > 0:
                        self.log(f"Imported {imported} questions from qa_data.json", "SUCCESS")
                    else:
                        self.log("All questions already in database", "INFO")
                        
            except Exception as e:
                self.log(f"Error importing data: {e}", "ERROR")
    
    #rewieve with DB TODO:21 MARK: 21
    def import_data_dialog(self):
        """Manual data import dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Q&A Data")
        dialog.geometry("600x400")
        
        ttk.Label(dialog, text="Paste JSON data or select file:", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(dialog, height=15, width=70)
        text_area.pack(padx=10, pady=10)
        
        def import_from_text():
            try:
                json_text = text_area.get(1.0, tk.END).strip()
                data = json.loads(json_text)
                
                if "questions" in data:
                    conn = sqlite3.connect(self.db_file)
                    cursor = conn.cursor()
                    
                    imported = 0
                    
                    for q in data["questions"]:
                        question_text = q.get("question", "")
                        if not question_text:
                            continue
                            
                        cursor.execute("SELECT id FROM questions WHERE question_text = ?", 
                                     (question_text,))
                        if not cursor.fetchone():
                            qtype = q.get("question_type", "single")
                            required = q.get("required_correct_answers", 1)
                            
                            cursor.execute("""
                                INSERT INTO questions (question_text, question_type, required_answers)
                                VALUES (?, ?, ?)
                            """, (question_text, qtype, required))
                            
                            question_id = cursor.lastrowid
                            
                            for ans in q.get("correct_answers", []):
                                cursor.execute("""
                                    INSERT INTO answers (question_id, answer_text, is_correct)
                                    VALUES (?, ?, 1)
                                """, (question_id, ans))
                                
                            for ans in q.get("wrong_answers", []):
                                cursor.execute("""
                                    INSERT INTO answers (question_id, answer_text, is_correct)
                                    VALUES (?, ?, 0)
                                """, (question_id, ans))
                                
                            imported += 1
                            
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("Success", f"Imported {imported} new questions!")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Invalid JSON format!")
                    
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON!")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")
                
        ttk.Button(dialog, text="Import", command=import_from_text).pack(pady=5)
        
    #test with real DB
    def show_database_stats(self):
        """Show database statistics"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM questions")
        total_questions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM answers WHERE is_correct = 1")
        total_correct = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM answers WHERE is_correct = 0")
        total_wrong = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM correction_log")
        total_corrections = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM correction_log 
            WHERE correction_successful = 1
        """)
        successful_corrections = cursor.fetchone()[0]
        
        conn.close()
        
        stats_text = f"""📊 DATABASE STATISTICS

Total Questions: {total_questions}
Total Correct Answers: {total_correct}
Total Wrong Answers: {total_wrong}

All-Time Corrections: {total_corrections}
Successful Corrections: {successful_corrections}
"""
        
        messagebox.showinfo("Database Stats", stats_text)


def main():
    root = tk.Tk()
    app = AutoTestCorrector(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()