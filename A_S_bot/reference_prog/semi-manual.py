"""
ULTIMATE AUTOMATED Q&A EXTRACTOR
Continuous loop with auto-save and enhanced bubble cleaning

Features:
- Enhanced bubble character removal
- Auto-saves after answers selection (no ENTER needed)
- Continuous loop: SPACE → question → answers → auto-save → repeat
- Stop button to end continuous session
- Success notifications without interrupting flow
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageTk, ImageEnhance
import pyautogui
import json
import os
from datetime import datetime
import threading
import keyboard
import time
import re

class UltimateAutomatedQAExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Automated Q&A Extractor")
        self.root.geometry("1100x870")

        # Configuration
        self.tesseract_path = r"C:\dt\Tesseract-OCR\tesseract.exe"
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

        # Data storage
        self.json_file = "qa_data.json"
        self.current_screenshot = None
        self.selection_window = None
        self.is_active = False
        self.question_counter = 1
        self.processing = False
        self.continuous_mode = False  # For continuous processing

        # Redo functionality
        self.redo_mode = None

        # Current Q&A session data
        self.current_question = ""
        self.correct_answers = []
        self.wrong_answers = []
        self.question_type = "unknown"
        self.required_correct_answers = 0
        self.phase = "idle"

        # Create GUI
        self.create_gui()

        # Setup keyboard listener
        self.setup_keyboard_listener()

    def create_gui(self):
        """Create GUI with continuous mode controls"""

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Control buttons with continuous mode
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Main controls
        main_controls = ttk.Frame(control_frame)
        main_controls.pack(fill=tk.X, pady=(0, 5))

        self.start_button = ttk.Button(main_controls, text="🚀 Start Continuous Mode", command=self.start_continuous_mode, 
                                     style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(main_controls, text="🛑 Stop", command=self.stop_continuous_mode, 
                                    state=tk.DISABLED, style="")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        # Status indicator for continuous mode
        self.mode_label = ttk.Label(main_controls, text="", font=('Arial', 10, 'bold'), foreground="green")
        self.mode_label.pack(side=tk.LEFT, padx=(20, 0))

        # Redo controls
        redo_controls = ttk.Frame(control_frame)
        redo_controls.pack(fill=tk.X)

        ttk.Label(redo_controls, text="Fix Mistakes:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))

        self.redo_question_button = ttk.Button(redo_controls, text="🔄 Re-read Question", 
                                             command=self.redo_question_selection, state=tk.DISABLED)
        self.redo_question_button.pack(side=tk.LEFT, padx=(0, 5))

        self.redo_answers_button = ttk.Button(redo_controls, text="🔄 Re-read Answers", 
                                            command=self.redo_answers_selection, state=tk.DISABLED)
        self.redo_answers_button.pack(side=tk.LEFT, padx=(0, 5))

        # Status with spinning circle
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        top_status_frame = ttk.Frame(status_frame)
        top_status_frame.pack(fill=tk.X)

        self.phase_label = ttk.Label(top_status_frame, text="Ready", font=('Arial', 14, 'bold'), foreground="blue")
        self.phase_label.pack(side=tk.LEFT)

        self.status_label = ttk.Label(top_status_frame, text="Click 'Start Continuous Mode' to begin", font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))

        # Loading with spinner
        loading_frame = ttk.Frame(status_frame)
        loading_frame.pack(fill=tk.X, pady=(5, 0))

        self.loading_label = ttk.Label(loading_frame, text="", font=('Arial', 9), foreground="orange")
        self.loading_label.pack(side=tk.LEFT)

        self.spinner = ttk.Progressbar(loading_frame, mode='indeterminate', length=120)
        self.spinner.pack(side=tk.LEFT, padx=(10, 0))

        self.speed_label = ttk.Label(loading_frame, text="", font=('Arial', 9), foreground="green")
        self.speed_label.pack(side=tk.LEFT, padx=(10, 0))

        # Success indicator for continuous mode
        self.success_label = ttk.Label(loading_frame, text="", font=('Arial', 10, 'bold'), foreground="green")
        self.success_label.pack(side=tk.LEFT, padx=(20, 0))

        # Question type and results
        type_frame = ttk.LabelFrame(main_frame, text="Detection Results", padding="5")
        type_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        type_info_frame = ttk.Frame(type_frame)
        type_info_frame.pack(fill=tk.X)

        ttk.Label(type_info_frame, text="Type:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.type_label = ttk.Label(type_info_frame, text="Not detected", font=('Arial', 10), foreground="gray")
        self.type_label.pack(side=tk.LEFT, padx=(5, 15))

        self.required_label = ttk.Label(type_info_frame, text="", font=('Arial', 9), foreground="blue")
        self.required_label.pack(side=tk.LEFT, padx=(0, 15))

        # Question counter for continuous mode
        self.counter_label = ttk.Label(type_info_frame, text="", font=('Arial', 10, 'bold'), foreground="purple")
        self.counter_label.pack(side=tk.LEFT, padx=(20, 15))

        # Results counts
        ttk.Label(type_info_frame, text="Found:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.green_count_label = ttk.Label(type_info_frame, text="", font=('Arial', 9), foreground="green")
        self.green_count_label.pack(side=tk.LEFT, padx=(5, 10))

        self.red_count_label = ttk.Label(type_info_frame, text="", font=('Arial', 9), foreground="red")
        self.red_count_label.pack(side=tk.LEFT, padx=(0, 10))

        self.total_count_label = ttk.Label(type_info_frame, text="", font=('Arial', 9), foreground="purple")
        self.total_count_label.pack(side=tk.LEFT)

        # Q&A preview
        qa_frame = ttk.LabelFrame(main_frame, text="Current Q&A", padding="5")
        qa_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Question
        question_frame = ttk.Frame(qa_frame)
        question_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(question_frame, text="📝 Question:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.question_text = scrolledtext.ScrolledText(question_frame, height=3, width=95, font=('Arial', 10))
        self.question_text.pack(fill=tk.X)

        # Answers
        answers_frame = ttk.Frame(qa_frame)
        answers_frame.pack(fill=tk.BOTH, expand=True)

        # Correct answers
        correct_frame = ttk.Frame(answers_frame)
        correct_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        ttk.Label(correct_frame, text="✅ Correct:", font=('Arial', 10, 'bold'), foreground="green").pack(anchor=tk.W)
        self.correct_answers_list = scrolledtext.ScrolledText(correct_frame, height=3, width=95, font=('Arial', 9))
        self.correct_answers_list.pack(fill=tk.BOTH, expand=True)

        # Wrong answers
        wrong_frame = ttk.Frame(answers_frame)
        wrong_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(wrong_frame, text="❌ Wrong:", font=('Arial', 10, 'bold'), foreground="red").pack(anchor=tk.W)
        self.wrong_answers_list = scrolledtext.ScrolledText(wrong_frame, height=3, width=95, font=('Arial', 9))
        self.wrong_answers_list.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions_frame = ttk.LabelFrame(main_frame, text="🚀 Automated Continuous Mode", padding="5")
        instructions_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        instructions_text = """🚀 AUTOMATED CONTINUOUS WORKFLOW:
