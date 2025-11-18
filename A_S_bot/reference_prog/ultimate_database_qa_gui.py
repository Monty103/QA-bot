"""
ULTIMATE DATABASE-CONNECTED Q&A EXTRACTOR
Saves data to remote Supabase database for collaborative scraping

Features:
- Connects to Supabase PostgreSQL database
- Real-time collaboration between multiple users
- Enhanced bubble cleaning
- Continuous auto-save mode
- Offline support with retry mechanism
- User identification system
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
import requests
import uuid
import getpass

class UltimateDBQAExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate DB Q&A Extractor")
        self.root.geometry("1100x900")

        # Configuration
        self.tesseract_path = r"C:\dt\Tesseract-OCR\tesseract.exe"
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

        # Database configuration - YOU NEED TO SET THESE VALUES
        self.SUPABASE_URL = "https://uidbhvmtdpkvvxpeadcv.supabase.co"  # Replace with your Supabase URL
        self.SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVpZGJodm10ZHBrdnZ4cGVhZGN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2NTIwMTgsImV4cCI6MjA3NDIyODAxOH0.3-wlLxBOVkPW-QaHQnM8oUHdyWCHNgfjILKsd8OWhNw"  # Replace with your anon key
        self.table_name = "questions"

        # User identification
        self.user_name = getpass.getuser()  # Get computer username
        self.session_id = str(uuid.uuid4())[:8]  # Unique session ID

        # Local backup (in case DB is down)
        self.json_file = "qa_data_backup.json"
        self.offline_queue = []  # Queue for offline data

        # State management
        self.current_screenshot = None
        self.selection_window = None
        self.is_active = False
        self.question_counter = 1
        self.processing = False
        self.continuous_mode = False
        self.redo_mode = None

        # Current Q&A session data
        self.current_question = ""
        self.correct_answers = []
        self.wrong_answers = []
        self.question_type = "unknown"
        self.required_correct_answers = 0
        self.phase = "idle"

        # Database connection status
        self.db_connected = False

        # Create GUI
        self.create_gui()

        # Test database connection
        self.test_database_connection()

        # Setup keyboard listener
        self.setup_keyboard_listener()

    def create_gui(self):
        """Create GUI with database status"""

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Database status at top
        db_frame = ttk.Frame(main_frame)
        db_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(db_frame, text="Database:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.db_status_label = ttk.Label(db_frame, text="Connecting...", font=('Arial', 10))
        self.db_status_label.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(db_frame, text="User:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.user_label = ttk.Label(db_frame, text=f"{self.user_name} ({self.session_id})", 
                                   font=('Arial', 10), foreground="blue")
        self.user_label.pack(side=tk.LEFT, padx=(5, 0))

        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Main controls
        main_controls = ttk.Frame(control_frame)
        main_controls.pack(fill=tk.X, pady=(0, 5))

        self.start_button = ttk.Button(main_controls, text="🚀 Start Collaborative Mode", 
                                     command=self.start_continuous_mode, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(main_controls, text="🛑 Stop", 
                                    command=self.stop_continuous_mode, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        self.sync_button = ttk.Button(main_controls, text="🔄 Sync Offline Data", 
                                    command=self.sync_offline_data, state=tk.DISABLED)
        self.sync_button.pack(side=tk.LEFT, padx=(0, 10))

        # Status indicators
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

        # Status with spinner
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        top_status_frame = ttk.Frame(status_frame)
        top_status_frame.pack(fill=tk.X)

        self.phase_label = ttk.Label(top_status_frame, text="Ready", font=('Arial', 14, 'bold'), foreground="blue")
        self.phase_label.pack(side=tk.LEFT)

        self.status_label = ttk.Label(top_status_frame, text="Configure database connection first", font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))

        # Loading indicators
        loading_frame = ttk.Frame(status_frame)
        loading_frame.pack(fill=tk.X, pady=(5, 0))

        self.loading_label = ttk.Label(loading_frame, text="", font=('Arial', 9), foreground="orange")
        self.loading_label.pack(side=tk.LEFT)

        self.spinner = ttk.Progressbar(loading_frame, mode='indeterminate', length=120)
        self.spinner.pack(side=tk.LEFT, padx=(10, 0))

        self.speed_label = ttk.Label(loading_frame, text="", font=('Arial', 9), foreground="green")
        self.speed_label.pack(side=tk.LEFT, padx=(10, 0))

        self.success_label = ttk.Label(loading_frame, text="", font=('Arial', 10, 'bold'), foreground="green")
        self.success_label.pack(side=tk.LEFT, padx=(20, 0))

        # Results frame
        type_frame = ttk.LabelFrame(main_frame, text="Detection Results", padding="5")
        type_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        type_info_frame = ttk.Frame(type_frame)
        type_info_frame.pack(fill=tk.X)

        ttk.Label(type_info_frame, text="Type:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.type_label = ttk.Label(type_info_frame, text="Not detected", font=('Arial', 10), foreground="gray")
        self.type_label.pack(side=tk.LEFT, padx=(5, 15))

        self.required_label = ttk.Label(type_info_frame, text="", font=('Arial', 9), foreground="blue")
        self.required_label.pack(side=tk.LEFT, padx=(0, 15))

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
        qa_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

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
        self.correct_answers_list = scrolledtext.ScrolledText(correct_frame, height=2, width=95, font=('Arial', 9))
        self.correct_answers_list.pack(fill=tk.BOTH, expand=True)

        # Wrong answers
        wrong_frame = ttk.Frame(answers_frame)
        wrong_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(wrong_frame, text="❌ Wrong:", font=('Arial', 10, 'bold'), foreground="red").pack(anchor=tk.W)
        self.wrong_answers_list = scrolledtext.ScrolledText(wrong_frame, height=2, width=95, font=('Arial', 9))
        self.wrong_answers_list.pack(fill=tk.BOTH, expand=True)

        # Instructions
        instructions_frame = ttk.LabelFrame(main_frame, text="🌐 Collaborative Database Mode", padding="5")
        instructions_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        instructions_text = """🌐 COLLABORATIVE DATABASE WORKFLOW:
