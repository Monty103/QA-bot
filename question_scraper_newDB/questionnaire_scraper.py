"""
Serbian Questionnaire Scraper
A semi-automatic tool for extracting questions and answers from questionnaires
and storing them in a remote database.
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import json
import requests
from PIL import ImageGrab
import pytesseract
from pynput import keyboard
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys
import os

# Configuration
API_BASE_URL = "https://question-database-api.onrender.com"
SELECTION_RECT_COLOR = (0, 255, 0)  # Green for selection rectangle
SELECTION_RECT_WIDTH = 2

# Local backup configuration
BACKUP_FOLDER = "data"
BACKUP_FILE = "questions_answers.json"

class SelectionArea:
    """Allows user to select a rectangular area on screen"""
    def __init__(self):
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.selected = False

    def select_area(self) -> Tuple[int, int, int, int]:
        """
        Creates a window for selecting a rectangular area.
        Returns: (left, top, right, bottom) coordinates
        """
        self.selected = False
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)
        root.attributes('-topmost', True)

        canvas = tk.Canvas(root, cursor="crosshair", bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)

        def on_mouse_down(event):
            self.start_x = event.x
            self.start_y = event.y
            canvas.delete("selection")

        def on_mouse_drag(event):
            canvas.delete("selection")
            canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=2, tags="selection"
            )

        def on_mouse_up(event):
            self.end_x = event.x
            self.end_y = event.y
            self.selected = True
            root.quit()

        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

        root.mainloop()
        root.destroy()

        if self.selected:
            left = min(self.start_x, self.end_x)
            top = min(self.start_y, self.end_y)
            right = max(self.start_x, self.end_x)
            bottom = max(self.start_y, self.end_y)
            return (left, top, right, bottom)

        return None

class TextExtractor:
    """Extracts text from images using OCR"""
    def __init__(self):
        try:
            pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        except:
            pass

    def extract_from_area(self, coords: Tuple[int, int, int, int]) -> str:
        """
        Extract text from a specific area of the screen with preprocessing.
        Args: coords = (left, top, right, bottom)
        Returns: extracted text
        """
        if not coords:
            return ""

        try:
            screenshot = ImageGrab.grab(bbox=coords)
            img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # Preprocess for better OCR
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # OCR with preprocessing
            text = pytesseract.image_to_string(processed, lang="srp+eng", config="--oem 1 --psm 6").strip()

            if not text:
                # Fallback to original
                text = pytesseract.image_to_string(img_cv, lang='srp').strip()

            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

class AnswerAnalyzer:
    """Analyzes answer text and detects correct/incorrect answers by color"""

    @staticmethod
    def analyze_answer_area(coords: Tuple[int, int, int, int]) -> List[Dict]:
        """
        Extract answers using contour detection for color blocks.
        Returns list of {'text': str, 'is_correct': bool} dictionaries
        """
        if not coords:
            return []

        try:
            screenshot = ImageGrab.grab(bbox=coords)
            region_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # Detect colored blocks using contours
            green_blocks = AnswerAnalyzer._detect_color_blocks(region_cv, "green")
            red_blocks = AnswerAnalyzer._detect_color_blocks(region_cv, "red")

            # Extract text from blocks
            answers = []

            # Process green blocks (correct answers)
            for block in green_blocks:
                text = AnswerAnalyzer._extract_text_from_block(region_cv, block)
                if text and len(text) > 2:
                    answers.append({'text': text, 'is_correct': True})

            # Process red blocks (incorrect answers)
            for block in red_blocks:
                text = AnswerAnalyzer._extract_text_from_block(region_cv, block)
                if text and len(text) > 2:
                    answers.append({'text': text, 'is_correct': False})

            # Sort by vertical position
            answers.sort(key=lambda a: a.get('_y', 0) if isinstance(a, dict) and '_y' in a else 0)

            # Remove the _y key if it exists
            for a in answers:
                if '_y' in a:
                    del a['_y']

            return answers

        except Exception as e:
            print(f"Answer analysis error: {e}")
            return []

    @staticmethod
    def _detect_color_blocks(img_cv, color_name):
        """Detect blocks of a specific color using contours"""
        try:
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)

            if color_name == "green":
                mask = cv2.inRange(hsv, np.array([25, 20, 20]), np.array([95, 255, 255]))
            else:  # red
                mask1 = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([25, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([155, 20, 20]), np.array([180, 255, 255]))
                mask = mask1 + mask2

            # Close small gaps in the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            blocks = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 120:  # Minimum block size
                    x, y, w, h = cv2.boundingRect(contour)
                    if w > 35 and h > 5:  # Reasonable dimensions
                        blocks.append({'x': x, 'y': y, 'w': w, 'h': h})

            # Sort by vertical position
            blocks.sort(key=lambda b: b['y'])
            return blocks
        except:
            return []

    @staticmethod
    def _extract_text_from_block(img_cv, block):
        """Extract text from a colored block"""
        try:
            x, y, w, h = block['x'], block['y'], block['w'], block['h']
            # Expand block region slightly
            block_region = img_cv[max(0, y-3):y+h+3, max(0, x-3):x+w+3]

            # Preprocess
            gray = cv2.cvtColor(block_region, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # OCR
            text = pytesseract.image_to_string(processed, lang="srp+eng", config="--oem 1 --psm 6").strip()

            if not text:
                text = pytesseract.image_to_string(block_region, lang='srp').strip()

            return text
        except:
            return ""

class DatabaseAPI:
    """Handles communication with the question database API"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            data = response.json()
            return data.get("success", False)
        except:
            return False

    def submit_question(self, question_text: str, answers: List[Dict],
                       question_type: str = "single") -> Optional[int]:
        """
        Submit a question with its answers to the database.

        Args:
            question_text: The question text
            answers: List of {'text': str, 'is_correct': bool} dicts
            question_type: "single" or "multi"

        Returns:
            question_id if successful, None otherwise
        """
        try:
            # Count correct answers
            correct_count = sum(1 for a in answers if a['is_correct'])

            if correct_count == 0:
                print("Warning: No correct answers detected")
                return None

            # Determine question type based on correct answers
            if correct_count > 1:
                question_type = "multi"

            # Step 1: Create question
            question_payload = {
                "question_text": question_text,
                "question_type": question_type,
                "required_answers": correct_count
            }

            response = requests.post(
                f"{self.base_url}/api/questions",
                json=question_payload,
                timeout=10
            )

            if not response.ok:
                print(f"Failed to create question: {response.status_code}")
                return None

            data = response.json()
            if not data.get("success"):
                print(f"API Error: {data.get('message')}")
                return None

            question_id = data["data"]["question_id"]

            # Step 2: Add answers
            for answer in answers:
                answer_payload = {
                    "answer_text": answer['text'],
                    "is_correct": answer['is_correct']
                }

                response = requests.post(
                    f"{self.base_url}/api/questions/{question_id}/answers",
                    json=answer_payload,
                    timeout=10
                )

                if not response.ok:
                    print(f"Failed to add answer: {response.status_code}")

            return question_id

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None
        except Exception as e:
            print(f"Error submitting question: {e}")
            return None