1. Click '🚀 Start Continuous Mode'
2. Press SPACE → Select question → Select answers → AUTO-SAVES! 
3. Press SPACE → Select next question → Select answers → AUTO-SAVES!
4. Repeat in loop until you click '🛑 Stop'

FEATURES:
• No ENTER needed - auto-saves after answers selection
• Success notification appears briefly
• Counter shows questions processed  
• Enhanced bubble cleaning (all types removed)
• Redo buttons work anytime for corrections
• SPACE starts next question immediately

ENHANCED BUBBLE CLEANING:
Removes: 0, o, O, M, MI, Bi, и, БИ, М, Ф, ф, ○, ◯, etc.

Perfect for processing many questions quickly!
Hotkeys: SPACE = Next question, ESC = Cancel current, 🛑 Stop = End session"""

        ttk.Label(instructions_frame, text=instructions_text, justify=tk.LEFT, font=('Arial', 8)).pack(anchor=tk.W)

        # Compact data display
        data_frame = ttk.LabelFrame(main_frame, text="Recent Q&A Data (Auto-updating)", padding="5")
        data_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        self.data_display = scrolledtext.ScrolledText(data_frame, height=4, width=95, font=('Arial', 8))
        self.data_display.pack(fill=tk.BOTH, expand=True)

        # Load existing data
        self.load_existing_data_robust()

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def start_spinner(self, message):
        """Start spinner"""
        try:
            self.processing = True
            self.loading_label.config(text=message)
            self.spinner.start(8)
            self.root.update_idletasks()
        except:
            pass

    def stop_spinner(self, speed_message=""):
        """Stop spinner"""
        try:
            self.processing = False
            self.loading_label.config(text="")
            self.spinner.stop()
            if speed_message:
                self.speed_label.config(text=speed_message)
                self.root.after(3000, lambda: self.safe_clear_speed())
            self.root.update_idletasks()
        except:
            pass

    def safe_clear_speed(self):
        """Clear speed label"""
        try:
            self.speed_label.config(text="")
        except:
            pass

    def show_success(self, message):
        """Show success message briefly"""
        try:
            self.success_label.config(text=message)
            self.root.after(2500, lambda: self.success_label.config(text=""))
        except:
            pass

    def setup_keyboard_listener(self):
        """Setup keyboard listener for continuous mode"""
        def on_space_press():
            if self.continuous_mode:
                if self.phase == "idle" or self.phase == "question":
                    self.start_new_question_in_continuous()

        def on_escape_press():
            if self.selection_window:
                self.selection_window.destroy()
                self.selection_window = None
                self.redo_mode = None
            elif self.continuous_mode:
                # ESC cancels current but stays in continuous mode
                self.reset_current_question()

        try:
            keyboard.add_hotkey('space', on_space_press)
            keyboard.add_hotkey('esc', on_escape_press)
        except Exception as e:
            print(f"Hotkey setup error: {e}")

    def start_continuous_mode(self):
        """Start continuous processing mode"""
        self.continuous_mode = True
        self.is_active = True

        # Update UI for continuous mode
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.redo_question_button.config(state=tk.NORMAL)
        self.redo_answers_button.config(state=tk.NORMAL)

        self.mode_label.config(text="🔄 CONTINUOUS MODE")
        self.phase_label.config(text="READY FOR QUESTIONS", foreground="green")
        self.update_status("Press SPACE to start first question")
        self.counter_label.config(text=f"Session: 0 questions")

    def stop_continuous_mode(self):
        """Stop continuous processing mode"""
        self.continuous_mode = False
        self.is_active = False
        self.phase = "idle"
        self.redo_mode = None
        self.processing = False

        self.stop_spinner()

        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.redo_question_button.config(state=tk.DISABLED)
        self.redo_answers_button.config(state=tk.DISABLED)

        self.mode_label.config(text="")
        self.phase_label.config(text="Ready", foreground="blue")
        self.update_status("Continuous mode stopped. Click 'Start Continuous Mode' to begin.")

        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None

    def start_new_question_in_continuous(self):
        """Start new question in continuous mode"""
        # Reset current Q&A data
        self.reset_current_question()

        # Set to question phase
        self.phase = "question"
        self.redo_mode = None

        self.phase_label.config(text="STEP 1: SELECT QUESTION", foreground="red")
        self.update_status("Select QUESTION region...")

        # Take screenshot and open selection
        self.take_screenshot_and_select()

    def reset_current_question(self):
        """Reset current question data"""
        self.current_question = ""
        self.correct_answers = []
        self.wrong_answers = []
        self.question_type = "unknown"
        self.required_correct_answers = 0

        # Clear displays
        self.question_text.delete(1.0, tk.END)
        self.correct_answers_list.delete(1.0, tk.END)
        self.wrong_answers_list.delete(1.0, tk.END)
        self.type_label.config(text="Not detected", foreground="gray")
        self.required_label.config(text="")
        self.green_count_label.config(text="")
        self.red_count_label.config(text="")
        self.total_count_label.config(text="")

    def update_status(self, message):
        """Safe status update"""
        try:
            self.status_label.config(text=message)
            self.root.update_idletasks()
        except:
            pass

    def redo_question_selection(self):
        """Re-select and re-read question"""
        if self.continuous_mode:
            self.redo_mode = "question"
            self.update_status("REDO: Select question region to re-read...")
            self.take_screenshot_and_select()
        else:
            messagebox.showwarning("Not Active", "Please start continuous mode first.")

    def redo_answers_selection(self):
        """Re-select and re-read answers"""
        if self.continuous_mode:
            self.redo_mode = "answers"
            self.update_status("REDO: Select answers region to re-read...")
            self.take_screenshot_and_select()
        else:
            messagebox.showwarning("Not Active", "Please start continuous mode first.")

    def take_screenshot_and_select(self):
        """Fast screenshot"""
        try:
            screenshot = pyautogui.screenshot()
            self.current_screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            self.open_selection_window(screenshot)
        except Exception as e:
            messagebox.showerror("Error", f"Screenshot failed: {e}")

    def auto_open_answers_selection(self):
        """Auto-open answers selection"""
        if not self.redo_mode and self.continuous_mode:
            try:
                screenshot = pyautogui.screenshot()
                self.current_screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                self.open_selection_window(screenshot)
            except Exception as e:
                self.update_status(f"Error: {e}")

    def open_selection_window(self, screenshot_pil):
        """Open selection window with proper mode handling"""
        if self.selection_window:
            self.selection_window.destroy()

        self.selection_window = tk.Toplevel(self.root)

        # Determine selection mode
        if self.redo_mode == "question":
            title = "REDO: Select Question"
            current_mode = "question"
        elif self.redo_mode == "answers":
            title = "REDO: Select Answers"  
            current_mode = "answers"
        elif self.phase == "question":
            title = "Step 1: Select Question"
            current_mode = "question"
        else:
            title = "Step 2: Select Answers"
            current_mode = "answers"

        self.selection_window.title(title)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.configure(bg='black')

        screen_width = self.selection_window.winfo_screenwidth()
        screen_height = self.selection_window.winfo_screenheight()

        screenshot_resized = screenshot_pil.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(screenshot_resized)

        canvas = tk.Canvas(self.selection_window, width=screen_width, height=screen_height, bg='black')
        canvas.pack()

        canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)

        # Instructions
        if current_mode == "question":
            if self.redo_mode:
                instruction = "REDO: Drag around QUESTION"
                subtitle = "Will re-process question only"
            else:
                instruction = "STEP 1: Drag around QUESTION"
                subtitle = "Auto-advances to answers after processing"
            color = 'red'
        else:
            if self.redo_mode:
                instruction = "REDO: Drag around ANSWERS"
                subtitle = "Will re-process answers only"
            else:
                instruction = "STEP 2: Drag around ANSWERS"
                subtitle = "AUTO-SAVES after processing!"
            color = 'green'

        canvas.create_text(screen_width//2, 30, text=instruction, fill=color, font=('Arial', 18, 'bold'))
        canvas.create_text(screen_width//2, 60, text=subtitle, fill='yellow', font=('Arial', 12))
        canvas.create_text(screen_width//2, 85, text="Drag & Release | ESC = Cancel", fill='white', font=('Arial', 10))

        self.setup_selection_events(canvas, screen_width, screen_height, current_mode)

    def setup_selection_events(self, canvas, screen_width, screen_height, current_mode):
        """Setup selection events"""
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

                color = 'red' if current_mode == "question" else 'green'
                self.selection_rect = canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)

        def on_mouse_up(event):
            """Process based on current mode"""
            if self.selection_start:
                x1, y1 = self.selection_start
                x2, y2 = event.x, event.y

                left = min(x1, x2)
                top = min(y1, y2)
                right = max(x1, x2)
                bottom = max(y1, y2)

                # Scale coordinates
                orig_width, orig_height = self.current_screenshot.shape[1], self.current_screenshot.shape[0]
                scale_x = orig_width / screen_width
                scale_y = orig_height / screen_height

                self.selection_coords = (
                    int(left * scale_x), int(top * scale_y),
                    int(right * scale_x), int(bottom * scale_y)
                )

                self.process_selected_region(current_mode)

        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_drag)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        canvas.bind('<Escape>', lambda e: self.cancel_selection())
        self.selection_window.focus_set()

    def cancel_selection(self):
        """Cancel selection"""
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
        self.redo_mode = None

    def process_selected_region(self, current_mode):
        """Process region based on mode"""
        try:
            if self.selection_window:
                self.selection_window.destroy()
                self.selection_window = None

            left, top, right, bottom = self.selection_coords
            selected_region = self.current_screenshot[top:bottom, left:right]

            if selected_region.size == 0:
                return

            # Process based on what was selected
            if current_mode == "question":
                self.process_question_fast(selected_region)
                # Auto-advance to answers (unless redo)
                if not self.redo_mode and self.continuous_mode:
                    self.phase = "answers"
                    self.phase_label.config(text="STEP 2: SELECT ANSWERS", foreground="green")
                    self.root.after(400, self.auto_open_answers_selection)
            else:  # answers
                self.process_answers_fast(selected_region)
                # AUTO-SAVE after answers (unless redo)
                if not self.redo_mode and self.continuous_mode:
                    self.auto_save_and_continue()

            # Clear redo mode
            self.redo_mode = None

        except Exception as e:
            self.stop_spinner()
            self.update_status(f"Error: {e}")
            self.redo_mode = None

    def auto_save_and_continue(self):
        """Automatically save Q&A and prepare for next question"""
        if self.current_question and (self.correct_answers or self.wrong_answers):
            # Auto-save without user intervention
            self.save_qa_set_silent()

    def process_question_fast(self, region_cv):
        """Fast question processing with enhanced bubble cleaning"""
        start_time = time.time()
        self.start_spinner("Processing question...")

        try:
            # Fast OCR
            raw_text, confidence = self.fast_ocr(region_cv)

            # Quick type detection
            self.detect_question_type(raw_text)

            # Enhanced question cleaning
            self.current_question = self.clean_question_enhanced(raw_text)
            self.question_text.delete(1.0, tk.END)
            self.question_text.insert(1.0, self.current_question)

            # Show speed
            speed_time = time.time() - start_time
            self.stop_spinner(f"⚡ {speed_time:.1f}s")

            if self.redo_mode:
                self.update_status(f"Question re-read! Type: {self.question_type.title()}")
            else:
                self.update_status(f"{self.question_type.title()} question ready. Auto-opening answers...")

        except Exception as e:
            self.stop_spinner()
            self.update_status(f"Question error: {e}")

    def process_answers_fast(self, region_cv):
        """Fast answer processing with enhanced cleaning"""
        start_time = time.time()
        self.start_spinner("Processing answers...")

        try:
            # Fast block detection
            green_blocks = self.fast_color_blocks(region_cv, "green")
            red_blocks = self.fast_color_blocks(region_cv, "red")

            total_blocks = len(green_blocks) + len(red_blocks)

            if total_blocks < 3:
                self.stop_spinner()
                messagebox.showwarning("Few Blocks", f"Only {total_blocks} blocks found.")
                return

            # Update counts
            self.green_count_label.config(text=f"✅{len(green_blocks)}")
            self.red_count_label.config(text=f"❌{len(red_blocks)}")
            self.total_count_label.config(text=f"📊{total_blocks}")

            # Enhanced text extraction with better bubble cleaning
            self.correct_answers = []
            for block in green_blocks:
                text, conf = self.fast_text_from_block(region_cv, block)
                if text:
                    clean_text = self.clean_answer_enhanced(text)
                    if clean_text and len(clean_text) > 2:
                        self.correct_answers.append({'text': clean_text, 'confidence': conf})

            self.wrong_answers = []
            for block in red_blocks:
                text, conf = self.fast_text_from_block(region_cv, block)
                if text:
                    clean_text = self.clean_answer_enhanced(text)
                    if clean_text and len(clean_text) > 2:
                        self.wrong_answers.append({'text': clean_text, 'confidence': conf})

            # Show speed
            speed_time = time.time() - start_time
            self.stop_spinner(f"⚡ {speed_time:.1f}s")

            # Update display
            self.update_answers_fast()

            total = len(self.correct_answers) + len(self.wrong_answers)
            if self.redo_mode:
                self.update_status(f"Answers re-read! Found {total} clean answers.")
            else:
                self.update_status(f"Found {total} answers! Auto-saving...")

        except Exception as e:
            self.stop_spinner()
            self.update_status(f"Answers error: {e}")

    def clean_answer_enhanced(self, text):
        """Enhanced answer cleaning - removes ALL bubble variations"""
        try:
            original = text.strip()

            # Comprehensive bubble patterns
            bubble_patterns = [
                # Single answer bubbles (round)
                r'^[0oOоО]+\s*',
                r'^[ФфΦφ]+\s*',
                r'^[○◯●⚫⚪]+\s*',

                # Multi-answer bubbles (rectangular)
                r'^[MМм]+\s*',
                r'^[MМм][IiІі]+\s*',
                r'^[БбBb]+\s*',
                r'^[БбBb][IiІі]+\s*',
                r'^[ИиIi]+\s*',
                r'^[ПпPp]+\s*',
                r'^[НнHhNn]+\s*',

                # Combined patterns
                r'^[0oOоОФфΦφ○◯●⚫⚪MМмBbБбИиIiПпPpНнHhNn]+[IiІі]*\s*',

                # With punctuation
                r'^[\[\(]?[0oOоОФфΦφ○◯●⚫⚪MМмBbБбИиIiПпPpНнHhNn]+[IiІі]*[\]\)]?\s*',

                # Multiple characters (OCR errors)
                r'^[0oOоОФфΦφ○◯●⚫⚪MМмBbБбИиIiПпPpНнHhNn]{2,}\s*',
            ]

            cleaned = original

            # Try each pattern
            for pattern in bubble_patterns:
                new_cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
                if new_cleaned != cleaned and len(new_cleaned.strip()) > 2:
                    cleaned = new_cleaned.strip()
                    break

            # Additional cleanup
            if cleaned:
                # Remove remaining single bubble chars at start
                cleaned = re.sub(r'^[0oOоОФфΦφMМмBbБбИиIi]\s+', '', cleaned)

                # Remove leading punctuation
                cleaned = re.sub(r'^[.,-]+\s*', '', cleaned)

                # Normalize whitespace
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            if cleaned != original:
                print(f"Enhanced cleaning: '{original[:30]}' → '{cleaned[:30]}'")

            return cleaned if cleaned and len(cleaned) > 2 else original

        except:
            return text.strip()

    def clean_question_enhanced(self, text):
        """Enhanced question cleaning"""
        try:
            # Remove indicator line
            cleaned = re.sub(r"Broj potrebnih odgovora:\s*\d+", "", text, flags=re.IGNORECASE)

            # Remove bubble chars from start of lines
            lines = []
            for line in cleaned.split('\n'):
                line = line.strip()
                if line:
                    # Remove bubble chars from start
                    line = re.sub(r'^[0oOоОФфΦφMМмBbБб]+\s*', '', line)
                    if len(line) > 3:
                        lines.append(line)

            result = ' '.join(lines)
            return result if result else text

        except:
            return text

    def fast_ocr(self, region_cv):
        """Fast OCR"""
        try:
            gray = cv2.cvtColor(region_cv, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            text = pytesseract.image_to_string(processed, lang="srp+eng", config="--oem 1 --psm 6").strip()
            return text, 75
        except:
            try:
                text = pytesseract.image_to_string(region_cv, lang="eng", config="--psm 6").strip()
                return text, 60
            except:
                return "", 0

    def fast_color_blocks(self, region_cv, color_name):
        """Fast color detection"""
        try:
            hsv = cv2.cvtColor(region_cv, cv2.COLOR_BGR2HSV)

            if color_name == "green":
                mask = cv2.inRange(hsv, np.array([25, 20, 20]), np.array([95, 255, 255]))
            else:
                mask1 = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([25, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([155, 20, 20]), np.array([180, 255, 255]))
                mask = mask1 + mask2

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            blocks = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 120:  # Even lower for better detection
                    x, y, w, h = cv2.boundingRect(contour)
                    if w > 35 and h > 5:
                        blocks.append({'x': x, 'y': y, 'w': w, 'h': h})

            blocks.sort(key=lambda b: b['y'])
            return blocks
        except:
            return []

    def fast_text_from_block(self, region_cv, block):
        """Fast text extraction"""
        try:
            x, y, w, h = block['x'], block['y'], block['w'], block['h']
            block_region = region_cv[max(0,y-3):y+h+3, max(0,x-3):x+w+3]  # Small padding
            return self.fast_ocr(block_region)
        except:
            return "", 0

    def detect_question_type(self, text):
        """Fast type detection"""
        match = re.search(r"Broj potrebnih odgovora:\s*(\d+)", text, re.IGNORECASE)
        if match:
            self.question_type = "multi"
            self.required_correct_answers = int(match.group(1))
            self.type_label.config(text="MULTI", foreground="orange")
            self.required_label.config(text=f"Need: {self.required_correct_answers}")
        else:
            self.question_type = "single"
            self.required_correct_answers = 1
            self.type_label.config(text="SINGLE", foreground="blue")
            self.required_label.config(text="Need: 1")

    def update_answers_fast(self):
        """Fast answer display update"""
        self.correct_answers_list.delete(1.0, tk.END)
        for i, ans in enumerate(self.correct_answers, 1):
            self.correct_answers_list.insert(tk.END, f"{i}. {ans['text']}\n")

        self.wrong_answers_list.delete(1.0, tk.END)
        for i, ans in enumerate(self.wrong_answers, 1):
            self.wrong_answers_list.insert(tk.END, f"{i}. {ans['text']}\n")

    def save_qa_set_silent(self):
        """Silent auto-save for continuous mode"""
        start_time = time.time()

        try:
            # Load existing data
            data = {"questions": []}
            if os.path.exists(self.json_file):
                try:
                    with open(self.json_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                except:
                    data = {"questions": []}

            if "questions" not in data:
                data["questions"] = []

            # Create entry
            qa_entry = {
                "id": self.question_counter,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": self.current_question,
                "question_type": self.question_type,
                "required_correct_answers": self.required_correct_answers,
                "correct_answers": [a['text'] for a in self.correct_answers],
                "wrong_answers": [a['text'] for a in self.wrong_answers],
                "total_correct": len(self.correct_answers),
                "total_wrong": len(self.wrong_answers),
                "total_answers": len(self.correct_answers) + len(self.wrong_answers)
            }

            data["questions"].append(qa_entry)

            # Save
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Update counter and display
            save_time = time.time() - start_time
            self.question_counter += 1

            # Update UI for continuous mode
            session_count = self.question_counter - 1
            self.counter_label.config(text=f"Session: {session_count} saved")
            self.update_data_display()

            # Show success and prepare for next
            success_msg = f"✅ Q&A #{qa_entry['id']} auto-saved! ({save_time:.1f}s)"
            self.show_success(success_msg)

            # Prepare for next question
            self.prepare_for_next_question()

        except Exception as e:
            messagebox.showerror("Auto-Save Error", f"Could not save Q&A: {e}")

    def prepare_for_next_question(self):
        """Prepare for next question in continuous mode"""
        # Reset current data
        self.reset_current_question()

        # Set to ready state
        self.phase = "idle"
        self.phase_label.config(text="READY FOR NEXT", foreground="green")
        self.update_status("Press SPACE to start next question")

    def load_existing_data_robust(self):
        """Robust data loading"""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if "questions" in data and isinstance(data["questions"], list) and data["questions"]:
                            self.question_counter = max(q.get("id", 0) for q in data["questions"]) + 1
                        self.update_data_display()
            except:
                pass

    def update_data_display(self):
        """Update data display"""
        self.data_display.delete(1.0, tk.END)

        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)

                        if "questions" in data and isinstance(data["questions"], list):
                            # Show recent questions
                            for q in data["questions"][-5:]:
                                qtype = q.get('question_type', '?')
                                correct = q.get('total_correct', 0)
                                wrong = q.get('total_wrong', 0)

                                line = f"Q{q.get('id', '?')} - {qtype.upper()} (✅{correct} ❌{wrong}) - {q.get('question', '')[:45]}...\n"
                                self.data_display.insert(tk.END, line)
            except:
                pass

def main():
    root = tk.Tk()
    app = UltimateAutomatedQAExtractor(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            keyboard.unhook_all()
        except:
            pass

if __name__ == "__main__":
    main()