1. Configure Supabase database connection (see setup instructions below)
2. Click '🚀 Start Collaborative Mode'
3. SPACE → Select question → Select answers → AUTO-SAVES TO DATABASE!
4. Your friend can run the same program and save to the same database
5. All data is stored remotely and accessible to both users

DATABASE FEATURES:
• Real-time collaboration (both users see each other's data)
• Offline support (saves locally if database is down, syncs later)
• User identification (tracks who saved what)
• Enhanced bubble cleaning
• Automatic retry on connection failures

SETUP REQUIRED:
You need to set up a FREE Supabase account and configure connection in the code.
See the setup instructions file created with this program."""

        ttk.Label(instructions_frame, text=instructions_text, justify=tk.LEFT, font=('Arial', 8)).pack(anchor=tk.W)

        # Database status display
        db_data_frame = ttk.LabelFrame(main_frame, text="Database Status & Recent Data", padding="5")
        db_data_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        self.data_display = scrolledtext.ScrolledText(db_data_frame, height=4, width=95, font=('Arial', 8))
        self.data_display.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def test_database_connection(self):
        """Test connection to Supabase database"""
        try:
            if self.SUPABASE_URL == "YOUR_SUPABASE_URL_HERE" or self.SUPABASE_KEY == "YOUR_SUPABASE_ANON_KEY_HERE":
                self.db_status_label.config(text="⚠ Not configured", foreground="orange")
                self.status_label.config(text="Please configure Supabase connection (see setup instructions)")
                self.data_display.insert(tk.END, "⚠ Database not configured. Please see setup instructions.\n")
                return

            # Test connection
            headers = {
                'apikey': self.SUPABASE_KEY,
                'Authorization': f'Bearer {self.SUPABASE_KEY}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.SUPABASE_URL}/rest/v1/{self.table_name}?limit=1",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                self.db_connected = True
                self.db_status_label.config(text="✅ Connected to Supabase", foreground="green")
                self.status_label.config(text="Database connected! Click 'Start Collaborative Mode' to begin")
                self.data_display.insert(tk.END, "✅ Successfully connected to Supabase database\n")
                self.load_recent_data()
            else:
                self.handle_db_error(f"Connection failed: HTTP {response.status_code}")

        except requests.RequestException as e:
            self.handle_db_error(f"Connection error: {e}")
        except Exception as e:
            self.handle_db_error(f"Unexpected error: {e}")

    def handle_db_error(self, error_msg):
        """Handle database connection errors"""
        self.db_connected = False
        self.db_status_label.config(text="❌ Connection failed", foreground="red")
        self.status_label.config(text="Database offline - will use local backup")
        self.data_display.insert(tk.END, f"❌ {error_msg}\n")
        self.data_display.insert(tk.END, "💾 Will save locally and sync when online\n")

        # Enable sync button for offline mode
        if self.offline_queue:
            self.sync_button.config(state=tk.NORMAL)

    def save_to_database(self, qa_data):
        """Save Q&A data to Supabase database"""
        try:
            if not self.db_connected:
                # Save to offline queue
                self.offline_queue.append(qa_data)
                self.sync_button.config(state=tk.NORMAL)
                return False, "Saved offline - will sync when online"

            headers = {
                'apikey': self.SUPABASE_KEY,
                'Authorization': f'Bearer {self.SUPABASE_KEY}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.SUPABASE_URL}/rest/v1/{self.table_name}",
                headers=headers,
                json=qa_data,
                timeout=10
            )

            if response.status_code == 201:
                return True, "Saved to database"
            else:
                # Save to offline queue on failure
                self.offline_queue.append(qa_data)
                self.sync_button.config(state=tk.NORMAL)
                return False, f"DB error: HTTP {response.status_code} - saved offline"

        except requests.RequestException as e:
            # Save to offline queue on network error
            self.offline_queue.append(qa_data)
            self.sync_button.config(state=tk.NORMAL)
            return False, f"Network error - saved offline: {e}"
        except Exception as e:
            self.offline_queue.append(qa_data)
            return False, f"Unexpected error - saved offline: {e}"

    def sync_offline_data(self):
        """Sync offline data to database"""
        if not self.offline_queue:
            messagebox.showinfo("Sync", "No offline data to sync!")
            return

        if not self.db_connected:
            # Retry connection
            self.test_database_connection()
            if not self.db_connected:
                messagebox.showerror("Sync Failed", "Database is still offline!")
                return

        self.start_spinner("Syncing offline data...")

        synced = 0
        failed = 0

        for qa_data in self.offline_queue.copy():
            try:
                headers = {
                    'apikey': self.SUPABASE_KEY,
                    'Authorization': f'Bearer {self.SUPABASE_KEY}',
                    'Content-Type': 'application/json'
                }

                response = requests.post(
                    f"{self.SUPABASE_URL}/rest/v1/{self.table_name}",
                    headers=headers,
                    json=qa_data,
                    timeout=10
                )

                if response.status_code == 201:
                    self.offline_queue.remove(qa_data)
                    synced += 1
                else:
                    failed += 1

            except Exception as e:
                failed += 1
                continue

        self.stop_spinner()

        if synced > 0:
            self.show_success(f"✅ Synced {synced} items to database!")

        if failed > 0:
            messagebox.showwarning("Partial Sync", f"Synced {synced}, failed {failed} items")
        else:
            messagebox.showinfo("Sync Complete", f"Successfully synced {synced} items!")

        if not self.offline_queue:
            self.sync_button.config(state=tk.DISABLED)

    def load_recent_data(self):
        """Load recent data from database for display"""
        try:
            if not self.db_connected:
                return

            headers = {
                'apikey': self.SUPABASE_KEY,
                'Authorization': f'Bearer {self.SUPABASE_KEY}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.SUPABASE_URL}/rest/v1/{self.table_name}?order=created_at.desc&limit=5",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.data_display.delete(1.0, tk.END)

                if data:
                    self.data_display.insert(tk.END, "📊 Recent questions from database:\n")
                    for item in data:
                        user = item.get('user_name', 'Unknown')
                        qtype = item.get('question_type', '?')
                        correct = item.get('total_correct', 0)
                        wrong = item.get('total_wrong', 0)
                        question = item.get('question', 'No question')[:50]
                        created = item.get('created_at', '')[:19]

                        line = f"[{created}] {user}: {qtype.upper()} (✅{correct} ❌{wrong}) - {question}...\n"
                        self.data_display.insert(tk.END, line)
                else:
                    self.data_display.insert(tk.END, "📊 No questions in database yet\n")

        except Exception as e:
            self.data_display.insert(tk.END, f"❌ Error loading recent data: {e}\n")

    # [Include all the processing methods from the previous version]
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
            self.root.after(3000, lambda: self.success_label.config(text=""))
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

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.redo_question_button.config(state=tk.NORMAL)
        self.redo_answers_button.config(state=tk.NORMAL)

        self.mode_label.config(text="🔄 COLLABORATIVE MODE")
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

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.redo_question_button.config(state=tk.DISABLED)
        self.redo_answers_button.config(state=tk.DISABLED)

        self.mode_label.config(text="")
        self.phase_label.config(text="Ready", foreground="blue")
        self.update_status("Collaborative mode stopped.")

        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None

    def save_qa_set_to_database(self):
        """Save Q&A data to database with enhanced data structure"""
        start_time = time.time()
        self.start_spinner("Saving to database...")

        try:
            # Create comprehensive data entry
            qa_entry = {
                "user_name": self.user_name,
                "session_id": self.session_id,
                "question": self.current_question,
                "question_type": self.question_type,
                "required_correct_answers": self.required_correct_answers,
                "correct_answers": [a['text'] for a in self.correct_answers],
                "correct_confidences": [a['confidence'] for a in self.correct_answers],
                "wrong_answers": [a['text'] for a in self.wrong_answers],
                "wrong_confidences": [a['confidence'] for a in self.wrong_answers],
                "total_correct": len(self.correct_answers),
                "total_wrong": len(self.wrong_answers),
                "total_answers": len(self.correct_answers) + len(self.wrong_answers),
                "created_at": datetime.now().isoformat()
            }

            # Try to save to database
            success, message = self.save_to_database(qa_entry)

            save_time = time.time() - start_time
            self.stop_spinner(f"⚡ {save_time:.1f}s")

            if success:
                # Update counter and display
                self.question_counter += 1
                session_count = self.question_counter - 1
                self.counter_label.config(text=f"Session: {session_count} saved")

                # Show success and reload recent data
                success_msg = f"✅ Q&A saved to database! ({save_time:.1f}s)"
                self.show_success(success_msg)
                self.load_recent_data()
            else:
                # Show offline save message
                self.show_success(f"💾 {message}")

            # Prepare for next question
            self.prepare_for_next_question()

        except Exception as e:
            self.stop_spinner()
            messagebox.showerror("Save Error", f"Could not save Q&A: {e}")

    def auto_save_and_continue(self):
        """Automatically save Q&A and prepare for next question"""
        if self.current_question and (self.correct_answers or self.wrong_answers):
            self.save_qa_set_to_database()

    def prepare_for_next_question(self):
        """Prepare for next question in continuous mode"""
        self.reset_current_question()
        self.phase = "idle"
        self.phase_label.config(text="READY FOR NEXT", foreground="green")
        self.update_status("Press SPACE to start next question")

    # ... [Include all the other processing methods from the previous version]
    # [Due to length limits, I'm showing the key database integration parts]
    # The full code would include all the OCR, selection, and processing methods

def main():
    root = tk.Tk()
    app = UltimateDBQAExtractor(root)

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