class QuestionnaireScraperApp:
    """Main application class"""

    def __init__(self, root):
        self.root = root
        self.root.title("Serbian Questionnaire Scraper")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Initialize components
        self.selection_area = SelectionArea()
        self.text_extractor = TextExtractor()
        self.answer_analyzer = AnswerAnalyzer()
        self.api = DatabaseAPI()

        # State
        self.is_listening = False
        self.collected_data = []  # List of {question, answers}
        self.listener = None

        # Setup UI
        self.setup_ui()
        self.check_api_connection()

    def setup_ui(self):
        """Create the user interface"""
        # Top frame with buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.start_button = tk.Button(
            button_frame, text="START", command=self.on_start,
            bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'),
            padx=15, pady=10
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            button_frame, text="STOP", command=self.on_stop,
            bg='#f44336', fg='white', font=('Arial', 12, 'bold'),
            padx=15, pady=10, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.sync_button = tk.Button(
            button_frame, text="SYNC", command=self.on_sync,
            bg='#2196F3', fg='white', font=('Arial', 12, 'bold'),
            padx=15, pady=10
        )
        self.sync_button.pack(side=tk.LEFT, padx=5)

        self.preview_button = tk.Button(
            button_frame, text="PREVIEW", command=self.on_preview,
            bg='#FF9800', fg='white', font=('Arial', 12, 'bold'),
            padx=15, pady=10
        )
        self.preview_button.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = tk.Label(
            button_frame, text="Ready", font=('Arial', 10),
            fg='green'
        )
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Main content frame
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Instructions and info
        left_panel = tk.Frame(content_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        tk.Label(left_panel, text="Instructions:", font=('Arial', 11, 'bold')).pack(anchor=tk.W)

        instructions = """
1. Press START button
2. Press SPACEBAR to capture
   a question/answer pair
3. Select question area
4. Select answer area
5. Program detects colors:
   • Green = Correct
   • Red = Incorrect
6. Repeat for more questions
7. Press STOP when done
8. Press SYNC to upload
9. Use PREVIEW to review

Note: Tesseract-OCR must be
installed on your system.
        """
        tk.Label(left_panel, text=instructions, justify=tk.LEFT,
                font=('Courier', 9), bg='#f5f5f5', padx=10, pady=10,
                relief=tk.SUNKEN).pack(fill=tk.BOTH, expand=True)

        # Right panel - Data display
        right_panel = tk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_panel, text=f"Captured: 0 questions",
                font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        self.counter_label = tk.Label(right_panel, text="Captured: 0 questions",
                                      font=('Arial', 10, 'bold'))
        self.counter_label.pack(anchor=tk.W)

        tk.Label(right_panel, text="Last captured:",
                font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 0))

        self.last_data_text = scrolledtext.ScrolledText(
            right_panel, height=20, width=60, font=('Courier', 9)
        )
        self.last_data_text.pack(fill=tk.BOTH, expand=True)

    def check_api_connection(self):
        """Check if API is accessible"""
        def check():
            if self.api.health_check():
                self.update_status("API Connected ✓", "green")
            else:
                self.update_status("API Disconnected ✗", "red")

        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    def update_status(self, message: str, color: str = "black"):
        """Update status label"""
        self.status_label.config(text=message, fg=color)

    def on_start(self):
        """Start listening for spacebar"""
        self.is_listening = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Listening for SPACEBAR... Press SPACEBAR to capture", "blue")

        # Start listening in a separate thread
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_stop(self):
        """Stop listening"""
        self.is_listening = False
        if self.listener:
            self.listener.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status(f"Stopped. Captured {len(self.collected_data)} questions", "orange")

    def on_key_press(self, key):
        """Handle spacebar press"""
        if not self.is_listening:
            return

        try:
            if key == keyboard.Key.space:
                # Run capture in main thread to access Tkinter
                self.root.after(0, self.capture_question_answer_pair)
        except AttributeError:
            pass

    def capture_question_answer_pair(self):
        """Capture a question and answer pair - seamless workflow without prompts"""
        try:
            # Step 1: Get question area - no prompt, just select
            self.update_status("Select question area (draw rectangle)...", "blue")
            question_coords = self.selection_area.select_area()

            if not question_coords:
                self.update_status("Ready", "black")
                return

            self.update_status("Extracting question...", "blue")
            question_text = self.text_extractor.extract_from_area(question_coords)

            if not question_text:
                self.update_status("OCR failed - could not extract question text", "red")
                return

            # Step 2: Get answers area immediately - no prompt between selections
            self.update_status("Select answer area (draw rectangle)...", "blue")
            answers_coords = self.selection_area.select_area()

            if not answers_coords:
                self.update_status("Ready", "black")
                return

            self.update_status("Analyzing answers...", "blue")
            answers = self.answer_analyzer.analyze_answer_area(answers_coords)

            if not answers:
                self.update_status("OCR failed - could not extract answers", "red")
                return

            # Store the data
            entry = {
                'question': question_text,
                'answers': answers,
                'timestamp': datetime.now().isoformat()
            }
            self.collected_data.append(entry)

            # Update UI
            self.update_counter()
            self.display_last_entry(entry)
            self.update_status(f"✓ Captured Q#{len(self.collected_data)} | Ready for next", "green")

        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")

    def update_counter(self):
        """Update the question counter"""
        self.counter_label.config(
            text=f"Captured: {len(self.collected_data)} questions"
        )

    def display_last_entry(self, entry: Dict):
        """Display the last captured entry"""
        self.last_data_text.config(state=tk.NORMAL)
        self.last_data_text.delete(1.0, tk.END)

        output = f"QUESTION:\n{entry['question']}\n\n"
        output += "ANSWERS:\n"

        for i, answer in enumerate(entry['answers'], 1):
            status = "✓ CORRECT" if answer['is_correct'] else "✗ INCORRECT"
            output += f"{i}. [{status}] {answer['text']}\n"

        output += f"\n[Captured at: {entry['timestamp']}]"

        self.last_data_text.insert(1.0, output)
        self.last_data_text.config(state=tk.DISABLED)

    def on_preview(self):
        """Show all collected data"""
        if not self.collected_data:
            messagebox.showinfo("Preview", "No data collected yet")
            return

        preview_window = tk.Toplevel(self.root)
        preview_window.title("Data Preview")
        preview_window.geometry("800x600")

        text_widget = scrolledtext.ScrolledText(preview_window, font=('Courier', 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        output = "="*80 + "\n"
        output += "QUESTIONNAIRE DATA PREVIEW\n"
        output += "="*80 + "\n\n"

        for idx, entry in enumerate(self.collected_data, 1):
            output += f"QUESTION #{idx}\n"
            output += "-"*40 + "\n"
            output += f"{entry['question']}\n\n"
            output += "ANSWERS:\n"

            for i, answer in enumerate(entry['answers'], 1):
                status = "✓ CORRECT" if answer['is_correct'] else "✗ INCORRECT"
                output += f"  {i}. [{status}] {answer['text']}\n"

            output += "\n"

        text_widget.insert(1.0, output)
        text_widget.config(state=tk.DISABLED)

    def save_to_local_backup(self, entries: List[Dict]) -> bool:
        """
        Save question/answer entries to local JSON file as backup.
        Appends to existing file if it exists.

        Args:
            entries: List of question/answer dictionaries to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            backup_dir = os.path.join(script_dir, BACKUP_FOLDER)
            backup_path = os.path.join(backup_dir, BACKUP_FILE)

            # Create backup folder if it doesn't exist
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # Load existing data if file exists
            existing_data = []
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    # If file is corrupted or empty, start fresh
                    existing_data = []

            # Append new entries
            existing_data.extend(entries)

            # Save to file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            print(f"Backup saved: {len(entries)} new entries ({len(existing_data)} total) to {backup_path}")
            return True

        except Exception as e:
            print(f"Error saving backup: {e}")
            return False

    def on_sync(self):
        """Sync all collected data to the database"""
        if not self.collected_data:
            messagebox.showwarning("No Data", "No questions collected yet")
            return

        response = messagebox.askyesno("Confirm Sync",
            f"Upload {len(self.collected_data)} questions to the database?")

        if not response:
            return

        self.update_status("Syncing to database...", "blue")

        def sync_thread():
            # First, save to local backup (before database sync)
            backup_success = self.save_to_local_backup(self.collected_data)
            if backup_success:
                print("Local backup saved successfully")
            else:
                print("Warning: Local backup failed, continuing with database sync")

            successful = 0
            failed = 0

            for idx, entry in enumerate(self.collected_data, 1):
                try:
                    question_id = self.api.submit_question(
                        entry['question'],
                        entry['answers']
                    )

                    if question_id:
                        successful += 1
                        self.update_status(
                            f"Syncing... {idx}/{len(self.collected_data)} ({successful} OK)",
                            "blue"
                        )
                    else:
                        failed += 1

                except Exception as e:
                    failed += 1
                    print(f"Error syncing question {idx}: {e}")

            # Show results
            message = f"Sync Complete!\n\n"
            message += f"Database upload: {successful} OK, {failed} failed\n"
            message += f"Local backup: {'Saved' if backup_success else 'Failed'}\n"

            if failed == 0:
                self.collected_data = []  # Clear after successful sync
                self.update_counter()
                self.last_data_text.config(state=tk.NORMAL)
                self.last_data_text.delete(1.0, tk.END)
                self.last_data_text.config(state=tk.DISABLED)
                self.update_status(f"✓ All {successful} questions uploaded!", "green")
                messagebox.showinfo("Success", message)
            else:
                self.update_status(f"⚠ Sync completed with {failed} errors", "orange")
                messagebox.showwarning("Partial Success", message)

        thread = threading.Thread(target=sync_thread, daemon=True)
        thread.start()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = QuestionnaireScraperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
